#SPDX-License-Identifier: MIT

"""
Augur library commands for controlling the backend components
"""

import os
import click
import subprocess
import uuid
import time
# from redis.exceptions import ConnectionError as RedisConnectionError

from augur import instance_id
from augur.application.logs import AugurLogger
from augur.application.config import AugurConfig
from augur.application.db.session import DatabaseSession
from augur.application.cli import test_connection, test_db_connection
from augur.application.cli._cli_util import clear_rabbitmq_messages, raise_open_file_limit


logger = AugurLogger("augur", reset_logfiles=False).get_logger()

@click.group('celery', short_help='Commands for controlling the backend API server & data collection workers')
def cli():
    """Placeholder docstring."""

@cli.command("start")
@test_connection
@test_db_connection
def start():
    """Start Augur's celery process."""

    raise_open_file_limit(100000)

    scheduling_worker_process = None
    core_worker_process = None
    secondary_worker_process = None
    
    
    with DatabaseSession(logger) as session:
        config = AugurConfig(logger, session)
        core_count = config.get_value("Celery", "core_worker_count")
        secondary_count = config.get_value("Celery", "secondary_worker_count")
       

    scheduling_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency=1 -n scheduling:{uuid.uuid4().hex}@%h -Q scheduling"
    core_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={core_count} -n core:{uuid.uuid4().hex}@%h"
    secondary_worker = f"celery -A augur.tasks.init.celery_app.celery_app worker -l info --concurrency={secondary_count} -n secondary:{uuid.uuid4().hex}@%h -Q secondary"

    
    scheduling_worker_process = subprocess.Popen(scheduling_worker.split(" "))
    core_worker_process = subprocess.Popen(core_worker.split(" "))
    secondary_worker_process = subprocess.Popen(secondary_worker.split(" "))
    time.sleep(5)

    try:
        scheduling_worker_process.wait()
    except KeyboardInterrupt:

        if scheduling_worker_process or core_worker_process or secondary_worker_process:
            logger.info("Shutting down celery process")

        if scheduling_worker_process:
            scheduling_worker_process.terminate()

        if core_worker_process:
            core_worker_process.terminate()

        if secondary_worker_process:
            secondary_worker_process.terminate()

        try:
            clear_rabbitmq_messages()
            
        except Exception as e:
            pass

@cli.command("clear-tasks")
@test_connection
@test_db_connection
def clear():


    while True:

        user_input = str(input("Warning this will remove all the tasks from all instances on this server!\nWould you like to proceed? [y/N]"))

        if not user_input:
            logger.info("Exiting")
            return
        
        if user_input in ("y", "Y", "Yes", "yes"):
            logger.info("Removing all tasks")
            celery_purge_command = "celery -A augur.tasks.init.celery_app.celery_app purge -f"
            subprocess.call(celery_purge_command.split(" "))
            return

        elif user_input in ("n", "N", "no", "NO"):
            logger.info("Exiting")
            return
        else:
            logger.error("Invalid input")

    
