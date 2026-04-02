#SPDX-License-Identifier: MIT

import logging
import datetime
from celery import group, chain

from subprocess import check_output
from augur.application.db.lib import get_session, get_repo_by_repo_git, get_repo_by_repo_id, remove_working_commits_by_repo_id_and_hashes, get_working_commits_by_repo_id, facade_bulk_insert_commits, bulk_insert_dicts, get_missing_commit_message_hashes

from augur.tasks.git.util.facade_worker.facade_worker.utilitymethods import trim_commits
from augur.tasks.git.util.facade_worker.facade_worker.utilitymethods import get_absolute_repo_path, get_parent_commits_set, get_existing_commits_set
from augur.tasks.git.util.facade_worker.facade_worker.analyzecommit import analyze_commit
from augur.tasks.git.util.facade_worker.facade_worker.utilitymethods import get_repo_commit_count, update_facade_scheduling_fields

from augur.tasks.github.facade_github.tasks import *
from augur.tasks.git.util.facade_worker.facade_worker.config import FacadeHelper
from augur.tasks.util.collection_state import CollectionState
from augur.tasks.util.collection_util import get_collection_status_repo_git_from_filter
from augur.tasks.git.util.facade_worker.facade_worker.repofetch import GitCloneError, git_repo_initialize, git_repo_updates



from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurFacadeRepoCollectionTask


from augur.application.db.models import Repo, CollectionStatus, CommitMessage

from augur.tasks.git.dependency_tasks.tasks import process_dependency_metrics
from augur.tasks.git.dependency_libyear_tasks.tasks import process_libyear_dependency_metrics
from augur.tasks.git.scc_value_tasks.tasks import process_scc_value_metrics

from augur.tasks.github.util.github_task_session import *

def filter_null_repo_id(records, logger, context=""):
    """Remove and log records with null/None repo_id."""
    filtered = []
    for rec in records:
        if rec.get("repo_id") is None:
            logger.error(
                f"[{context}] Null repo_id in commit record: {json.dumps(rec, default=str)}"
            )
        else:
            filtered.append(rec)
    return filtered

#define an error callback for chains in facade collection so facade doesn't make the program crash
#if it does.
@celery.task
def facade_error_handler(request,exc,traceback):

    logger = logging.getLogger(facade_error_handler.__name__)

    logger.error(f"Task {request.id} raised exception: {exc}! \n {traceback}")

    print(f"chain: {request.chain}")
    #Make sure any further execution of tasks dependent on this one stops.
    try:
        #Replace the tasks queued ahead of this one in a chain with None.
        request.chain = None
    except AttributeError:
        pass #Task is not part of a chain. Normal so don't log.
    except Exception as e:
        logger.error(f"Could not mutate request chain! \n Error: {e}")


#Predefine facade collection with tasks
@celery.task(base=AugurFacadeRepoCollectionTask)
def facade_analysis_init_facade_task(repo_git):

    logger = logging.getLogger(facade_analysis_init_facade_task.__name__)
    facade_helper = FacadeHelper(logger)

    facade_helper.update_status('Running analysis')
    facade_helper.log_activity('Info',f"Beginning analysis.")


@celery.task(base=AugurFacadeRepoCollectionTask)
def trim_commits_facade_task(repo_git):

    logger = logging.getLogger(trim_commits_facade_task.__name__)

    facade_helper = FacadeHelper(logger)

    repo = get_repo_by_repo_git(repo_git)

    repo_id = repo.repo_id

    facade_helper.inc_repos_processed()
    facade_helper.update_analysis_log(repo_id,"Beginning analysis.")
    # First we check to see if the previous analysis didn't complete

    working_commits = get_working_commits_by_repo_id(repo_id)

    # If there's a commit still there, the previous run was interrupted and
    # the commit data may be incomplete. It should be trimmed, just in case.
    commits_to_trim = [commit['working_commit'] for commit in working_commits]
    
    trim_commits(facade_helper,repo_id,commits_to_trim)
    # Start the main analysis

    facade_helper.update_analysis_log(repo_id,'Collecting data')
    logger.info(f"Got past repo {repo_id}")

