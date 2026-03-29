#SPDX-License-Identifier: MIT
"""
Augur library commands for controlling the backend components
"""
import resource
import os
import time
import subprocess
import click
import logging
import psutil
import signal
import uuid
import traceback
import requests
from redis.exceptions import ConnectionError as RedisConnectionError

from augur.tasks.start_tasks import augur_collection_monitor, create_collection_status_records
from augur.tasks.git.facade_tasks import clone_repos
from augur.tasks.github.contributors import process_contributors
from augur.tasks.github.util.github_api_key_handler import GithubApiKeyHandler
from augur.tasks.gitlab.gitlab_api_key_handler import GitlabApiKeyHandler
from augur.tasks.data_analysis.contributor_breadth_worker.contributor_breadth_worker import contributor_breadth_model
from augur.application.db.models import UserRepo
from augur.application.db.session import DatabaseSession
from augur.application.logs import AugurLogger
from augur.application.service_manager import AugurServiceManager, cleanup_collection_status_and_rabbit, clean_collection_status
from augur.application.db.lib import get_value
from augur.application.cli import test_connection, test_db_connection, with_database, DatabaseContext
import sqlalchemy as s

from keyman.KeyClient import KeyClient, KeyPublisher

reset_logs = os.getenv("AUGUR_RESET_LOGS", 'True').lower() in ('true', '1', 't', 'y', 'yes')

logger = AugurLogger("augur", reset_logfiles=reset_logs).get_logger()

@click.group('server', short_help='Commands for controlling the backend API server & data collection workers')
@click.pass_context
def cli(ctx):
    ctx.obj = DatabaseContext()

