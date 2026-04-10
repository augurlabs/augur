from __future__ import annotations
import logging
import os
#from celery.result import AsyncResult
from celery import group, chain
from sqlalchemy import and_,update
import sqlalchemy as s


from augur.tasks.github import *
if os.environ.get('AUGUR_DOCKER_DEPLOY') != "1":
    from augur.tasks.data_analysis import *
from augur.tasks.github.detect_move.tasks import detect_github_repo_move_core, detect_github_repo_move_secondary
from augur.tasks.github.releases.tasks import collect_releases
from augur.tasks.github.repo_info.tasks import collect_repo_info, collect_linux_badge_info
from augur.tasks.github.pull_requests.files_model.tasks import process_pull_request_files
from augur.tasks.github.pull_requests.commits_model.tasks import process_pull_request_commits
from augur.tasks.github.util.populate_repo_src_id import populate_repo_src_id_task
from augur.tasks.git.dependency_tasks.tasks import process_ossf_dependency_metrics
from augur.tasks.github.traffic import collect_github_repo_clones_data
from augur.tasks.gitlab.merge_request_task import collect_gitlab_merge_requests, collect_merge_request_metadata, collect_merge_request_commits, collect_merge_request_files, collect_merge_request_comments
from augur.tasks.gitlab.issues_task import collect_gitlab_issues, collect_gitlab_issue_comments
from augur.tasks.gitlab.events_task import collect_gitlab_issue_events, collect_gitlab_merge_request_events
from augur.tasks.git.facade_tasks import *
from augur.tasks.db.refresh_materialized_views import *
from augur.tasks.init.celery_app import celery_app as celery
from augur.application.db.session import DatabaseSession
from augur.application.db.models import CollectionStatus, Repo
from augur.tasks.util.collection_state import CollectionState
from augur.tasks.util.collection_util import *
from augur.application.db.lib import execute_sql, get_session
from augur.application.config import AugurConfig

RUNNING_DOCKER = os.environ.get('AUGUR_DOCKER_DEPLOY') == "1"

CELERY_GROUP_TYPE = type(group())
CELERY_CHAIN_TYPE = type(chain())



"""
    Predefine phases. For new phases edit this and the config to reflect.
    The domain of tasks ran should be very explicit.

    A phase in this context is a function that takes a repo_git and returns a message
    for the celery worker to process.
"""

#Prelim phases are used to detect if where the repo has hosted has moved or not.
def prelim_phase(repo_git, full_collection):

    logger = logging.getLogger(prelim_phase.__name__)

    return detect_github_repo_move_core.si(repo_git)

def prelim_phase_secondary(repo_git, full_collection):
    logger = logging.getLogger(prelim_phase.__name__)

    return detect_github_repo_move_secondary.si(repo_git)


#This is the phase that defines the message for core augur collection
#A chain is needed for each repo.
def primary_repo_collect_phase(repo_git, full_collection):
    logger = logging.getLogger(primary_repo_collect_phase.__name__)


    #Define primary group of jobs for the primary collect phase: issues and pull requests.
    primary_repo_jobs = group(
        populate_repo_src_id_task.si(repo_git),
        collect_issues.si(repo_git, full_collection),
        collect_pull_requests.si(repo_git, full_collection)
    )

    #Define secondary group that can't run until after primary jobs have finished.
    secondary_repo_jobs = group(
        collect_events.si(repo_git, full_collection),#*create_grouped_task_load(dataList=first_pass, task=collect_events).tasks,
        collect_github_messages.si(repo_git, full_collection), #*create_grouped_task_load(dataList=first_pass,task=collect_github_messages).tasks,
        collect_github_repo_clones_data.si(repo_git),
    )

    #Other tasks that don't need other tasks to run before they do just put in final group.
    repo_task_group = group(
        collect_repo_info.si(repo_git),
        chain(primary_repo_jobs, secondary_repo_jobs),
        #facade_phase(logger,repo_git),
        collect_linux_badge_info.si(repo_git),
        collect_releases.si(repo_git),
        grab_comitters.si(repo_git)
    )

    return repo_task_group

def primary_repo_collect_phase_gitlab(repo_git, full_collection):

    logger = logging.getLogger(primary_repo_collect_phase_gitlab.__name__)

    jobs = group(
         chain(collect_gitlab_merge_requests.si(repo_git), group(
                                                                 collect_merge_request_comments.s(repo_git), 
                                                                 #collect_merge_request_reviewers.s(repo_git),
                                                                collect_merge_request_metadata.s(repo_git),
                                                                collect_merge_request_commits.s(repo_git),
                                                                collect_merge_request_files.s(repo_git),
                                                                collect_gitlab_merge_request_events.si(repo_git),
                                                                )),
         chain(collect_gitlab_issues.si(repo_git), group(
                                                        collect_gitlab_issue_comments.s(repo_git),
                                                        collect_gitlab_issue_events.si(repo_git),
                                                         )),
    )

    return jobs


