from augur.tasks.github.util.github_task_session import *
from augur.application.db.models import Repo, CollectionStatus
from augur.tasks.github.util.github_paginator import hit_api
from augur.tasks.github.util.util import get_owner_repo
from augur.tasks.github.util.util import parse_json_response
from datetime import datetime
from augur.tasks.util.collection_state import CollectionState
from augur.application.db.util import execute_session_query
from augur.application.db.lib import bulk_insert_dicts
from augur.application.db.models import HistoricalRepoURLs
from sqlalchemy.exc import IntegrityError


class RepoMovedException(Exception):
    def __init__(self, message, new_url=None): 
        super().__init__(message)
        self.new_url = new_url 

class RepoGoneException(Exception):
    pass


def update_repo_with_dict(repo,new_dict,logger):
    """
        Update a repository record in the database using a dictionary tagged with
        the appropriate table fields

        Args:
            repo: orm repo object to update
            new_dict: dict of new values to add to the repo record
            logger: logging object
            db: db object
    """
    to_insert = dict(repo.__dict__)
    del to_insert['_sa_instance_state']

    old_url = to_insert["repo_git"]
    repo_id = to_insert["repo_id"]

    with DatabaseSession(logger) as session:
        previous_alias = HistoricalRepoURLs(repo_id=repo_id, git_url=old_url)
        try:
            result = session.add(previous_alias)
            session.commit()
        except IntegrityError as e: #Unique violation
            session.rollback()    

    to_insert.update(new_dict)

    result = bulk_insert_dicts(logger, to_insert, Repo, ['repo_id'])

    url = to_insert['repo_git']
    logger.info(f"Updated repo {old_url} to {url} and set alias\n")
    return url



def extract_owner_and_repo_from_endpoint(key_auth, url, logger):
    response_from_gh = hit_api(key_auth, url, logger)

    page_data = parse_json_response(logger, response_from_gh)
    # Note: if parse_json_response fails, it will return a string, causing `in` to do a substring check.
    # This may lead to a crash if the field is present but the parsing fails.
    if response_from_gh.status_code != 200 or 'full_name' not in page_data:
        logger.error(
            f"Unexpected response fetching redirect target: status={response_from_gh.status_code}, "
            f"url={url}, body={response_from_gh.text}"
        )
        raise Exception("Could not resolve owner/repo from redirect target due to missing data in the github response")
    full_repo_name = page_data['full_name']

    splits = full_repo_name.split('/')

    return splits[0], splits[-1]

def ping_github_for_repo_move(session, key_auth, repo, logger,collection_hook='core'):

    owner, name = get_owner_repo(repo.repo_git)
    url = f"https://api.github.com/repos/{owner}/{name}"

    attempts = 0
    while attempts < 10:
        response_from_gh = hit_api(key_auth, url, logger, follow_redirects=False)

        if response_from_gh:
            break

        attempts += 1

    if attempts >= 10:
        logger.error(f"Could not check if repo moved because the api timed out 10 times. Url: {url}")
        raise Exception(f"ERROR: Could not get api response for repo: {url}")

    #Update Url and retry if 301
    #301 moved permanently 
    if response_from_gh.status_code == 301:
        redirect_location = response_from_gh.headers.get('location') or response_from_gh.headers.get('Location')
        if not redirect_location:
            logger.error(f"Could not check if repo moved because the redirect location is not present. Url: {url}")
            raise Exception(f"ERROR: Could not get redirect location for repo: {url}")

        owner, name = extract_owner_and_repo_from_endpoint(key_auth, redirect_location, logger)

        try:
            old_description = str(repo.description)
        except Exception:
            old_description = ""

        #Create new repo object to update existing
        repo_update_dict = {
            'repo_git': f"https://github.com/{owner}/{name}",
            'repo_path': None,
            'repo_name': None,
            'description': f"(Originally hosted at {url}) {old_description}"
        }

        new_url = update_repo_with_dict(repo, repo_update_dict, logger)

        raise RepoMovedException("ERROR: Repo has moved! Resetting Collection!", new_url=new_url)
    
    #Mark as ignore if 404
    if response_from_gh.status_code == 404:
        repo_update_dict = {
            'repo_git': repo.repo_git,
            'repo_path': None,
            'repo_name': None,
            'description': f"During our check for this repo on {datetime.today().strftime('%Y-%m-%d')}, a 404 error was returned. The repository does not appear to have moved. Instead, it appears to be deleted",
            'data_collection_date': datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ')
            }

        update_repo_with_dict(repo, repo_update_dict, logger)

        statusQuery = session.query(CollectionStatus).filter(CollectionStatus.repo_id == repo.repo_id)

        collectionRecord = execute_session_query(statusQuery,'one')

        collectionRecord.core_status = CollectionState.IGNORE.value
        collectionRecord.core_task_id = None
        collectionRecord.core_data_last_collected = datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ')

        collectionRecord.secondary_status = CollectionState.IGNORE.value
        collectionRecord.secondary_task_id = None
        collectionRecord.secondary_data_last_collected = datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ')

        collectionRecord.facade_status = CollectionState.IGNORE.value
        collectionRecord.facade_task_id = None
        collectionRecord.facade_data_last_collected = datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ')

        collectionRecord.ml_status = CollectionState.IGNORE.value
        collectionRecord.ml_task_id = None
        collectionRecord.ml_data_last_collected = datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ')


        session.commit()
        raise RepoGoneException("ERROR: Repo has moved, and there is no redirection! 404 returned, not 301. Resetting Collection!")

    
    #skip if not 404
    logger.info(f"Repo found at url: {url}")
    return

