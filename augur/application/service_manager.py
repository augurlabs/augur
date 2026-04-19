import sys
import os
import subprocess
import sqlalchemy as s
from augur.application.logs import AugurLogger
from augur.application.db.session import DatabaseSession
from augur.application.db.lib import get_value
from augur.tasks.init.redis_connection import get_redis_connection
from urllib.parse import urlparse

logger = AugurLogger("augur_servicemanager").get_logger()


class AugurServiceManager:
    """ Provides a storage space for references to the various components of augur
    This enables them to all be properly shut down in the event a shutdown signal (SIGINT - AKA ctrl-c, or SIGTERM) is received 
    """
    def __init__(self, ctx, pidfile, disable_collection):
        self.ctx = ctx
        self.pidfile = pidfile
        self.disable_collection = disable_collection
        self.server = None
        self.processes = []
        self.celery_beat_process = None
        self.keypub = None
        self.shutting_down = False

    def shutdown_signal_handler(self, signum, frame):
        if self.shutting_down:
            return
        
        self.shutting_down = True
        logger.info(f"Received signal {signum}, shutting down gracefully")

        # Stop server
        if self.server:
            logger.info("Stopping server")
            self.server.terminate()
            try:
                self.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server did not terminate in time, killing")
                self.server.kill()

        # Stop celery workers
        logger.info("Stopping celery workers")
        for p in self.processes:
            if p and p.poll() is None:
                p.terminate()
        
        # Wait for workers to terminate
        for p in self.processes:
            if p:
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Worker {p.pid} did not terminate in time, killing")
                    p.kill()

        # Stop celery beat
        if self.celery_beat_process:
            logger.info("Stopping celery beat")
            self.celery_beat_process.terminate()
            try:
                self.celery_beat_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                logger.warning("Celery beat did not terminate in time, killing")
                self.celery_beat_process.kill()

        # Cleanup collection resources
        if not self.disable_collection:
            try:
                if self.keypub:
                    self.keypub.shutdown()
                cleanup_collection_status_and_rabbit(logger, self.ctx.obj.engine)
            except Exception as e:
                logger.debug(f"Error during collection cleanup: {e}")

        # Remove pidfile
        if os.path.exists(self.pidfile):
            try:
                os.unlink(self.pidfile)
            except OSError as e:
                logger.error(f"Could not remove pidfile {self.pidfile}: {e}")

        sys.exit(0)

def cleanup_collection_status_and_rabbit(logger, engine):
    # TODO: tech debt: this should probbaly be in a helper function but its so tightly coupled with other stuff
    clear_redis_caches()

    connection_string = get_value("RabbitMQ", "connection_string")

    with DatabaseSession(logger, engine=engine) as session:

        clean_collection_status(session)

    clear_rabbitmq_messages(connection_string)

def clear_redis_caches():
    """Clears the redis databases that celery and redis use."""

    logger.info("Flushing all redis databases this instance was using")
    celery_purge_command = "celery -A augur.tasks.init.celery_app.celery_app purge -f"
    subprocess.call(celery_purge_command.split(" "))

    redis_connection = get_redis_connection()
    redis_connection.flushdb()

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


def clear_rabbitmq_messages(connection_string):
    #virtual_host_string = connection_string.split("/")[-1]

    logger.info("Clearing all messages from celery queue in rabbitmq")
    from augur.tasks.init.celery_app import celery_app
    try:
        celery_app.control.purge()
    except Exception as e:
        logger.warning(f"Failed to purge celery queue (this is usually benign if the queue doesn't exist yet): {e}")

    clear_all_message_queues(connection_string)
    #rabbitmq_purge_command = f"sudo rabbitmqctl purge_queue celery -p {virtual_host_string}"
    #subprocess.call(rabbitmq_purge_command.split(" "))


def clear_all_message_queues(connection_string):
    queues = ['celery','secondary','scheduling','facade']

    virtual_host_string = connection_string.split("/")[-1]

    #Parse username and password with urllib
    parsed = urlparse(connection_string)

    for q in queues:
        # Use the hostname from the connection string instead of localhost
        # to ensure it works in both docker and non-docker environments
        hostname = parsed.hostname or "localhost"
        curl_cmd = f"curl -is -u {parsed.username}:{parsed.password} -XDELETE http://{hostname}:15672/api/queues/{virtual_host_string}/{q}"
        subprocess.call(curl_cmd.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
