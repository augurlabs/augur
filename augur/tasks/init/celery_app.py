"""Defines the Celery app."""
from celery.signals import worker_process_init, worker_process_shutdown
import logging
from typing import List, Dict
import os
import datetime
import traceback
import inspect
import celery
from celery import Celery
from celery.signals import after_setup_logger


from augur.application.logs import TaskLogConfig, AugurLogger
from augur.application.db.session import DatabaseSession
from augur.application.db import get_engine
from augur.application.db.lib import get_session
from augur.application.config import AugurConfig
from augur.tasks.init import get_redis_conn_values, get_rabbitmq_conn_string
from augur.application.db.models import Repo
from augur.tasks.util.collection_state import CollectionState

logger = logging.getLogger(__name__)

start_tasks = ['augur.tasks.start_tasks',
                'augur.tasks.data_analysis',
                'augur.tasks.util.collection_util']

github_tasks = ['augur.tasks.github.contributors',
                'augur.tasks.github.issues',
                'augur.tasks.github.pull_requests.tasks',
                'augur.tasks.github.events',
                'augur.tasks.github.messages',
                'augur.tasks.github.facade_github.tasks',
                'augur.tasks.github.releases.tasks',
                'augur.tasks.github.repo_info.tasks',
                'augur.tasks.github.detect_move.tasks',
                'augur.tasks.github.pull_requests.files_model.tasks',
                'augur.tasks.github.pull_requests.commits_model.tasks',
                'augur.tasks.github.traffic', 
                'augur.tasks.github.util.populate_repo_src_id']

gitlab_tasks = ['augur.tasks.gitlab.merge_request_task',
                'augur.tasks.gitlab.issues_task',
                'augur.tasks.gitlab.events_task']

git_tasks = ['augur.tasks.git.facade_tasks',
            'augur.tasks.git.dependency_tasks.tasks',
            'augur.tasks.git.dependency_libyear_tasks.tasks',
            'augur.tasks.git.scc_value_tasks.tasks']

data_analysis_tasks = ['augur.tasks.data_analysis.message_insights.tasks',
                       'augur.tasks.data_analysis.clustering_worker.tasks',
                       'augur.tasks.data_analysis.discourse_analysis.tasks',
                       'augur.tasks.data_analysis.pull_request_analysis_worker.tasks',
                       'augur.tasks.data_analysis.insight_worker.tasks',
                       'augur.tasks.data_analysis.contributor_breadth_worker.contributor_breadth_worker']

materialized_view_tasks = ['augur.tasks.db.refresh_materialized_views']

frontend_tasks = ['augur.tasks.frontend']

tasks = start_tasks + github_tasks + gitlab_tasks + git_tasks + materialized_view_tasks + frontend_tasks

if os.environ.get('AUGUR_DOCKER_DEPLOY') != "1":
    tasks += data_analysis_tasks

redis_db_number, redis_conn_string = get_redis_conn_values()

# initialize the celery app
BROKER_URL = get_rabbitmq_conn_string()#f'{redis_conn_string}{redis_db_number}'
BACKEND_URL = f'{redis_conn_string}{redis_db_number+1}'