@cli.command("start")
@click.option("--disable-collection", is_flag=True, default=False, help="Turns off data collection workers")
@click.option("--development", is_flag=True, default=False, help="Enable development mode, implies --disable-collection")
@click.option("--pidfile", default="main.pid", help="File to store the controlling process ID in")
@click.option('--port')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def start(ctx, disable_collection, development, pidfile, port):
    """Start Augur's backend server."""
    with open(pidfile, "w") as pidfile_io:
        pidfile_io.write(str(os.getpid()))

    manager = AugurServiceManager(ctx, pidfile, disable_collection)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, manager.shutdown_signal_handler)
    signal.signal(signal.SIGINT, manager.shutdown_signal_handler)

    try:
        if os.environ.get('AUGUR_DOCKER_DEPLOY') != "1":
            raise_open_file_limit(100000)
    except Exception as e:
        logger.error(
                    ''.join(traceback.format_exception(None, e, e.__traceback__)))

        logger.error("Failed to raise open file limit!")
        raise e

    if development:
        os.environ["AUGUR_DEV"] = "1"
        logger.info("Starting in development mode")
    
    os.environ["AUGUR_PIDFILE"] = pidfile

    try:
        gunicorn_location = os.getcwd() + "/augur/api/gunicorn_conf.py"
    except FileNotFoundError:
        logger.error("\n\nPlease run augur commands in the root directory\n\n")

    host = get_value("Server", "host")

    if not port:
        port = get_value("Server", "port")
    
    os.environ["AUGUR_PORT"] = str(port)
    
    if disable_collection:
        os.environ["AUGUR_DISABLE_COLLECTION"] = "1"
    
    core_worker_count = get_value("Celery", 'core_worker_count')
    secondary_worker_count = get_value("Celery", 'secondary_worker_count')
    facade_worker_count = get_value("Celery", 'facade_worker_count')


    # create rabbit messages so if it failed on shutdown the queues are clean
    cleanup_collection_status_and_rabbit(logger, ctx.obj.engine)

    # Retrieve the log directory from the configuration or default to current directory
    log_dir = get_value("Logging", "logs_directory") or "."
    gunicorn_log_file = os.path.join(log_dir, "gunicorn.log")

    gunicorn_command = f"gunicorn -c {gunicorn_location} -b {host}:{port} augur.api.server:app --log-file {gunicorn_log_file}"
    server = subprocess.Popen(gunicorn_command.split(" "))
    manager.server = server

    logger.info("awaiting Gunicorn start")
    while not server.poll():
        try:
            api_response = requests.get(f"http://{host}:{port}/api")
        except requests.exceptions.ConnectionError as e:
            time.sleep(0.5)
            continue
        
        if not api_response.ok:
            logger.critical("Gunicorn failed to start or was not reachable. Exiting")
            exit(247)
        break
    else:
        logger.critical("Gunicorn was shut down abnormally. Exiting")
        exit(247)
    
    logger.info('Gunicorn webserver started...')
    logger.info(f'Augur is running at: {"http" if development else "https"}://{host}:{port}')
    logger.info(f"The API is available at '{api_response.json()['route']}'")

    processes = start_celery_worker_processes((core_worker_count, secondary_worker_count, facade_worker_count), disable_collection)
    manager.processes = processes

    celery_beat_schedule_db = os.getenv("CELERYBEAT_SCHEDULE_DB", "celerybeat-schedule.db")
    if os.path.exists(celery_beat_schedule_db):
            logger.info("Deleting old task schedule")
            os.remove(celery_beat_schedule_db)

    log_level = get_value("Logging", "log_level")
    celery_beat_process = None
    celery_command = f"celery -A augur.tasks.init.celery_app.celery_app beat -l {log_level.lower()} -s {celery_beat_schedule_db}"
    celery_beat_process = subprocess.Popen(celery_command.split(" "))
    manager.celery_beat_process = celery_beat_process    
    keypub = KeyPublisher()
    manager.keypub = keypub
    
    if not disable_collection:
        if os.environ.get('AUGUR_DOCKER_DEPLOY') != "1":
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
            keypub.publish(key, "github_search")

        for key in glkeyman.keys:
            keypub.publish(key, "gitlab_rest")
        
        with DatabaseSession(logger, engine=ctx.obj.engine) as session:

            clean_collection_status(session)
            assign_orphan_repos_to_default_user(session)
        
        create_collection_status_records.si().apply_async()
        time.sleep(3)

        #put contributor breadth back in. Not sure why it was commented out
        contributor_breadth_model.si().apply_async()

        # start cloning repos when augur starts
        clone_repos.si().apply_async()

        process_contributors.si().apply_async()

        augur_collection_monitor.si().apply_async()
        
    else:
        logger.info("Collection disabled")
    
    try:
        server.wait()
    except KeyboardInterrupt:
        # Signal handler will take care of cleanup
        pass
    finally:
        # Ensure pidfile is cleaned up if we exit normally
        if os.path.exists(pidfile):
            try:
                os.unlink(pidfile)
            except OSError as e:
                logger.error(f"Could not remove pidfile {pidfile}: {e}")