@celery.task(base=AugurFacadeRepoCollectionTask)
def trim_commits_post_analysis_facade_task(repo_git):

    logger = logging.getLogger(trim_commits_post_analysis_facade_task.__name__)
    
    facade_helper = FacadeHelper(logger)

    repo = repo = get_repo_by_repo_git(repo_git)
    repo_id = repo.repo_id

    logger.info(f"Generating sequence for repo {repo_id}")

    repo = get_repo_by_repo_git(repo_git)

    #Get the huge list of commits to process.
    absolute_path = get_absolute_repo_path(facade_helper.repo_base_directory, repo.repo_id, repo.repo_path,repo.repo_name)
    repo_loc = (f"{absolute_path}/.git")
    # Grab the parents of HEAD

    parent_commits = get_parent_commits_set(repo_loc, facade_helper)

    # Grab the existing commits from the database
    existing_commits = get_existing_commits_set(repo_id)

    # Find missing commits and add them

    missing_commits = parent_commits - existing_commits

    facade_helper.log_activity('Debug',f"Commits missing from repo {repo_id}: {len(missing_commits)}")
    
    # Find commits which are out of the analysis range

    trimmed_commits = existing_commits - parent_commits

    facade_helper.update_analysis_log(repo_id,'Data collection complete')

    facade_helper.update_analysis_log(repo_id,'Beginning to trim commits')

    facade_helper.log_activity('Debug',f"Commits to be trimmed from repo {repo_id}: {len(trimmed_commits)}")

    #for commit in trimmed_commits:
    trim_commits(facade_helper,repo_id,trimmed_commits)
    
    facade_helper.update_analysis_log(repo_id,'Commit trimming complete')

    facade_helper.update_analysis_log(repo_id,'Complete')
    


@celery.task
def facade_analysis_end_facade_task():

    logger = logging.getLogger(facade_analysis_end_facade_task.__name__)
    facade_helper = FacadeHelper(logger)
    facade_helper.log_activity('Info','Running analysis (complete)')



@celery.task
def facade_start_contrib_analysis_task():

    logger = logging.getLogger(facade_start_contrib_analysis_task.__name__)
    facade_helper = FacadeHelper(logger)
    facade_helper.update_status('Updating Contributors')
    facade_helper.log_activity('Info', 'Updating Contributors with commits')