#Classes for tasks that take a repo_git as an argument.
class AugurCoreRepoCollectionTask(celery.Task):

    def augur_handle_task_failure(self,exc,task_id,repo_git,logger_name,collection_hook='core',after_fail=CollectionState.ERROR.value):
            
        # Note: I think self.app.engine would work but leaving it to try later
        engine = get_engine()

        task_logger = AugurLogger(logger_name).get_logger()

        task_logger.error(f"Task {task_id} raised exception: {exc}\n Traceback: {''.join(traceback.format_exception(None, exc, exc.__traceback__))}")

        with get_session() as session:
            task_logger.info(f"Repo git: {repo_git}")
            repo = session.query(Repo).filter(Repo.repo_git == repo_git).one()

            repoStatus = repo.collection_status[0]

            #Only set to error if the repo was actually running at the time.
            #This is to allow for things like exiting from collection without error.
            #i.e. detect_repo_move changes the repo's repo_git and resets collection to pending without error
            prevStatus = getattr(repoStatus, f"{collection_hook}_status")

            if prevStatus == CollectionState.COLLECTING.value or prevStatus == CollectionState.INITIALIZING.value:
                setattr(repoStatus, f"{collection_hook}_status", after_fail)
                setattr(repoStatus, f"{collection_hook}_task_id", None)
                session.commit()

    def on_failure(self,exc,task_id,args, kwargs, einfo):
        repo_git = self._extract_repo_git(args, kwargs)
        # log traceback to error file
        self.augur_handle_task_failure(exc, task_id, repo_git, "core_task_failure")

    def _extract_repo_git(self, args, kwargs):
        if 'repo_git' in kwargs:
            return kwargs['repo_git']
        
        sig = inspect.signature(self.run)
        param_names = list(sig.parameters.keys())

        try:
            index = param_names.index('repo_git')
            return args[index]
        except (ValueError, IndexError):
            pass

        return None 

class AugurSecondaryRepoCollectionTask(AugurCoreRepoCollectionTask):
    def on_failure(self,exc,task_id,args, kwargs, einfo):
        
        repo_git = self._extract_repo_git(args, kwargs)
        self.augur_handle_task_failure(exc, task_id, repo_git, "secondary_task_failure",collection_hook='secondary')

class AugurFacadeRepoCollectionTask(AugurCoreRepoCollectionTask):
    def on_failure(self,exc,task_id,args, kwargs, einfo):
        repo_git = self._extract_repo_git(args, kwargs)
        self.augur_handle_task_failure(exc, task_id, repo_git, "facade_task_failure",collection_hook='facade')

class AugurMlRepoCollectionTask(AugurCoreRepoCollectionTask):
    def on_failure(self,exc,task_id,args,kwargs,einfo):
        repo_git = self._extract_repo_git(args, kwargs)
        self.augur_handle_task_failure(exc,task_id,repo_git, "ml_task_failure", collection_hook='ml')



#task_cls='augur.tasks.init.celery_app:AugurCoreRepoCollectionTask'
celery_app = Celery('tasks', broker=BROKER_URL, backend=BACKEND_URL, include=tasks)

# define the queues that tasks will be put in (by default tasks are put in celery queue)
celery_app.conf.task_routes = {
    'augur.tasks.start_tasks.*': {'queue': 'scheduling'},
    'augur.tasks.util.collection_util.*': {'queue': 'scheduling'},
    'augur.tasks.git.facade_tasks.*': {'queue': 'facade'},
    'augur.tasks.github.facade_github.tasks.*': {'queue': 'facade'},
    'augur.tasks.github.pull_requests.commits_model.tasks.*': {'queue': 'secondary'},
    'augur.tasks.github.pull_requests.files_model.tasks.*': {'queue': 'secondary'},
    'augur.tasks.github.pull_requests.tasks.collect_pull_request_reviews': {'queue': 'secondary'},
    'augur.tasks.github.pull_requests.tasks.collect_pull_request_review_comments': {'queue': 'secondary'},
    'augur.tasks.git.dependency_tasks.tasks.process_ossf_dependency_metrics': {'queue': 'secondary'},
    'augur.tasks.git.dependency_tasks.tasks.process_dependency_metrics': {'queue': 'facade'},
    'augur.tasks.git.scc_value_tasks.tasks.process_scc_value_metrics' : {'queue': 'facade'},
    'augur.tasks.git.dependency_libyear_tasks.tasks.process_libyear_dependency_metrics': {'queue': 'facade'},
    'augur.tasks.frontend.*': {'queue': 'frontend'},
    'augur.tasks.data_analysis.contributor_breadth_worker.*': {'queue': 'secondary'},
}

#Setting to be able to see more detailed states of running tasks
celery_app.conf.task_track_started = True

#ignore task results by default
##celery_app.conf.task_ignore_result = True

# store task erros even if the task result is ignored
celery_app.conf.task_store_errors_even_if_ignored = True

# set task default rate limit
celery_app.conf.task_default_rate_limit = '5/s'

