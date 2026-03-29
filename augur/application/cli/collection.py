#SPDX-License-Identifier: MIT
"""
Augur library commands for controlling the backend components
"""
import os
import time
import subprocess
import click
import logging
import psutil
import signal
from redis.exceptions import ConnectionError as RedisConnectionError
import uuid
import traceback
import sqlalchemy as s

from augur.tasks.start_tasks import augur_collection_monitor, create_collection_status_records
from augur.tasks.git.facade_tasks import clone_repos
from augur.tasks.github.util.github_api_key_handler import GithubApiKeyHandler
from augur.tasks.gitlab.gitlab_api_key_handler import GitlabApiKeyHandler
from augur.tasks.data_analysis.contributor_breadth_worker.contributor_breadth_worker import contributor_breadth_model
from augur.application.db.models import UserRepo
from augur.application.db.session import DatabaseSession
from augur.application.logs import AugurLogger
from augur.application.db.lib import get_value
from augur.application.cli import test_connection, test_db_connection, with_database, DatabaseContext
from augur.application.cli._cli_util import _broadcast_signal_to_processes, raise_open_file_limit, clear_redis_caches, clear_rabbitmq_messages

from keyman.KeyClient import KeyPublisher

logger = AugurLogger("augur", reset_logfiles=False).get_logger()

@click.group('server', short_help='Commands for controlling the backend API server & data collection workers')
@click.pass_context
def cli(ctx):
    ctx.obj = DatabaseContext()

@cli.command("start")
@click.option("--development", is_flag=True, default=False, help="Enable development mode, implies --disable-collection")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def start(ctx, development):
    """Start Augur's backend server."""

    try:
        if os.environ.get('AUGUR_DOCKER_DEPLOY') != "1":
            raise_open_file_limit(100000)
    except Exception as e: 
        logger.error(
                    ''.join(traceback.format_exception(None, e, e.__traceback__)))
        
        logger.error("Failed to raise open file limit!")
        raise e
    
    keypub = KeyPublisher()

    orchestrator = subprocess.Popen("python keyman/Orchestrator.py".split())

    # Wait for orchestrator startup
    if not keypub.wait(republish=True):
        logger.critical("Key orchestrator did not respond in time")
        return
    
    # load keys
    ghkeyman = GithubApiKeyHandler(logger)
    glkeyman = GitlabApiKeyHandler(logger)

    for key in ghkeyman.keys:
        keypub.publish(key, "github_rest")
        keypub.publish(key, "github_graphql")

    for key in glkeyman.keys:
        keypub.publish(key, "gitlab_rest")
    
    if development:
        os.environ["AUGUR_DEV"] = "1"
        logger.info("Starting in development mode")

    core_worker_count = get_value("Celery", 'core_worker_count')
    secondary_worker_count = get_value("Celery", 'secondary_worker_count')
    facade_worker_count = get_value("Celery", 'facade_worker_count')

    process_list = start_celery_collection_processes((core_worker_count, secondary_worker_count, facade_worker_count))

    if os.path.exists("celerybeat-schedule.db"):
            logger.info("Deleting old task schedule")
            os.remove("celerybeat-schedule.db")

    log_level = get_value("Logging", "log_level")
    celery_beat_process = None
    celery_command = f"celery -A augur.tasks.init.celery_app.celery_app beat -l {log_level.lower()}"
    celery_beat_process = subprocess.Popen(celery_command.split(" "))    


    with DatabaseSession(logger, ctx.obj.engine) as session:

        clean_collection_status(session)
        assign_orphan_repos_to_default_user(session)
    
    create_collection_status_records.si().apply_async()
    time.sleep(3)

    contributor_breadth_model.si().apply_async()

    # start cloning repos when augur starts
    clone_repos.si().apply_async()

    augur_collection_monitor.si().apply_async()

    
    try:
        process_list[0].wait()
    except KeyboardInterrupt:

        logger.info("Shutting down all celery worker processes")
        for p in process_list:
            if p:
                p.terminate()

        keypub.shutdown()

        if celery_beat_process:
            logger.info("Shutting down celery beat process")
            celery_beat_process.terminate()
        try:
            cleanup_after_collection_halt(logger, ctx.obj.engine)
        except RedisConnectionError:
            pass

def start_celery_collection_processes(worker_counts: tuple[int, int, int]):
    """
    Args:
        worker_counts (tuple): a tuple of three integers describing how many workers to use for core, secondary, and facade tasks

    Returns:
        list: a list of the collection processes as executed by subprocess.Popen
    """

    process_list = []

    sleep_time = 0

    core_worker_count, secondary_worker_count, facade_worker_count = worker_counts

    #2 processes are always reserved as a baseline.
    scheduling_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency=2 -n scheduling:{uuid.uuid4().hex}@%h -Q scheduling"
    process_list.append(subprocess.Popen(scheduling_worker.split(" ")))
    sleep_time += 6

    logger.info(f"Starting core collection processes with concurrency={core_worker_count}")
    core_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={core_worker_count} -n core:{uuid.uuid4().hex}@%h"
    process_list.append(subprocess.Popen(core_worker.split(" ")))
    sleep_time += 6

    logger.info(f"Starting secondary collection processes with concurrency={secondary_worker_count}")
    secondary_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={secondary_worker_count} -n secondary:{uuid.uuid4().hex}@%h -Q secondary"
    process_list.append(subprocess.Popen(secondary_worker.split(" ")))
    sleep_time += 6

    logger.info(f"Starting facade collection processes with concurrency={facade_worker_count}")
    facade_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={facade_worker_count} -n facade:{uuid.uuid4().hex}@%h -Q facade"
    
    process_list.append(subprocess.Popen(facade_worker.split(" ")))
    sleep_time += 6

    time.sleep(sleep_time)

    return process_list