#This phase creates the message for secondary collection tasks.
#These are less important and have their own worker.
def secondary_repo_collect_phase(repo_git, full_collection):
    logger = logging.getLogger(secondary_repo_collect_phase.__name__)

    repo_task_group = group(
        process_pull_request_files.si(repo_git, full_collection),
        process_pull_request_commits.si(repo_git, full_collection),
        chain(collect_pull_request_reviews.si(repo_git, full_collection), collect_pull_request_review_comments.si(repo_git, full_collection)),
        process_ossf_dependency_metrics.si(repo_git)
    )

    return repo_task_group




#This is a periodic task that runs less often to handle less important collection tasks such as 
#refreshing the materialized views.
@celery.task(bind=True)
def non_repo_domain_tasks(self):

    engine = self.app.engine

    logger = logging.getLogger(non_repo_domain_tasks.__name__)

    logger.info("Executing non-repo domain tasks")

    enabled_phase_names = get_enabled_phase_names_from_config(engine, logger)

    enabled_tasks = []

    if not RUNNING_DOCKER and machine_learning_phase.__name__ in enabled_phase_names:
        #enabled_tasks.extend(machine_learning_phase())
        from augur.tasks.data_analysis.contributor_breadth_worker.contributor_breadth_worker import contributor_breadth_model
        enabled_tasks.append(contributor_breadth_model.si())

    tasks = chain(
        *enabled_tasks,
    )

    tasks.apply_async()


def build_primary_repo_collect_request(session, logger, enabled_phase_names, days_until_collect_again = 15):
    #Add all required tasks to a list and pass it to the CollectionRequest
    primary_enabled_phases = []
    primary_gitlab_enabled_phases = []

    #Primary jobs
    if prelim_phase.__name__ in enabled_phase_names:
        primary_enabled_phases.append(prelim_phase)

    primary_enabled_phases.append(primary_repo_collect_phase)
    primary_gitlab_enabled_phases.append(primary_repo_collect_phase_gitlab)

    #task success is scheduled no matter what the config says.
    def core_task_success_util_gen(repo_git, full_collection):
        return core_task_success_util.si(repo_git)

    primary_enabled_phases.append(core_task_success_util_gen)
    primary_gitlab_enabled_phases.append(core_task_success_util_gen)

    primary_request = CollectionRequest("core",primary_enabled_phases,max_repo=40, days_until_collect_again=days_until_collect_again, gitlab_phases=primary_gitlab_enabled_phases)
    primary_request.get_valid_repos(session)
    return primary_request

def build_secondary_repo_collect_request(session, logger, enabled_phase_names, days_until_collect_again = 1):
    #Deal with secondary collection
    secondary_enabled_phases = []

    if prelim_phase.__name__ in enabled_phase_names:
        secondary_enabled_phases.append(prelim_phase_secondary)


    secondary_enabled_phases.append(secondary_repo_collect_phase)

    def secondary_task_success_util_gen(repo_git, full_collection):
        return secondary_task_success_util.si(repo_git)

    secondary_enabled_phases.append(secondary_task_success_util_gen)
    
    request = CollectionRequest("secondary",secondary_enabled_phases,max_repo=60, days_until_collect_again=days_until_collect_again)

    request.get_valid_repos(session)
    return request


def build_facade_repo_collect_request(session, logger, enabled_phase_names, days_until_collect_again = 10):
    #Deal with facade collection
    facade_enabled_phases = []

    facade_enabled_phases.append(facade_phase)

    def facade_task_success_util_gen(repo_git, full_collection):
        return facade_task_success_util.si(repo_git)

    facade_enabled_phases.append(facade_task_success_util_gen)


    request = CollectionRequest("facade",facade_enabled_phases,max_repo=30, days_until_collect_again=days_until_collect_again)

    request.get_valid_repos(session)
    return request

def build_ml_repo_collect_request(session, logger, enabled_phase_names, days_until_collect_again = 40):
    ml_enabled_phases = []

    ml_enabled_phases.append(machine_learning_phase)

    def ml_task_success_util_gen(repo_git, full_collection):
        return ml_task_success_util.si(repo_git)

    ml_enabled_phases.append(ml_task_success_util_gen)

    request = CollectionRequest("ml",ml_enabled_phases,max_repo=5, days_until_collect_again=days_until_collect_again)
    request.get_valid_repos(session)
    return request