@celery.task(base=AugurFacadeRepoCollectionTask)
def facade_fetch_missing_commit_messages(repo_git):
    logger = logging.getLogger(facade_fetch_missing_commit_messages.__name__)
    facade_helper = FacadeHelper(logger)

    repo = get_repo_by_repo_git(repo_git)
    
    logger.debug(f"Fetching missing commit message records for repo {repo_git}")

    missing_message_hashes = get_missing_commit_message_hashes(repo.repo_id)

    to_insert = []

    for hash in missing_message_hashes:
        #Get the huge list of commits to process.
        logger.debug(f"The hash object is: {hash}. It has a type of: {type(hash)}")

        try:
            escaped_hash = hash['cmt_commit_hash']
        except (TypeError, IndexError):
            escaped_hash = hash
            
        absolute_path = get_absolute_repo_path(facade_helper.repo_base_directory, repo.repo_id, repo.repo_path, repo.repo_name)
        repo_loc = (f"{absolute_path}/.git")

        try: 
            commit_message = check_output(
                f"git --git-dir {repo_loc} log --format=%B -n 1 {escaped_hash}".split()
                #f"git --git-dir {repo_loc} log --format=%B -n 1 {hash}".split()
            ).decode('utf-8').strip()

            msg_record = {
                'repo_id' : repo.repo_id,
                'cmt_msg' : commit_message,
                #'cmt_hash' : hash,
                'cmt_hash': escaped_hash if isinstance(escaped_hash, str) else escaped_hash['cmt_commit_hash'],
                'tool_source' : 'Facade',
                'tool_version' : '0.78?',
                'data_source' : 'git',
                'data_collection_date' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if len(to_insert) >= 1000:
                bulk_insert_dicts(logger,to_insert, CommitMessage, ["repo_id","cmt_hash"])
                to_insert.clear()
            
            to_insert.append(msg_record)
        except Exception as e: 
            logger.info(f'The exception is : {e}.')

    if to_insert:
        bulk_insert_dicts(logger, to_insert, CommitMessage, ["repo_id","cmt_hash"])


#enable celery multithreading
@celery.task(base=AugurFacadeRepoCollectionTask)
def analyze_commits_in_parallel(repo_git, multithreaded: bool)-> None:
    """Take a large list of commit data to analyze and store in the database. Meant to be run in parallel with other instances of this task.
    """

    #create new session for celery thread.
    logger = logging.getLogger(analyze_commits_in_parallel.__name__)
    facade_helper = FacadeHelper(logger)

    repo = get_repo_by_repo_git(repo_git)
    repo_id = repo.repo_id

    logger.info(f"Generating sequence for repo {repo_id}")
    
    repo = get_repo_by_repo_id(repo_id)

    #Get the huge list of commits to process.
    absolute_path = get_absolute_repo_path(facade_helper.repo_base_directory, repo.repo_id, repo.repo_path, repo.repo_name)
    repo_loc = (f"{absolute_path}/.git")
    # Grab the parents of HEAD

    parent_commits = get_parent_commits_set(repo_loc, facade_helper)

    # Grab the existing commits from the database
    existing_commits = get_existing_commits_set(repo_id)

    # Find missing commits and add them
    missing_commits = parent_commits - existing_commits

    facade_helper.log_activity('Debug',f"Commits missing from repo {repo_id}: {len(missing_commits)}")

    
    if not missing_commits or repo_id is None:
        #session.log_activity('Info','Type of missing_commits: %s' % type(missing_commits))
        return
    
    queue = list(missing_commits)

    logger.info(f"Got to analysis!")
    absolute_path = get_absolute_repo_path(facade_helper.repo_base_directory, repo.repo_id, repo.repo_path,repo.repo_name)
    repo_loc = (f"{absolute_path}/.git")

    pendingCommitRecordsToInsert = []
    pendingCommitMessageRecordsToInsert = []

    """
    for count, commitTuple in enumerate(queue):
        quarterQueue = int(len(queue) / 4)

        if quarterQueue == 0:
            quarterQueue = 1 # prevent division by zero with integer math

        #Log progress when another quarter of the queue has been processed
        if (count + 1) % quarterQueue == 0:
            logger.info(f"Progress through current analysis queue is {(count / len(queue)) * 100}%")

        #logger.info(f"Got to analysis!")
        commitRecords, commit_msg = analyze_commit(logger, repo_id, repo_loc, commitTuple)
        #logger.debug(commitRecord)
        if commitRecords:
            pendingCommitRecordsToInsert.extend(commitRecords)
            if len(pendingCommitRecordsToInsert) >= 1000:
                facade_bulk_insert_commits(logger,pendingCommitRecordsToInsert)
                pendingCommitRecordsToInsert = []
        
        if commit_msg:
            pendingCommitMessageRecordsToInsert.append(commit_msg)
        
        if len(pendingCommitMessageRecordsToInsert) >= 1000:
            bulk_insert_dicts(logger,pendingCommitMessageRecordsToInsert, CommitMessage, ["repo_id","cmt_hash"])
    
    bulk_insert_dicts(logger,pendingCommitMessageRecordsToInsert, CommitMessage, ["repo_id","cmt_hash"])
    facade_bulk_insert_commits(logger,pendingCommitRecordsToInsert)
    """
    for count, commitTuple in enumerate(queue):
        quarterQueue = int(len(queue) / 4) or 1

        if (count + 1) % quarterQueue == 0:
            logger.info(f"Progress through current analysis queue is {(count / len(queue)) * 100}%")

        commitRecords, commit_msg = analyze_commit(logger, repo_id, repo_loc, commitTuple)
        if commitRecords:
            pendingCommitRecordsToInsert.extend(commitRecords)
            if len(pendingCommitRecordsToInsert) >= 1000:
                # FILTER AND LOG NULL REPO_IDs HERE
                pendingCommitRecordsToInsert = filter_null_repo_id(
                    pendingCommitRecordsToInsert, logger, context="batch insert"
                )
                if pendingCommitRecordsToInsert:
                    facade_bulk_insert_commits(logger, pendingCommitRecordsToInsert)
                pendingCommitRecordsToInsert.clear()

        if commit_msg and facade_helper.commit_messages:
            pendingCommitMessageRecordsToInsert.append(commit_msg)

        if len(pendingCommitMessageRecordsToInsert) >= 1000:
            bulk_insert_dicts(logger, pendingCommitMessageRecordsToInsert, CommitMessage, ["repo_id", "cmt_hash"])
            pendingCommitMessageRecordsToInsert.clear()

    # FINAL MESSAGE INSERT
    bulk_insert_dicts(logger, pendingCommitMessageRecordsToInsert, CommitMessage, ["repo_id", "cmt_hash"])

    # FINAL COMMIT INSERT, FILTER & LOG NULLS
    pendingCommitRecordsToInsert = filter_null_repo_id(
        pendingCommitRecordsToInsert, logger, context="final insert"
    )
    if pendingCommitRecordsToInsert:
        facade_bulk_insert_commits(logger, pendingCommitRecordsToInsert)
        
    # Remove the working commit.
    remove_working_commits_by_repo_id_and_hashes(repo_id, queue)

    logger.info("Analysis complete")
    return

# retry this task indefinitely every 5 minutes if it errors. Since the only way it gets scheduled is by itself, so if it stops running no more clones will happen till the instance is restarted
@celery.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=300, retry_jitter=True, max_retries=None)
def clone_repos():

    logger = logging.getLogger(clone_repos.__name__)
    
    is_pending = CollectionStatus.facade_status == CollectionState.PENDING.value

    facade_helper = FacadeHelper(logger)

    with get_session() as session:

        # process up to 1000 repos at a time
        repo_git_identifiers = get_collection_status_repo_git_from_filter(session, is_pending, 999999)
        for repo_git in repo_git_identifiers:
            # set repo to intializing
            repo = Repo.get_by_repo_git(session, repo_git)
            repoStatus = repo.collection_status[0]
            setattr(repoStatus,"facade_status", CollectionState.INITIALIZING.value)
            session.commit()

            # clone repo
            try:
                git_repo_initialize(facade_helper, session, repo_git)
                session.commit()

                # get the commit count (still used for facade status checks)
                commit_count = get_repo_commit_count(logger, facade_helper, repo_git)
                
                update_facade_scheduling_fields(repo_git, commit_count)

                # set repo to update
                setattr(repoStatus,"facade_status", CollectionState.UPDATE.value)
                session.commit()
            except GitCloneError:
                # continue to next repo, since we can't calculate 
                # commit_count or weight without the repo cloned
                setattr(repoStatus,"facade_status", CollectionState.FAILED_CLONE.value)
                session.commit()
            except Exception as e:
                logger.error(f"Ran into unexpected issue when cloning repositories \n Error: {e}")
                # set repo to error
                setattr(repoStatus,"facade_status", CollectionState.ERROR.value)
                session.commit()

            clone_repos.si().apply_async(countdown=60*5)