@cli.command('stop')
@with_database
@click.pass_context
def stop(ctx):
    """
    Sends SIGTERM to all Augur server & worker processes
    """
    cli_logger = logging.getLogger("augur.cli")

    augur_stop(signal.SIGTERM, cli_logger, ctx.obj.engine)

@cli.command('kill')
@with_database
@click.pass_context
def kill(ctx):
    """
    Sends SIGKILL to all Augur server & worker processes
    """
    cli_logger = logging.getLogger("augur.cli")
    augur_stop(signal.SIGKILL, cli_logger, ctx.obj.engine)

@cli.command('repo-reset')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def repo_reset(ctx):
    """
    Refresh repo collection to force data collection
    """
    with ctx.obj.engine.connect() as connection:
        connection.execute(s.sql.text("""
            UPDATE augur_operations.collection_status 
            SET core_status='Pending',core_task_id = NULL, core_data_last_collected = NULL;

            UPDATE augur_operations.collection_status 
            SET secondary_status='Pending',secondary_task_id = NULL, secondary_data_last_collected = NULL;

            UPDATE augur_operations.collection_status 
            SET facade_status='Pending', facade_task_id=NULL, facade_data_last_collected = NULL;

            TRUNCATE augur_data.commits CASCADE;
            """))

        logger.info("Repos successfully reset")

@cli.command('processes')
def processes():
    """
    Outputs the name/PID of all Augur server & worker processes"""
    augur_processes = get_augur_collection_processes()
    for process in augur_processes:
        logger.info(f"Found process {process.pid}")

def get_augur_collection_processes():
    augur_processes = []
    for process in psutil.process_iter(['cmdline', 'name', 'environ']):
        if process.info['cmdline'] is not None and process.info['environ'] is not None:
            try:
                if is_collection_process(process):
                        augur_processes.append(process)
            except (KeyError, FileNotFoundError):
                pass
    return augur_processes

def is_collection_process(process):

    command = ''.join(process.info['cmdline'][:]).lower()
    if os.getenv('VIRTUAL_ENV') in process.info['environ']['VIRTUAL_ENV'] and 'python' in command:
        if process.pid != os.getpid():
            
            if "augurbackendcollection" in command  or "celery_app.celery_appbeat" in command:
                return True 
            if "augur.tasks.init.celery_app.celery_app" in command:
                
                if ("scheduling" in command or
                    "facade" in command or 
                    "secondary" in command or 
                    "core" in command):

                    return True

    return False


def augur_stop(stop_signal, logger_instance, engine):
    """
    Stops augur with the given signal, 
    and cleans up collection if it was running
    """

    augur_collection_processes = get_augur_collection_processes()

    _broadcast_signal_to_processes(augur_collection_processes, logger=logger_instance, broadcast_signal=stop_signal)

    cleanup_after_collection_halt(logger, engine)

def cleanup_after_collection_halt(logger_instance, engine):
    
    queues = ['celery', 'core', 'secondary','scheduling','facade']

    connection_string = get_value("RabbitMQ", "connection_string")

    with DatabaseSession(logger_instance, engine) as session:
        clean_collection_status(session)

    clear_rabbitmq_messages(connection_string, queues, logger_instance)
    clear_redis_caches(logger_instance)

#Make sure that database reflects collection status when processes are killed/stopped.
def clean_collection_status(session):
    session.execute_sql(s.sql.text("""
        UPDATE augur_operations.collection_status 
        SET core_status='Pending',core_task_id = NULL
        WHERE core_status='Collecting' AND core_data_last_collected IS NULL;

        UPDATE augur_operations.collection_status
        SET core_status='Success',core_task_id = NULL
        WHERE core_status='Collecting' AND core_data_last_collected IS NOT NULL;

        UPDATE augur_operations.collection_status 
        SET secondary_status='Pending',secondary_task_id = NULL
        WHERE secondary_status='Collecting' AND secondary_data_last_collected IS NULL;

        UPDATE augur_operations.collection_status 
        SET secondary_status='Success',secondary_task_id = NULL
        WHERE secondary_status='Collecting' AND secondary_data_last_collected IS NOT NULL;

        UPDATE augur_operations.collection_status 
        SET facade_status='Update', facade_task_id=NULL
        WHERE facade_status LIKE '%Collecting%' and facade_data_last_collected IS NULL;

        UPDATE augur_operations.collection_status 
        SET facade_status='Success', facade_task_id=NULL
        WHERE facade_status LIKE '%Collecting%' and facade_data_last_collected IS NOT NULL;

        UPDATE augur_operations.collection_status
        SET facade_status='Pending', facade_task_id=NULL
        WHERE facade_status='Failed Clone' OR facade_status='Initializing';
    """))
    #TODO: write timestamp for currently running repos.

def assign_orphan_repos_to_default_user(session):
    query = s.sql.text("""
        SELECT repo_id FROM repo WHERE repo_id NOT IN (SELECT repo_id FROM augur_operations.user_repos)
    """)

    repos = session.execute_sql(query).fetchall()

    for repo in repos:
        UserRepo.insert(session, repo[0],1)