@celery.task(bind=True)
def augur_collection_monitor(self):     

    engine = self.app.engine

    logger = logging.getLogger(augur_collection_monitor.__name__)

    logger.info("Checking for repos to collect")

    
    #Get list of enabled phases 
    enabled_phase_names = get_enabled_phase_names_from_config(engine, logger)

    enabled_collection_hooks = []

    with DatabaseSession(logger, self.app.engine) as session:

        # Get config values for collection intervals
        config = AugurConfig(logger, session)
        core_interval = config.get_value('Tasks', 'core_collection_interval_days') or 15
        secondary_interval = config.get_value('Tasks', 'secondary_collection_interval_days') or 10
        facade_interval = config.get_value('Tasks', 'facade_collection_interval_days') or 10
        ml_interval = config.get_value('Tasks', 'ml_collection_interval_days') or 40

        if primary_repo_collect_phase.__name__ in enabled_phase_names:
            enabled_collection_hooks.append(build_primary_repo_collect_request(session, logger, enabled_phase_names, core_interval))
        
        if secondary_repo_collect_phase.__name__ in enabled_phase_names:
            enabled_collection_hooks.append(build_secondary_repo_collect_request(session, logger, enabled_phase_names, secondary_interval))
            #start_secondary_collection(session, max_repo=10)

        if facade_phase.__name__ in enabled_phase_names:
            #start_facade_collection(session, max_repo=30)
            enabled_collection_hooks.append(build_facade_repo_collect_request(session, logger, enabled_phase_names, facade_interval))
        
        if not RUNNING_DOCKER and machine_learning_phase.__name__ in enabled_phase_names:
            enabled_collection_hooks.append(build_ml_repo_collect_request(session, logger, enabled_phase_names, ml_interval))
            #start_ml_collection(session,max_repo=5)
        
        logger.info(f"Starting collection phases: {[h.name for h in enabled_collection_hooks]}")

        main_routine = AugurTaskRoutine(logger, enabled_collection_hooks)

        main_routine.start_data_collection()

# have a pipe of 180

@celery.task(bind=True)
def retry_errored_repos(self):
    """
        Periodic task to reset repositories that have errored and try again.
    """
    engine = self.app.engine
    logger = logging.getLogger(create_collection_status_records.__name__)

    #TODO: Isaac needs to normalize the status's to be abstract in the 
    #collection_status table once augur dev is less unstable.
    query = s.sql.text(f"""UPDATE collection_status SET secondary_status = '{CollectionState.PENDING.value}'"""
    f""" WHERE secondary_status = '{CollectionState.ERROR.value}' and secondary_data_last_collected is NULL;"""
    f"""UPDATE collection_status SET core_status = '{CollectionState.PENDING.value}'"""
    f""" WHERE core_status = '{CollectionState.ERROR.value}' and core_data_last_collected is NULL;"""
    f"""UPDATE collection_status SET facade_status = '{CollectionState.PENDING.value}'"""
    f""" WHERE facade_status = '{CollectionState.ERROR.value}' and facade_data_last_collected is NULL;"""
    f"""UPDATE collection_status SET ml_status = '{CollectionState.PENDING.value}'"""
    f""" WHERE ml_status = '{CollectionState.ERROR.value}' and ml_data_last_collected is NULL;"""
    
    f"""UPDATE collection_status SET secondary_status = '{CollectionState.SUCCESS.value}'"""
    f""" WHERE secondary_status = '{CollectionState.ERROR.value}' and secondary_data_last_collected is not NULL;"""
    f"""UPDATE collection_status SET core_status = '{CollectionState.SUCCESS.value}'"""
    f""" WHERE core_status = '{CollectionState.ERROR.value}' and core_data_last_collected is not NULL;;"""
    f"""UPDATE collection_status SET facade_status = '{CollectionState.SUCCESS.value}'"""
    f""" WHERE facade_status = '{CollectionState.ERROR.value}' and facade_data_last_collected is not NULL;;"""
    f"""UPDATE collection_status SET ml_status = '{CollectionState.SUCCESS.value}'"""
    f""" WHERE ml_status = '{CollectionState.ERROR.value}' and ml_data_last_collected is not NULL;;"""
    )

    execute_sql(query)



#Retry this task for every issue so that repos that were added manually get the chance to be added to the collection_status table.
@celery.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=300, retry_jitter=True, max_retries=None, bind=True)
def create_collection_status_records(self):
    """
    Automatic task that runs and checks for repos that haven't been given a collection_status
    record corresponding to the state of their collection at the monent. 

    A special celery task that automatically retries itself and has no max retries.
    """

    engine = self.app.engine
    logger = logging.getLogger(create_collection_status_records.__name__)

    query = s.sql.text("""
    SELECT repo_id FROM repo WHERE repo_id NOT IN (SELECT repo_id FROM augur_operations.collection_status)
    """)

    repo = execute_sql(query).first()

    with DatabaseSession(logger) as session:

        while repo is not None:
            CollectionStatus.insert(session, logger, repo[0])
            repo = execute_sql(query).first()

    # no longer recursively run this task because collection status records are added when repos are inserted
    #create_collection_status_records.si().apply_async(countdown=60*7)