#@celery.task(bind=True)
#def check_for_repo_updates_facade_task(self, repo_git):
#
#    engine = self.app.engine
#
#    logger = logging.getLogger(check_for_repo_updates_facade_task.__name__)
#
#    facade_helper = FacadeHelper(logger)
#        check_for_repo_updates(session, repo_git)


@celery.task(base=AugurFacadeRepoCollectionTask)
def git_repo_updates_facade_task(repo_git):

    logger = logging.getLogger(git_repo_updates_facade_task.__name__)

    facade_helper = FacadeHelper(logger)

    git_repo_updates(facade_helper, repo_git)


def generate_analysis_sequence(logger,repo_git, facade_helper):
    """Run the analysis by looping over all active repos. For each repo, we retrieve
    the list of commits which lead to HEAD. If any are missing from the database,
    they are filled in. Then we check to see if any commits in the database are
    not in the list of parents, and prune them out.

    We also keep track of the last commit to be processed, so that if the analysis
    is interrupted (possibly leading to partial data in the database for the
    commit being analyzed at the time) we can recover.
    """

    analysis_sequence = []

    #repo_ids = [repo['repo_id'] for repo in repos]

    #repo_id = repo_ids.pop(0)

    analysis_sequence.append(facade_analysis_init_facade_task.si(repo_git))

    analysis_sequence.append(trim_commits_facade_task.si(repo_git))

    analysis_sequence.append(analyze_commits_in_parallel.si(repo_git,True))

    analysis_sequence.append(trim_commits_post_analysis_facade_task.si(repo_git))

    if facade_helper.commit_messages:
        analysis_sequence.append(facade_fetch_missing_commit_messages.si(repo_git))
    
    analysis_sequence.append(facade_analysis_end_facade_task.si())
    
    logger.info(f"Analysis sequence: {analysis_sequence}")
    return analysis_sequence




def facade_phase(repo_git, full_collection):
    logger = logging.getLogger(facade_phase.__name__)
    logger.info("Generating facade sequence")
    facade_helper = FacadeHelper(logger)
    #Get the repo_id
    #repo_list = s.sql.text("""SELECT repo_id,repo_group_id,repo_path,repo_name FROM repo WHERE repo_git=:value""").bindparams(value=repo_git)
    #repos = fetchall_data_from_sql_text(repo_list)

    #repo_ids = [repo['repo_id'] for repo in repos]

    #repo_id = repo_ids.pop(0)

    #Get the collectionStatus
    #query = session.query(CollectionStatus).filter(CollectionStatus.repo_id == repo_id)

    #status = execute_session_query(query,'one')
    
    # Figure out what we need to do
    limited_run = facade_helper.limited_run
    run_analysis = facade_helper.run_analysis
    pull_repos = facade_helper.pull_repos
    #force_analysis = session.force_analysis
    run_facade_contributors = facade_helper.run_facade_contributors

    facade_core_collection = []

    if not limited_run or (limited_run and pull_repos):
        facade_core_collection.append(git_repo_updates_facade_task.si(repo_git))
    

    #Generate commit analysis task order.
    if not limited_run or (limited_run and run_analysis):
        facade_core_collection.extend(generate_analysis_sequence(logger,repo_git,facade_helper))

    #Generate contributor analysis task group.
    if not limited_run or (limited_run and run_facade_contributors):
        facade_core_collection.append(insert_facade_contributors.si(repo_git))


    #These tasks need repos to be cloned by facade before they can work.
    facade_sequence = group(
        chain(*facade_core_collection),
        process_dependency_metrics.si(repo_git),
        process_libyear_dependency_metrics.si(repo_git),
        process_scc_value_metrics.si(repo_git)
    )

    logger.info(f"Facade sequence: {facade_sequence}")
    return facade_sequence