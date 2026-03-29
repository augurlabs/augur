# Copyright 2016-2018 Brian Warner
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier:  Apache-2.0

# Git repo maintenance
#
# This script is responsible for cloning new repos and keeping existing repos up
# to date. It can be run as often as you want (and will detect when it's
# already running, so as not to spawn parallel processes), but once or twice per
# day should be more than sufficient. Each time it runs, it updates the repo
# and checks for any parents of HEAD that aren't already accounted for in the
# repos. It also rebuilds analysis data, checks any changed affiliations and
# aliases, and caches data for display.
import sys
import time
import os
import json
import logging
import random
import subprocess
from urllib.parse import urlparse
import sqlalchemy as s
from sqlalchemy.exc import OperationalError
from psycopg2.errors import DeadlockDetected

from augur.application.db.session import DatabaseSession
from augur.application.config import AugurConfig
from augur.application.db.lib import execute_sql
from logging import Logger

logger = logging.getLogger(__name__)

def get_database_args_from_env():

    db_str = os.getenv("AUGUR_DB")
    try:
        db_json_file_location = os.getcwd() + "/db.config.json"
    except FileNotFoundError:
        logger.error("\n\nPlease run augur commands in the root directory\n\n")
        sys.exit()

    db_json_exists = os.path.exists(db_json_file_location)

    if not db_str and not db_json_exists:

        logger.error("ERROR no way to get connection to the database. \n\t\t\t\t\t\t    There is no db.config.json and the AUGUR_DB environment variable is not set\n\t\t\t\t\t\t    Please run make install or set the AUGUR_DB environment then run make install")
        sys.exit()

    credentials = {}
    if db_str:
        parsedArgs = urlparse(db_str)

        credentials['db_user'] = parsedArgs.username#read_config('Database', 'user', 'AUGUR_DB_USER', 'augur')
        credentials['db_pass'] = parsedArgs.password#read_config('Database', 'password', 'AUGUR_DB_PASSWORD', 'augur')
        credentials['db_name'] = parsedArgs.path.replace('/','')#read_config('Database', 'name', 'AUGUR_DB_NAME', 'augur')
        credentials['db_host'] = parsedArgs.hostname#read_config('Database', 'host', 'AUGUR_DB_HOST', 'localhost')
        credentials['db_port'] = parsedArgs.port#read_config('Database', 'port', 'AUGUR_DB_PORT', 5432)
    else:
        with open("db.config.json", 'r') as f:
            db_config = json.load(f)

        credentials['db_user'] = db_config["user"]#read_config('Database', 'user', 'AUGUR_DB_USER', 'augur')
        credentials['db_pass'] = db_config["password"]#read_config('Database', 'password', 'AUGUR_DB_PASSWORD', 'augur')
        credentials['db_name'] = db_config["database_name"]#read_config('Database', 'name', 'AUGUR_DB_NAME', 'augur')
        credentials['db_host'] = db_config["host"]#read_config('Database', 'host', 'AUGUR_DB_HOST', 'localhost')
        credentials['db_port'] = db_config["port"]#read_config('Database', 'port', 'AUGUR_DB_PORT', 5432)
    #print(credentials)
    return credentials