def start_celery_worker_processes(worker_counts: tuple[int, int, int], disable_collection=False):
    """
    Args:
        worker_counts (tuple): a tuple of three integers describing how many workers to use for core, secondary, and facade tasks
        disable_collection (bool, optional): whether to disable collection entirely and not schedule any actual task workers. Defaults to False.

    Returns:
        list: a list of the worker processes as executed by subprocess.Popen
    """

    #Calculate process scaling based on how much memory is available on the system in bytes.
    #Each celery process takes ~500MB or 500 * 1024^2 bytes

    process_list = []

    core_worker_count, secondary_worker_count, facade_worker_count = worker_counts

    sleep_time = 0
    
    frontend_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency=1 -n frontend:{uuid.uuid4().hex}@%h -Q frontend"
    process_list.append(subprocess.Popen(frontend_worker.split(" ")))
    sleep_time += 6

    if not disable_collection:

        #2 processes are always reserved as a baseline.
        scheduling_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency=2 -n scheduling:{uuid.uuid4().hex}@%h -Q scheduling"
        process_list.append(subprocess.Popen(scheduling_worker.split(" ")))
        sleep_time += 6
        logger.info(f"Starting core worker processes with concurrency={core_worker_count}")
        core_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={core_worker_count} -n core:{uuid.uuid4().hex}@%h"
        process_list.append(subprocess.Popen(core_worker.split(" ")))
        sleep_time += 6

        logger.info(f"Starting secondary worker processes with concurrency={secondary_worker_count}")
        secondary_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={secondary_worker_count} -n secondary:{uuid.uuid4().hex}@%h -Q secondary"
        process_list.append(subprocess.Popen(secondary_worker.split(" ")))
        sleep_time += 6

        logger.info(f"Starting facade worker processes with concurrency={facade_worker_count}")
        facade_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={facade_worker_count} -n facade:{uuid.uuid4().hex}@%h -Q facade"
        
        process_list.append(subprocess.Popen(facade_worker.split(" ")))
        sleep_time += 6

    time.sleep(sleep_time)

    return process_list


@cli.command('stop')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def stop(ctx):
    """
    Sends SIGTERM to all Augur server & worker processes
    """
    logger = logging.getLogger("augur.cli")

    augur_stop(signal.SIGTERM, logger, ctx.obj.engine)

@cli.command('stop-collection-blocking')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def stop_collection(ctx):
    """
    Stop collection tasks if they are running, block until complete
    """
    processes = get_augur_processes()
    
    stopped = []
    
    p: psutil.Process
    for p in processes:
        if p.name() == "celery":
            stopped.append(p)
            p.terminate()
    
    if not len(stopped):
        logger.info("No collection processes found")
        return
    
    _, alive = psutil.wait_procs(stopped, 5,
                                 lambda p: logger.info(f"STOPPED: {p.pid}"))
    
    killed = []
    while True:
        for i in range(len(alive)):
            if alive[i].status() == psutil.STATUS_ZOMBIE:
                logger.info(f"KILLING ZOMBIE: {alive[i].pid}")
                alive[i].kill()
                killed.append(i)
            elif not alive[i].is_running():
                logger.info(f"STOPPED: {p.pid}")
                killed.append(i)
        
        for i in reversed(killed):
            alive.pop(i)
        
        if not len(alive):
            break
        
        logger.info(f"Waiting on [{', '.join(str(p.pid for p in alive))}]")
        time.sleep(0.5)
    
    cleanup_collection_status_and_rabbit(logger, ctx.obj.engine)

@cli.command('kill')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def kill(ctx):
    """
    Sends SIGKILL to all Augur server & worker processes
    """
    logger = logging.getLogger("augur.cli")
    augur_stop(signal.SIGKILL, logger, ctx.obj.engine)


def augur_stop(signal, logger, engine):
    """
    Stops augur with the given signal, 
    and cleans up collection if it was running
    """

    augur_processes = get_augur_processes()
    # if celery is running, run the cleanup function
    process_names = [process.name() for process in augur_processes]

    _broadcast_signal_to_processes(augur_processes, broadcast_signal=signal, given_logger=logger)

    if "celery" in process_names:
        cleanup_collection_status_and_rabbit(logger, engine)


def assign_orphan_repos_to_default_user(session):
    query = s.sql.text("""
        SELECT repo_id FROM repo WHERE repo_id NOT IN (SELECT repo_id FROM augur_operations.user_repos)
    """)

    repos = session.execute_sql(query).fetchall()

    for repo in repos:
        UserRepo.insert(session, repo[0],1)


