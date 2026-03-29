from __future__ import annotations
import logging
import random
import datetime
#from celery.result import AsyncResult
from celery import chain
import sqlalchemy as s
from sqlalchemy import or_, update
from augur.application.logs import AugurLogger
from augur.tasks.init.celery_app import celery_app as celery
from augur.application.db.models import CollectionStatus, Repo
from augur.application.db.util import execute_session_query
from augur.tasks.github.util.util import get_repo_weight_core, get_repo_weight_by_issue
from augur.application.db import get_engine
from augur.application.db.lib import execute_sql, get_session, get_active_repo_count, get_repo_by_repo_git
from augur.tasks.util.worker_util import calculate_date_weight_from_timestamps
from augur.tasks.util.collection_state import CollectionState
from augur.application.db.session import DatabaseSession
from augur.application.config import AugurConfig


class CollectionRequest:
    def __init__(self,name,phases,max_repo = 10,days_until_collect_again = 1, gitlab_phases=None):
        self.name = name
        self.phases = phases
        self.gitlab_phases = gitlab_phases
        self.max_repo = max_repo
        self.days_until_collect_again = days_until_collect_again
        self.new_status = CollectionState.PENDING.value
        self.repo_list = []

        self.status_column = f"{name}_status"


        if name == "facade":
            self.new_status = CollectionState.UPDATE.value

    def get_valid_repos(self,session):

        active_repo_count = get_active_repo_count(self.name)
        limit = self.max_repo-active_repo_count

        if limit <= 0:
            return

        new_collection_git_list = get_newly_added_repos(session, limit, hook=self.name)
        collection_list = [(repo_git, True) for repo_git in new_collection_git_list]
        self.repo_list.extend(collection_list)
        limit -= len(collection_list)

        #Now start recollecting other repos if there is space to do so.
        if limit <= 0:
            return

        recollection_git_list = get_repos_for_recollection(session, limit, hook=self.name, days_until_collect_again=self.days_until_collect_again)
        collection_list = [(repo_git, False) for repo_git in recollection_git_list]
        self.repo_list.extend(collection_list)


def get_newly_added_repos(session, limit, hook):

    condition_string = ""
    order_by_field = ""
    if hook in ["core", "secondary", "ml"]:
        condition_string += f"""{hook}_status='{str(CollectionState.PENDING.value)}'"""
        order_by_field = "issue_pr_sum"
        
    elif hook == "facade":
        condition_string += f"""facade_status='{str(CollectionState.UPDATE.value)}'"""
        order_by_field = "commit_sum"

    if hook == "secondary":
        condition_string += f""" and core_status='{str(CollectionState.SUCCESS.value)}'"""

    repo_query = s.sql.text(f"""
        select repo_git 
        from augur_operations.collection_status x, augur_data.repo y 
        where x.repo_id=y.repo_id 
        and {condition_string}
        order by {order_by_field}
        limit :limit_num
    """).bindparams(limit_num=limit)

    valid_repos = session.execute_sql(repo_query).fetchall()
    valid_repo_git_list = [repo[0] for repo in valid_repos]

    return valid_repo_git_list

def get_repos_for_recollection(session, limit, hook, days_until_collect_again):

    if hook in ["core", "secondary", "ml"]:
        condition_string = f"""{hook}_status='{str(CollectionState.SUCCESS.value)}'"""
        
    elif hook == "facade":
        condition_string = f"""facade_status='{str(CollectionState.SUCCESS.value)}'"""

    repo_query = s.sql.text(f"""
        select repo_git 
        from augur_operations.collection_status x,  repo y 
        where x.repo_id = y.repo_id
        and {condition_string}
        and {hook}_data_last_collected <= NOW() - INTERVAL '{days_until_collect_again} DAYS'
        order by {hook}_data_last_collected 
        limit :limit_num
    """).bindparams(limit_num=limit)

    valid_repos = session.execute_sql(repo_query).fetchall()
    valid_repo_git_list = [repo[0] for repo in valid_repos]

    return valid_repo_git_list


def get_enabled_phase_names_from_config(engine, logger):
    with DatabaseSession(logger, engine) as session:
        return get_enabled_phase_names_from_config_session(session, logger)


def get_enabled_phase_names_from_config_session(session, logger):

    config = AugurConfig(logger, session)
    return get_enabled_phase_names_from_config_object(config)


def get_enabled_phase_names_from_config_object(config):
    phase_options = config.get_section("Task_Routine")

    #Get list of enabled phases 
    enabled_phase_names = [name for name, phase in phase_options.items() if phase == 1]

    return enabled_phase_names