class FacadeHelper():
    """ORM session used in facade tasks.

        This class adds the various attributes needed for legacy facade as well as a modified version of the legacy FacadeConfig class.
        This is mainly for compatibility with older functions from legacy facade.

    Attributes:
        repos_processed (int): git repositories processed
        limited_run (int): value that determines whether legacy facade is only doing a portion of its full run of commit analysis or not. By default all steps are run but if any options in particular are specified then only those are ran.
        delete_marked_repos (int): toggle that determines whether to delete git cloned git directories when they are marked for deletion
        pull_repos (int): toggles whether to update existing repos in the facade directory
        clone_repos (int): toggles whether to run 'git clone' on repos that haven't been cloned yet.
        check_updates (int): toggles whether to check if any repos are marked for update
        force_updates (int): force all repos to have 'git pull' run on them
        run_analysis (int): toggles analysis of repos in a limited run
        force_analysis (int): forces all repos to have their commits analyzed by legacy facade.
        nuke_stored_affiliations (int): toggles nuking facade affliations
        fix_affiliations (int): toggles filling empty affilations
        force_invalidate_caches (int): toggles whether to clear facade's backend caches
        rebuild_caches (int): toggles whether to rebuild unknown affiliation and web caches
        multithreaded (int): toggles whether to allow the facade task to execute subtasks in parallel
        create_xlsx_summary_files (int): toggles whether to create excel summary files
    """
    def __init__(self,logger: Logger):

        from augur.application.db import get_engine
        engine = get_engine()
        self.repos_processed = 0
        # super().__init__(logger=logger, engine=engine)

        self.logger = logger
        
        with DatabaseSession(logger, engine) as session:
            config = AugurConfig(logger, session)
        
            worker_options = config.get_section("Facade")

        self.limited_run = worker_options["limited_run"]
        self.delete_marked_repos = worker_options["delete_marked_repos"]
        self.pull_repos = worker_options["pull_repos"]
        #self.clone_repos = worker_options["clone_repos"]
        self.check_updates = worker_options["check_updates"]
        #self.force_updates = worker_options["force_updates"]
        self.run_analysis = worker_options["run_analysis"]
        #self.force_analysis = worker_options["force_analysis"]
        self.run_facade_contributors = worker_options["run_facade_contributors"]
        self.nuke_stored_affiliations = worker_options["nuke_stored_affiliations"]
        self.fix_affiliations = worker_options["fix_affiliations"]
        self.force_invalidate_caches = worker_options["force_invalidate_caches"]
        self.rebuild_caches = worker_options["rebuild_caches"]
        self.multithreaded = worker_options["multithreaded"]
        self.create_xlsx_summary_files = worker_options["create_xlsx_summary_files"]
        self.facade_contributor_full_recollect = worker_options["facade_contributor_full_recollect"]
        self.commit_messages = worker_options["commit_messages"]

        self.tool_source = "Facade"
        self.data_source = "Git Log"
        self.tool_version = "1.4.4"

        # Get the location of the directory where git repos are stored
        if 'repo_directory' in worker_options:
            self.repo_base_directory = worker_options['repo_directory']
        else:
            self.repo_base_directory = None

        # Determine if it's safe to start the script
        current_status = self.get_setting('utility_status')

        if len(self.repo_base_directory) == 0:
            self.cfg.log_activity('Error','No base directory. It is unsafe to continue.')
            raise Exception('Failed: No base directory')

    def get_setting(self,setting):
        #Get a setting from the db

        query = s.sql.text("""SELECT value FROM settings WHERE setting=:settingParam ORDER BY
            last_modified DESC LIMIT 1""").bindparams(settingParam=setting)
        
        result = execute_sql(query).fetchone()
        print(result)
        return result[0]
        

    def update_status(self, status):
        query = s.sql.text("""UPDATE settings SET value=:statusParam WHERE setting='utility_status'
            """).bindparams(statusParam=status)
        
        execute_sql(query)

    def log_activity(self, level, status):
        # Log an activity based upon urgency and user's preference.  If the log level is
        # "Debug", then just print it and don't save it in the database.
        log_options = ('Error','Quiet','Info','Verbose','Debug')
        logmsg = f"* {status}\n"
        if level == "Error":
            self.logger.error(logmsg)
        elif level == "Debug" or level == "Verbose":
            self.logger.debug(logmsg)
        else:
            self.logger.info(logmsg)

        #Return if only debug 
        if level == 'Debug':
            return
        
        #Else write to database
        query = s.sql.text("""INSERT INTO utility_log (level,status) VALUES (:levelParam,:statusParam)
            """).bindparams(levelParam=level,statusParam=status)

        try:
            execute_sql(query)
        except Exception as e:
            self.logger.error(f"Error encountered: {e}")
            raise e
    def update_repo_log(self,repos_id,status):
        self.logger.info(f"{status} {repos_id}")

        log_message = s.sql.text("""INSERT INTO repos_fetch_log (repos_id,status) 
            VALUES (:repo_id,:repo_status)""").bindparams(repo_id=repos_id,repo_status=status)
        
        try:
            execute_sql(log_message)
        except:
            pass

    def update_analysis_log(self, repos_id,status):

        # Log a repo's analysis status

        log_message = s.sql.text("""INSERT INTO analysis_log (repos_id,status)
            VALUES (:repo_id,:status)""").bindparams(repo_id=repos_id,status=status)

        execute_sql(log_message)

    def insert_or_update_data(self, query, **bind_args)-> None:
        """Provide deadlock detection for postgres updates, inserts, and deletions for facade.

        Returns:
            A page of data from the Github API at the specified url
        """

        attempts = 0
        sleep_time_list = [x for x in range(1,11)]
        deadlock_detected = False
        # if there is no data to return then it executes the insert the returns nothing

        while attempts < 10:
            try:
                if bind_args:
                    #self.cfg.cursor.execute(query, params)
                    execute_sql(query.bindparams(**bind_args))
                else:
                    execute_sql(query)
                break
            except OperationalError as e:
                # print(str(e).split("Process")[1].split(";")[0])
                if isinstance(e.orig, DeadlockDetected):
                    deadlock_detected = True
                    sleep_time = random.choice(sleep_time_list)
                    self.logger.debug(f"Deadlock detected on query {query}...trying again in {round(sleep_time)} seconds")
                    time.sleep(sleep_time)

                    attempts += 1
                    continue
                else:
                    raise OperationalError(f"An OperationalError other than DeadlockDetected occurred: {e}") 

        else:
            self.logger.error(f"Unable to insert data in 10 attempts")
            return

        if deadlock_detected is True:
            self.logger.error(f"Made it through even though Deadlock was detected")
                    
            return
    def inc_repos_processed(self):
        self.repos_processed += 1

    def run_git_command(self, cmd: str, timeout: int, capture_output: bool = False, operation_description: str = None) -> tuple:
        """
        Execute a git command with timeout handling.

        This method provides a unified interface for running git commands with
        consistent timeout handling and error logging across all facade operations.

        Args:
            cmd: The git command to execute
            timeout: Timeout in seconds
            capture_output: If True, capture stdout/stderr; if False, discard them
            operation_description: Human-readable description for error logging
                                 (defaults to cmd if not provided)

        Returns:
            tuple: (return_code, stdout_content)
                   return_code is -1 on timeout
                   stdout_content is empty string if capture_output=False
        """
        if operation_description is None:
            operation_description = cmd

        try:
            # Common options for all subprocess.run calls
            run_options = {
                'shell': True,
                'timeout': timeout,
                'check': False
            }

            # Add capture_output-specific options
            if capture_output:
                run_options['capture_output'] = True
                run_options['encoding'] = 'utf-8'
                run_options['errors'] = 'replace'
            else:
                run_options['stdout'] = subprocess.DEVNULL
                run_options['stderr'] = subprocess.DEVNULL

            result = subprocess.run(cmd, **run_options)

            # Return appropriate output based on capture_output flag
            return result.returncode, (result.stdout.strip() if capture_output else '')
        except subprocess.TimeoutExpired:
            self.log_activity('Error', f'Git operation timed out: {operation_description}')
            return -1, ''