@cli.command('export-env')
def export_env(config):
    """
    Exports your GitHub key and database credentials
    """

    export_file = open(os.getenv('AUGUR_EXPORT_FILE', 'augur_export_env.sh'), 'w+')
    export_file.write('#!/bin/bash')
    export_file.write('\n')
    env_file = open(os.getenv('AUGUR_ENV_FILE', 'docker_env.txt'), 'w+')

    for env_var in config.get_env_config().items():
        if "LOG" not in env_var[0]:
            logger.info(f"Exporting {env_var[0]}")
            export_file.write('export ' + env_var[0] + '="' + str(env_var[1]) + '"\n')
            env_file.write(env_var[0] + '=' + str(env_var[1]) + '\n')

    export_file.close()
    env_file.close()

@cli.command('repo-reset')
@test_connection
@test_db_connection
def repo_reset(augur_app):
    """
    Refresh repo collection to force data collection
    """
    augur_app.database.execute(s.sql.text("""
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
    augur_processes = get_augur_processes()
    for process in augur_processes:
        logger.info(f"Found process {process.pid} [{process.name()}] -> Parent: {process.parent().pid}")

def get_augur_processes():
    augur_processes = []
    for process in psutil.process_iter(['cmdline', 'name', 'environ']):
        if process.info['cmdline'] is not None and process.info['environ'] is not None:
            try:
                if os.getenv('VIRTUAL_ENV') in process.info['environ']['VIRTUAL_ENV'] and 'python' in ''.join(process.info['cmdline'][:]).lower():
                    if process.pid != os.getpid():
                        augur_processes.append(process)
            except (KeyError, FileNotFoundError):
                pass
    return augur_processes

def _broadcast_signal_to_processes(processes, broadcast_signal=signal.SIGTERM, given_logger=None):
    if given_logger is None:
        _logger = logger
    else:
        _logger = given_logger
    for process in processes:
        if process.pid != os.getpid():
            logger.info(f"Stopping process {process.pid}")
            try:
                process.send_signal(broadcast_signal)
            except psutil.NoSuchProcess:
                pass


def raise_open_file_limit(num_files):
    """
    sets number of open files soft limit 
    """
    current_soft, current_hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    # if soft is already greater than the requested amount then don't change it
    if current_soft > num_files:
        return

    # if the requested amount is greater than the hard limit then set the hard limit to the num_files value
    if current_hard <= num_files:
        current_hard = num_files

    resource.setrlimit(resource.RLIMIT_NOFILE, (num_files, current_hard))

    return

# def initialize_components(augur_app, disable_housekeeper):
#     master = None
#     manager = None
#     broker = None
#     housekeeper = None
#     worker_processes = []
#     mp.set_start_method('forkserver', force=True)

#     if not disable_housekeeper:

#         manager = mp.Manager()
#         broker = manager.dict()
#         housekeeper = Housekeeper(broker=broker, augur_app=augur_app)

#         controller = augur_app.config.get_section('Workers')
#         for worker in controller.keys():
#             if controller[worker]['switch']:
#                 for i in range(controller[worker]['workers']):
#                     logger.info("Booting {} #{}".format(worker, i + 1))
#                     worker_process = mp.Process(target=worker_start, name=f"{worker}_{i}", kwargs={'worker_name': worker, 'instance_number': i, 'worker_port': controller[worker]['port']}, daemon=True)
#                     worker_processes.append(worker_process)
#                     worker_process.start()

#     augur_app.manager = manager
#     augur_app.broker = broker
#     augur_app.housekeeper = housekeeper

#     atexit._clear()
#     atexit.register(exit, augur_app, worker_processes, master)
#     return AugurGunicornApp(augur_app.gunicorn_options, augur_app=augur_app)

# def worker_start(worker_name=None, instance_number=0, worker_port=None):
#     try:
#         time.sleep(30 * instance_number)
#         destination = subprocess.DEVNULL
#         process = subprocess.Popen("cd workers/{} && {}_start".format(worker_name,worker_name), shell=True, stdout=destination, stderr=subprocess.STDOUT)
#         logger.info("{} #{} booted.".format(worker_name,instance_number+1))
#     except KeyboardInterrupt as e:
#         pass