#Query db for CollectionStatus records that fit the desired condition.
#Used to get CollectionStatus for differant collection hooks
def get_collection_status_repo_git_from_filter(session,filter_condition,limit,order=None):

    if order is not None:
        repo_status_list = session.query(CollectionStatus).order_by(order).filter(filter_condition).limit(limit).all()
    else:
        repo_status_list = session.query(CollectionStatus).filter(filter_condition).limit(limit).all()

    return [status.repo.repo_git for status in repo_status_list]


def split_list_into_chunks(given_list, num_chunks):
    #Split list up into four parts with python list comprehension
    #variable n is the 
    n = 1 + (len(given_list) // num_chunks)
    return [given_list[i:i + n] for i in range(0, len(given_list),n)]


@celery.task(bind=True)
def task_failed_util(self, request,exc,traceback):

    engine = self.app.engine

    logger = logging.getLogger(task_failed_util.__name__)

    # log traceback to error file
    logger.error(f"Task {request.id} raised exception: {exc}\n{traceback}")
    
    with get_session() as session:
        core_id_match = CollectionStatus.core_task_id == request.id
        secondary_id_match = CollectionStatus.secondary_task_id == request.id
        facade_id_match = CollectionStatus.facade_task_id == request.id

        query = session.query(CollectionStatus).filter(or_(core_id_match,secondary_id_match,facade_id_match))

        print(f"chain: {request.chain}")
        #Make sure any further execution of tasks dependent on this one stops.
        try:
            #Replace the tasks queued ahead of this one in a chain with None.
            request.chain = None
        except AttributeError:
            pass #Task is not part of a chain. Normal so don't log.
        except Exception as e:
            logger.error(f"Could not mutate request chain! \n Error: {e}")
        
        try:
            collectionRecord = execute_session_query(query,'one')
        except:
            #Exit if we can't find the record.
            return
        
        if collectionRecord.core_task_id == request.id:
            # set status to Error in db
            collectionRecord.core_status = CollectionStatus.ERROR.value
            collectionRecord.core_task_id = None
        

        if collectionRecord.secondary_task_id == request.id:
            # set status to Error in db
            collectionRecord.secondary_status = CollectionStatus.ERROR.value
            collectionRecord.secondary_task_id = None
            
        
        if collectionRecord.facade_task_id == request.id:
            #Failed clone is differant than an error in collection.
            if collectionRecord.facade_status != CollectionStatus.FAILED_CLONE.value or collectionRecord.facade_status != CollectionStatus.UPDATE.value:
                collectionRecord.facade_status = CollectionStatus.ERROR.value

            collectionRecord.facade_task_id = None
        
        session.commit()
    


#This task updates the core and secondary weight with the issues and prs already passed in
@celery.task(bind=True)
def issue_pr_task_update_weight_util(self, issue_and_pr_nums,repo_git=None,session=None):

    engine = self.app.engine
    logger = logging.getLogger(issue_pr_task_update_weight_util.__name__)

    if repo_git is None:
        return
    
    if session is not None:
        update_issue_pr_weights(logger, session, repo_git, sum(issue_and_pr_nums))
    else:
        with get_session() as session:
            update_issue_pr_weights(logger,session,repo_git,sum(issue_and_pr_nums))


@celery.task(bind=True)
def core_task_success_util(self, repo_git):

    engine = self.app.engine

    logger = logging.getLogger(core_task_success_util.__name__)

    logger.info(f"Repo '{repo_git}' succeeded through core collection")

    with get_session() as session:

        repo = Repo.get_by_repo_git(session, repo_git)
        if not repo:
            raise Exception(f"Task with repo_git of {repo_git} but could not be found in Repo table")

        collection_status = repo.collection_status[0]

        collection_status.core_status = CollectionState.SUCCESS.value
        collection_status.core_data_last_collected = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        collection_status.core_task_id = None

        session.commit()

        repo_git = repo.repo_git
        status = repo.collection_status[0]
        raw_count = status.issue_pr_sum

        #Update the values for core and secondary weight
        issue_pr_task_update_weight_util([int(raw_count)],repo_git=repo_git,session=session)

#Update the existing core and secondary weights as well as the raw sum of issues and prs
def update_issue_pr_weights(logger,session,repo_git,raw_sum):
    repo = Repo.get_by_repo_git(session, repo_git)
    status = repo.collection_status[0]

    try: 
        weight = raw_sum

        weight -= calculate_date_weight_from_timestamps(repo.repo_added, status.core_data_last_collected)

        secondary_tasks_weight = raw_sum - calculate_date_weight_from_timestamps(repo.repo_added, status.secondary_data_last_collected)

        ml_tasks_weight = raw_sum - calculate_date_weight_from_timestamps(repo.repo_added,status.ml_data_last_collected)
    except Exception as e:
        logger.error(f"{e}")
        weight = None
        secondary_tasks_weight = None

    logger.info(f"Repo {repo_git} has a weight of {weight}")

    logger.info(f"Args: {raw_sum} , {repo_git}")

    if weight is None:
        return


    update_query = (
        update(CollectionStatus)
        .where(CollectionStatus.repo_id == repo.repo_id)
        .values(core_weight=weight,issue_pr_sum=raw_sum,secondary_weight=secondary_tasks_weight,ml_weight=ml_tasks_weight)
    )

    session.execute(update_query)
    session.commit()



@celery.task(bind=True)
def secondary_task_success_util(self, repo_git):

    engine = self.app.engine

    logger = logging.getLogger(secondary_task_success_util.__name__)

    logger.info(f"Repo '{repo_git}' succeeded through secondary collection")

    with get_session() as session:

        repo = Repo.get_by_repo_git(session, repo_git)
        if not repo:
            raise Exception(f"Task with repo_git of {repo_git} but could not be found in Repo table")

        collection_status = repo.collection_status[0]

        collection_status.secondary_status = CollectionState.SUCCESS.value
        collection_status.secondary_data_last_collected	 = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        collection_status.secondary_task_id = None

        session.commit()

        #Update the values for core and secondary weight
        repo_git = repo.repo_git
        status = repo.collection_status[0]
        raw_count = status.issue_pr_sum

        issue_pr_task_update_weight_util([int(raw_count)],repo_git=repo_git,session=session)

#Get the weight for each repo for the secondary collection hook.
def get_repo_weight_secondary(logger,repo_git):

    engine = get_engine()

    with get_session() as session:
        repo = Repo.get_by_repo_git(session, repo_git)
        if not repo:
            raise Exception(f"Task with repo_git of {repo_git} but could not be found in Repo table")

        status = repo.collection_status[0]

        last_collected = status.secondary_data_last_collected

        if last_collected:
            time_delta = datetime.datetime.now() - status.secondary_data_last_collected
            days = time_delta
        else:
            days = 0

        return get_repo_weight_by_issue(logger, repo_git, days)


@celery.task(bind=True)
def facade_task_success_util(self, repo_git):

    engine = self.app.engine

    logger = logging.getLogger(facade_task_success_util.__name__)

    logger.info(f"Repo '{repo_git}' succeeded through facade task collection")

    with get_session() as session:

        repo = Repo.get_by_repo_git(session, repo_git)
        if not repo:
            raise Exception(f"Task with repo_git of {repo_git} but could not be found in Repo table")

        collection_status = repo.collection_status[0]

        collection_status.facade_status = CollectionState.SUCCESS.value
        collection_status.facade_data_last_collected = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        collection_status.facade_task_id = None

        session.commit()

@celery.task(bind=True)
def ml_task_success_util(self, repo_git):

    engine = self.app.engine

    logger = logging.getLogger(facade_task_success_util.__name__)

    logger.info(f"Repo '{repo_git}' succeeded through machine learning task collection")

    with get_session() as session:

        repo = Repo.get_by_repo_git(session, repo_git)
        if not repo:
            raise Exception(f"Task with repo_git of {repo_git} but could not be found in Repo table")

        collection_status = repo.collection_status[0]

        collection_status.ml_status = CollectionState.SUCCESS.value
        collection_status.ml_data_last_collected = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        collection_status.ml_task_id = None

        session.commit()



@celery.task(bind=True)
def facade_clone_success_util(self, repo_git):

    engine = self.app.engine

    logger = logging.getLogger(facade_clone_success_util.__name__)

    logger.info(f"Repo '{repo_git}' succeeded through facade update/clone")

    with get_session() as session:

        repo = Repo.get_by_repo_git(session, repo_git)
        if not repo:
            raise Exception(f"Task with repo_git of {repo_git} but could not be found in Repo table")

        collection_status = repo.collection_status[0]

        collection_status.facade_status = CollectionState.UPDATE.value
        collection_status.facade_task_id = None

        session.commit()


class AugurCollectionTotalRepoWeight:
    """
        small class to encapsulate the weight calculation of each repo that is
        being scheduled. Intended to be used as a counter where while it is greater than
        one it is subtracted from until it reaches zero. The weight calculation starts
        from a default method for core repos and can be passed differant calculations accordingly
        as a function that takes a repo_git


    Attributes:
        logger (Logger): Get logger from AugurLogger
        value (int): current value of the collection weight
        value_weight_calculation (function): Function to use on repo to determine weight
    """
    def __init__(self,starting_value: int, weight_calculation=get_repo_weight_core):
        self.logger = AugurLogger("data_collection_jobs").get_logger()
        self.value = starting_value
        self.value_weight_calculation = weight_calculation
    
    #This class can have it's value subtracted using a Repo orm class
    #or a plain integer value.
    def __sub__(self, other):

        if isinstance(other, int):
            self.value -= other
        elif isinstance(other, AugurCollectionTotalRepoWeight):
            self.value -= other.value
        elif isinstance(other, Repo):
            repo_weight = self.value_weight_calculation(self.logger,other.repo_git)
            self.value -= repo_weight
        elif isinstance(other, str):
            repo_weight = self.value_weight_calculation(self.logger,other)
            self.value -= repo_weight
        else:
            raise TypeError(f"Could not subtract object of type {type(other)}")

        if self.value < 0:
            self.value = 0

        return self


class AugurTaskRoutine:
    """
        class to keep track of various groups of collection tasks for a group of repos.
        Simple version to just schedule a number of repos not worrying about repo weight.
        The repo weight matters when constructing the CollectionRequest through get_valid_repos
        Used when scheduling repo clones/updates.


    Attributes:
        logger (Logger): Get logger from AugurLogger
        repos (List[str]): List of repo_ids to run collection on.
        collection_phases (List[str]): List of phases to run in augur collection.
        collection_hook (str): String determining the attributes to update when collection for a repo starts. e.g. core
        session: Database session to use
    """
    def __init__(self, logger,collection_hooks):
        self.logger = logger

        self.collection_hooks = collection_hooks

    def update_status_and_id(self,repo_git, task_id, name, session):
        # NOTE: Can't simply replace with lib method because it is doing .collection_status[0] afterwards
        repo = session.query(Repo).filter(Repo.repo_git == repo_git).one()

        #Set status in database to collecting
        repoStatus = repo.collection_status[0]
        #
        setattr(repoStatus,f"{name}_task_id",task_id)
        setattr(repoStatus,f"{name}_status", CollectionState.COLLECTING.value)
        session.commit()


    def start_data_collection(self):
        """Start all task items and return.

            The purpose is to encapsulate both preparing each message to the broker
            and starting the tasks for each repo in a general sense.
            This way all the specific stuff for each collection hook/ repo
            is generalized.
        """

        #Send messages starts each repo and yields its running info
        #to concurrently update the correct field in the database.

        with get_session() as session:

            for repo_git, task_id, hook_name in self.send_messages():
                self.update_status_and_id(repo_git,task_id,hook_name, session)
    
    def send_messages(self):
        augur_collection_list = []
        
        for col_hook in self.collection_hooks:

            self.logger.info(f"Starting collection on {len(col_hook.repo_list)} {col_hook.name} repos")

            for repo_git, full_collection in col_hook.repo_list:

                repo = get_repo_by_repo_git(repo_git)
                platform_name = "github"
                # this needs to be here and not up a level since it should be set/reset for each repo.
                # otherwise a gitlab repo would reset it and cause subsequent github repos to use gitlab phases.
                phases = None
                if "github" in repo.repo_git:
                    phases = col_hook.phases
                    # use default platform name

                elif "gitlab" in repo.repo_git:
                    platform_name = "gitlab"
                    if col_hook.gitlab_phases is None:
                        continue
                    phases = col_hook.gitlab_phases
           
                augur_collection_sequence = []
                for job in phases:
                    #Add the phase to the sequence in order as a celery task.
                    #The preliminary task creates the larger task chain 
                    augur_collection_sequence.append(job(repo_git, full_collection))

                #augur_collection_sequence.append(core_task_success_util.si(repo_git))
                #Link all phases in a chain and send to celery
                augur_collection_chain = chain(*augur_collection_sequence)
                task_id = augur_collection_chain.apply_async().task_id

                self.logger.info(f"Setting {platform_name} repo {col_hook.name} status to collecting for repo: {repo_git}")

                #yield the value of the task_id to the calling method so that the proper collectionStatus field can be updated
                yield repo_git, task_id, col_hook.name
                
