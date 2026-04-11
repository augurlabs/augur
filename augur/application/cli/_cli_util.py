import resource
import os
import subprocess
import psutil
import signal
from urllib.parse import urlparse
import sqlalchemy as s

from augur.tasks.init.redis_connection import get_redis_connection

def clear_redis_caches(logger):
    """Clears the redis databases that celery and redis use."""

    logger.info("Flushing all redis databases this instance was using")
    celery_purge_command = "celery -A augur.tasks.init.celery_app.celery_app purge -f"
    subprocess.call(celery_purge_command.split(" "))


    redis_connection = get_redis_connection()
    redis_connection.flushdb()


def clear_rabbitmq_messages(connection_string, queues, logger):
    #virtual_host_string = connection_string.split("/")[-1]

    logger.info("Clearing all messages from celery queue in rabbitmq")
    from augur.tasks.init.celery_app import celery_app
    celery_app.control.purge()

    clear_message_queues(connection_string, queues)


def clear_message_queues(connection_string, queues):
    queues = ['celery','secondary','scheduling','facade']

    virtual_host_string = connection_string.split("/")[-1]

    #Parse username and password with urllib
    parsed = urlparse(connection_string)

    for q in queues:
        curl_cmd = f"curl -i -u {parsed.username}:{parsed.password} -XDELETE http://localhost:15672/api/queues/{virtual_host_string}/{q}"
        subprocess.call(curl_cmd.split(" "),stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _broadcast_signal_to_processes(processes, logger, broadcast_signal=signal.SIGTERM):

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

def get_db_version(engine):
    """ a helper function to return the database version
    used in print_db_version and upgrade_db_version in the db cli module
    """
    
    db_version_sql = s.sql.text(
        """
        SELECT * FROM augur_operations.augur_settings WHERE setting = 'augur_data_version'
        """
    )

    with engine.connect() as connection:
        result = int(connection.execute(db_version_sql).fetchone()[2])

    engine.dispose()
    return result