# set tasks annotations for rate limiting specific tasks
celery_app.conf.task_annotations = None

# allow workers to be restarted remotely
celery_app.conf.worker_pool_restarts = True



def split_tasks_into_groups(augur_tasks: List[str]) -> Dict[str, List[str]]:
    """Split tasks on the celery app into groups.

    Args:
        augur_tasks: list of tasks specified in augur

    Returns
        The tasks so that they are grouped by the module they are defined in
    """
    grouped_tasks = {}

    for task in augur_tasks: 
        task_divided = task.split(".")

        try:
            grouped_tasks[task_divided[-2]].append(task_divided[-1])
        except KeyError:
            grouped_tasks[task_divided[-2]] = [task_divided[-1]]
    
    return grouped_tasks




@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup task scheduler.

    Note:
        This is where all task scedules are defined and added the celery beat

    Args:
        app: Celery app

    Returns
        The tasks so that they are grouped by the module they are defined in
    """
    from celery.schedules import crontab
    from augur.tasks.start_tasks import augur_collection_monitor
    from augur.tasks.start_tasks import non_repo_domain_tasks, retry_errored_repos, create_collection_status_records
    from augur.tasks.git.facade_tasks import clone_repos
    from augur.tasks.github.contributors import process_contributors
    from augur.tasks.db.refresh_materialized_views import refresh_materialized_views
    from augur.tasks.data_analysis.contributor_breadth_worker.contributor_breadth_worker import contributor_breadth_model
    from augur.application.db import temporary_database_engine

    # Need to engine to be temporary so that there isn't an engine defined when the parent is forked to create worker processes
    with temporary_database_engine() as engine, DatabaseSession(logger, engine) as session:

        config = AugurConfig(logger, session)

        collection_interval = config.get_value('Tasks', 'collection_interval')
        logger.info(f"Scheduling collection every {collection_interval/60} minutes")
        sender.add_periodic_task(collection_interval, augur_collection_monitor.s())

        #Do longer tasks less often
        logger.info(f"Scheduling data analysis every 30 days")
        thirty_days_in_seconds = 30*24*60*60
        sender.add_periodic_task(thirty_days_in_seconds, non_repo_domain_tasks.s())

        mat_views_interval = int(config.get_value('Celery', 'refresh_materialized_views_interval_in_days'))
        if mat_views_interval > 0: 
            logger.info(f"Scheduling refresh materialized view every night at 1am CDT")
            sender.add_periodic_task(datetime.timedelta(days=mat_views_interval), refresh_materialized_views.s())
        else:
            logger.info(f"Refresh materialized view task is disabled.")

        # logger.info(f"Scheduling update of collection weights on midnight each day")
        # sender.add_periodic_task(crontab(hour=0, minute=0),augur_collection_update_weights.s())

        logger.info(f"Setting 404 repos to be marked for retry on midnight each day")
        sender.add_periodic_task(crontab(hour=0, minute=0),retry_errored_repos.s())

        one_hour_in_seconds = 60*60
        sender.add_periodic_task(one_hour_in_seconds, process_contributors.s())

        one_day_in_seconds = 24*60*60
        sender.add_periodic_task(one_day_in_seconds, create_collection_status_records.s())

@after_setup_logger.connect
def setup_loggers(*args,**kwargs):
    """Override Celery loggers with our own."""

    all_celery_tasks = list(celery_app.tasks.keys())

    augur_tasks = [task for task in all_celery_tasks if 'celery.' not in task]
    
    TaskLogConfig(split_tasks_into_groups(augur_tasks))


#engine = None
@worker_process_init.connect
def init_worker(**kwargs):

    celery_app.engine = get_engine()

    # global engine

    # from augur.application.db.engine import DatabaseEngine
    # from sqlalchemy.pool import NullPool, StaticPool

    # engine = DatabaseEngine(poolclass=StaticPool).engine


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):

    from augur.application.db import dispose_database_engine
    dispose_database_engine()

    # global engine
    # if engine:
    #     logger.info('Closing database connectionn for worker')
    #     engine.dispose()


