#!/usr/bin/env python3

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
import html.parser
import subprocess
import os
import pathlib
import sqlalchemy as s
from .utilitymethods import update_repo_log, get_absolute_repo_path
from sqlalchemy.orm.exc import NoResultFound
from augur.application.db.models.augur_data import *
from augur.application.db.models.augur_operations import CollectionStatus
from augur.application.db.util import execute_session_query, convert_orm_list_to_dict_list
from augur.application.db.lib import execute_sql, get_repo_by_repo_git

class GitCloneError(Exception):
    pass

def git_repo_initialize(facade_helper, session, repo_git):

    # Select any new git repos so we can set up their locations and git clone

    facade_helper.update_status('Fetching non-cloned repos')
    facade_helper.log_activity('Info', 'Fetching non-cloned repos')

    # Get data as a list of dicts
    # new_repos = fetchall_data_from_sql_text(query)#list(cfg.cursor)
    row = Repo.get_by_repo_git(session, repo_git)

    if row:

        facade_helper.log_activity(
            'Info', f"Fetching repo with repo id: {row.repo_id}")

        update_repo_log(logger, facade_helper, row.repo_id, 'Cloning')

        git = html.unescape(row.repo_git)

        # Strip protocol from remote URL, set a unique path on the filesystem
        if git.find('://', 0) > 0:
            platform_org_git_url_section = git[git.find(
                '://', 0)+3:][:git[git.find('://', 0)+3:].rfind('/', 0)+1]
            facade_helper.log_activity(
                'Info', f"Repo Relative Path from facade05, from for row in new_repos, line 79: {platform_org_git_url_section}")
            facade_helper.log_activity('Info', f"The git path used : {git}")

        else:
            platform_org_git_url_section = git[:git.rfind('/', 0)+1]
            facade_helper.log_activity(
                'Info', f"Repo Relative Path from facade05, line 80, reset at 86: {platform_org_git_url_section}")

        # Get the name of repo
        repo_name = git[git.rfind('/', 0)+1:]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:repo_name.find('.git', 0)]
            facade_helper.log_activity(
                'Info', f"Repo Name from facade05, line 93: {repo_name}")
        
        path_identifier = f"{platform_org_git_url_section}{repo_name}".replace('/','-')

        # Get the full path to the directory where we'll clone the repo
        repo_path = (
            f"{facade_helper.repo_base_directory}{row.repo_id}-{path_identifier}")
        facade_helper.log_activity(
            'Info', f"Repo Path from facade05, line 86: {repo_path}")

        

        # query = s.sql.text("""SELECT NULL FROM repo WHERE CONCAT(repo_group_id,'/',repo_path,repo_name) = :repo_group_id
        #    """).bindparams(repo_group_id=f"{row.repo_group_id}/{platform_org_git_url_section}{repo_name}")
        #
        # result = fetchall_data_from_sql_text(query)

        query = s.sql.text("""UPDATE repo SET repo_path=:pathParam, 
            repo_name=:nameParam WHERE repo_id=:idParam
            """).bindparams(pathParam=path_identifier, nameParam=repo_name, idParam=row.repo_id)

        execute_sql(query)
        # Check if there will be a storage path collision
        # If there is a collision, throw an error so that it updates the existing repo instead of trying
        # to reclone.
        if os.path.isdir(repo_path):  # len(result):

            facade_helper.log_activity(
                'Verbose', f"Identical repo detected, storing {git} in {repo_name}")
            logger.warning(
                f"Identical repo found in facade directory! Repo git: {git}")
            statusQuery = session.query(CollectionStatus).filter(
                CollectionStatus.repo_id == row.repo_id)
            collectionRecord = execute_session_query(statusQuery, 'one')
            collectionRecord.facade_status = 'Update'
            collectionRecord.facade_task_id = None
            session.commit()

            #Make sure repo in repo table reflects found path.
            query = s.sql.text("""UPDATE repo SET repo_path=:pathParam, 
            repo_name=:nameParam WHERE repo_id=:idParam
            """).bindparams(pathParam=path_identifier, nameParam=repo_name, idParam=row.repo_id)

            execute_sql(query)
            return

        # Create the prerequisite directories
        try:
            pathlib.Path(repo_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print("COULD NOT CREATE REPO DIRECTORY")

            update_repo_log(logger, facade_helper, row.repo_id, 'Failed (mkdir)')
            facade_helper.update_status(f"Failed (mkdir {repo_path})")
            facade_helper.log_activity(
                'Error', f"Could not create repo directory: {repo_path}")

            raise e

        update_repo_log(logger, facade_helper, row.repo_id, 'New (cloning)')

        #Make sure newly cloned repo path is recorded in repo table
        query = s.sql.text("""UPDATE repo SET repo_path=:pathParam, 
            repo_name=:nameParam WHERE repo_id=:idParam
            """).bindparams(pathParam=path_identifier, nameParam=repo_name, idParam=row.repo_id)

        execute_sql(query)

        facade_helper.log_activity('Verbose', f"Cloning: {git}")

        cmd = f"git -C {repo_path} clone '{git}' {repo_name}"
        return_code, _ = facade_helper.run_git_command(
            cmd,
            timeout=7200,  # 2 hours for large repos
            capture_output=False,
            operation_description=f'git clone {git}'
        )

        if (return_code == 0):
            # If cloning succeeded, repo is ready for analysis
            # Mark the entire project for an update, so that under normal
            # circumstances caches are rebuilt only once per waiting period.
            update_repo_log(logger, facade_helper, row.repo_id, 'Up-to-date')
            facade_helper.log_activity('Info', f"Cloned {git}")

        else:
            # If cloning failed, log it and set the status back to new
            update_repo_log(logger, facade_helper, row.repo_id, f"Failed ({return_code})")

            facade_helper.log_activity('Error', f"Could not clone {git}")

            raise GitCloneError(f"Could not clone {git}")

    facade_helper.log_activity('Info', f"Fetching new repos (complete)")


# Deprecated functionality. No longer used
# Should be re-purposed in start_tasks when tasks are being scheduled
def check_for_repo_updates(session, repo_git):

    # Check the last time a repo was updated and if it has been longer than the
    # update_frequency, mark its project for updating during the next analysis.
    raise NotImplementedError(
        "This functionality is deprecated and won't work with present facade versions")
    session.update_status('Checking if any repos need to update')
    session.log_activity('Info', 'Checking repos to update')

    update_frequency = session.get_setting('update_frequency')

    get_initialized_repos = s.sql.text("""SELECT repo_id FROM repo WHERE repo_status NOT LIKE 'New%' 
        AND repo_status != 'Delete' 
        AND repo_status != 'Analyze' AND repo_status != 'Empty'
        AND repo_git = :value""").bindparams(value=repo_git)

    # repos = fetchall_data_from_sql_text(get_initialized_repos)#list(cfg.cursor)
    repo = execute_sql(get_initialized_repos).fetchone()

    if repo:

        # Figure out which repos have been updated within the waiting period

        get_last_update = s.sql.text("""SELECT NULL FROM repos_fetch_log WHERE
            repos_id=:repo_id AND status='Up-to-date' AND
            date >= CURRENT_TIMESTAMP(6) - INTERVAL :update_freq HOUR """).bindparams(repo_id=repo['repo_id'], update_freq=update_frequency[0])

        result = fetchall_data_from_sql_text(get_last_update)
        # If the repo has not been updated within the waiting period, mark it.
        # Also mark any other repos in the project, so we only recache the
        # project once per waiting period.

        if len(result) == 0:
            mark_repo = s.sql.text("""UPDATE repo
                SET repo_status='Update' 
                        WHERE repo.ctid IN (
                SELECT repo.ctid FROM repo JOIN repo_groups ON repo.repo_group_id=repo_groups.repo_group_id
                AND repo.repo_id=:repo_id 
                AND repo.repo_status != 'Empty')""").bindparams(repo_id=repo['repo_id'])

            # ("UPDATE repos r JOIN projects p ON p.id = r.projects_id "
            #     "SET status='Update' WHERE "
            #     "r.id=%s and r.status != 'Empty'")

            execute_sql(mark_repo)

    # Mark the entire project for an update, so that under normal
    # circumstances caches are rebuilt only once per waiting period.

    update_project_status = s.sql.text("""UPDATE repo
        SET repo_status='Update' 
                WHERE repo.ctid IN (
        SELECT repo.ctid FROM repo LEFT JOIN repo a ON repo.repo_group_id=a.repo_group_id
        AND repo.repo_status='Update'
        AND repo.repo_status != 'Analyze' 
        AND repo.repo_status != 'Empty')
        AND repo.repo_git = :value""").bindparams(value=repo_git)

    # ("UPDATE repos r LEFT JOIN repos s ON r.projects_id=s.projects_id "
    #     "SET r.status='Update' WHERE s.status='Update' AND "
    #     "r.status != 'Analyze' AND r.status != 'Empty'")

    session.insert_or_update_data(update_project_status)

    session.log_activity('Info', 'Checking repos to update (complete)')

# Deprecated. No longer used.


def force_repo_updates(session, repo_git):
    raise NotImplementedError(
        "This functionality is deprecated and won't work with present facade versions")

# Set the status of all non-new repos to "Update".

    session.update_status('Forcing all non-new repos to update')
    session.log_activity('Info', 'Forcing repos to update')

    get_repo_ids = s.sql.text("""UPDATE repo SET repo_status='Update' WHERE repo_status
        NOT LIKE 'New%' AND repo_status!='Delete' AND repo_status !='Empty'
        AND repo_git=:value""").bindparams(value=repo_git)
    execute_sql(get_repo_ids)

    session.log_activity('Info', 'Forcing repos to update (complete)')

# Deprecated. No longer used.


def force_repo_analysis(session, repo_git):
    raise NotImplementedError(
        "This functionality is deprecated and won't work with present facade versions")

    session.update_status('Forcing all non-new repos to be analyzed')
    session.log_activity('Info', 'Forcing repos to be analyzed')

    set_to_analyze = s.sql.text("""UPDATE repo SET repo_status='Analyze' WHERE repo_status
        NOT LIKE 'New%' AND repo_status!='Delete' AND repo_status != 'Empty'
        AND repo_git=:repo_git_ident""").bindparams(repo_git_ident=repo_git)

    execute_sql(set_to_analyze)

    session.log_activity('Info', 'Forcing repos to be analyzed (complete)')


def git_repo_updates(facade_helper, repo_git):

    # Update existing repos

    facade_helper.update_status('Updating repos')
    facade_helper.log_activity('Info', 'Updating existing repos')

    # query = s.sql.text("""SELECT repo_id,repo_group_id,repo_git,repo_name,repo_path FROM repo WHERE
    #    repo_status='Update'""")

    try:
        repo = get_repo_by_repo_git(repo_git)
    except NoResultFound:
        raise Exception(
            f"Repo git: {repo_git} does not exist or the status is not 'Update'")


    if repo.repo_path is None or repo.repo_name is None:
        raise Exception(
            f"The repo path or repo name is NULL for repo_id: {repo.repo_id}")

    facade_helper.log_activity(
        'Verbose', f"Attempting to update {repo.repo_git}")  # ['git'])
    update_repo_log(logger, facade_helper, repo.repo_id, 'Updating')  # ['id'],'Updating')

    attempt = 0

    # Try two times. If it fails the first time, reset and clean the git repo,
    # as somebody may have done a rebase. No work is being done in the local
    # repo, so there shouldn't be legit local changes to worry about.

    # default_branch = ''

    absolute_path = get_absolute_repo_path(
        facade_helper.repo_base_directory, repo.repo_id, repo.repo_path, repo.repo_name)

    while attempt < 2:

        try:

            firstpull = (f"git -C {absolute_path} pull")

            return_code_remote, _ = facade_helper.run_git_command(
                firstpull,
                timeout=600,  # 10 minutes for git pull
                capture_output=False,
                operation_description=f'git pull {repo.repo_git}'
            )

            facade_helper.log_activity('Verbose', 'Got to here. 1.')

            if return_code_remote == 0:

                #                    logremotedefault = ("git -C %s%s/%s%s remote set-head origin -a"
                #                        % (session.repo_base_directory,row[1],row[4],row[3]))

                #                    return_code_remote_default = subprocess.Popen([logremotedefault],stdout=subprocess.PIPE,shell=True).wait()

                #                    session.log_activity('Verbose', f'remote default is {logremotedefault}.')

                getremotedefault = (
                    f"git -C {absolute_path} remote show origin | sed -n '/HEAD branch/s/.*: //p'")

                return_code_remote, remotedefault = facade_helper.run_git_command(
                    getremotedefault,
                    timeout=60,  # 1 minute for remote query
                    capture_output=True,
                    operation_description='get remote default branch'
                )

                facade_helper.log_activity(
                    'Verbose', f'remote default getting checked out is: {remotedefault}.')

                getremotedefault = (
                    f"git -C {absolute_path} checkout {remotedefault}")

                facade_helper.log_activity(
                    'Verbose', f"get remote default command is: \n \n {getremotedefault} \n \n ")

                return_code_remote_default_again, _ = facade_helper.run_git_command(
                    getremotedefault,
                    timeout=600,  # 10 minutes for git checkout
                    capture_output=False,
                    operation_description=f'git checkout {remotedefault}'
                )

                if return_code_remote_default_again == 0:
                    facade_helper.log_activity('Verbose', "local checkout worked.")
                    cmd = (f"git -C {absolute_path} pull")

                    return_code, _ = facade_helper.run_git_command(
                        cmd,
                        timeout=600,  # 10 minutes for git pull
                        capture_output=False,
                        operation_description=f'git pull {repo.repo_git}'
                    )

        except Exception as e:
            facade_helper.log_activity(
                'Verbose', f'Error code on branch change is {e}.')
            pass

        finally:

            cmd = (f"git -C {absolute_path} pull")

            return_code, _ = facade_helper.run_git_command(
                cmd,
                timeout=600,  # 10 minutes for git pull
                capture_output=False,
                operation_description=f'git pull {repo.repo_git}'
            )

        # If the attempt succeeded, then don't try any further fixes. If
        # the attempt to fix things failed, give up and try next time.
        if return_code == 0 or attempt == 2:
            break

        elif attempt == 0:
            facade_helper.log_activity(
                'Verbose', f"git pull failed, attempting reset and clean for {repo.repo_git}")

#                remotedefault = 'main'

#                logremotedefault = ("git -C %s%s/%s%s remote set-head origin -a"
#                    % (session.repo_base_directory,row[1],row[4],row[3]))

#                return_code_remote = subprocess.Popen([logremotedefault],stdout=subprocess.PIPE,shell=True).wait()

#                session.log_activity('Verbose', f'remote default is {logremotedefault}.')

            getremotedefault = (
                f"git -C {absolute_path} remote show origin | sed -n '/HEAD branch/s/.*: //p'")

            return_code_remote, remotedefault = facade_helper.run_git_command(
                getremotedefault,
                timeout=60,  # 1 minute for remote query
                capture_output=True,
                operation_description='get remote default branch'
            )

            try:

                getremotedefault = (
                    f"git -C {absolute_path} checkout {remotedefault}")

                return_code_remote_default, _ = facade_helper.run_git_command(
                    getremotedefault,
                    timeout=600,  # 10 minutes for git checkout
                    capture_output=False,
                    operation_description=f'git checkout {remotedefault}'
                )

                facade_helper.log_activity(
                    'Verbose', f'get remote default result (return code): {return_code_remote_default}')

                getcurrentbranch = (f"git -C {absolute_path} branch")

                return_code_local, localdefault = facade_helper.run_git_command(
                    getcurrentbranch,
                    timeout=60,  # 1 minute for branch query
                    capture_output=True,
                    operation_description='get current branch'
                )

                facade_helper.log_activity(
                    'Verbose', f'remote default is: {remotedefault}, and localdefault is {localdefault}.')

                cmd_checkout_default = (
                    f"git -C {absolute_path} checkout {remotedefault}")

                cmd_checkout_default_wait, _ = facade_helper.run_git_command(
                    cmd_checkout_default,
                    timeout=600,  # 10 minutes for git checkout
                    capture_output=False,
                    operation_description=f'git checkout {remotedefault}'
                )

                cmdpull2 = (f"git -C {absolute_path} pull")

                cmd_reset = (f"git -C {absolute_path} reset --hard origin/{remotedefault}")

                cmd_reset_wait, _ = facade_helper.run_git_command(
                    cmd_reset,
                    timeout=300,  # 5 minutes for git reset
                    capture_output=False,
                    operation_description=f'git reset --hard origin/{remotedefault}'
                )

                cmd_clean = (f"git -C {absolute_path} clean -df")

                return_code_clean, _ = facade_helper.run_git_command(
                    cmd_clean,
                    timeout=300,  # 5 minutes for git clean
                    capture_output=False,
                    operation_description='git clean -df'
                )

            except Exception as e:

                facade_helper.log_activity('Verbose', f'Second pass failed: {e}.')
                pass

        cmdpull2 = (f"git -C {absolute_path} pull")

        print(cmdpull2)
        return_code, _ = facade_helper.run_git_command(
            cmdpull2,
            timeout=600,  # 10 minutes for git pull
            capture_output=False,
            operation_description=f'git pull {repo.repo_git}'
        )

        attempt += 1

        # default_branch = ''

    if return_code == 0:

        update_repo_log(logger, facade_helper, repo.repo_id, 'Up-to-date')
        facade_helper.log_activity('Verbose', f"Updated {repo.repo_git}")

    else:

        update_repo_log(logger, facade_helper, repo.repo_id, f"Failed ({return_code})")
        facade_helper.log_activity('Error', f"Could not update {repo.repo_git}")

    facade_helper.log_activity('Info', 'Updating existing repos (complete)')
