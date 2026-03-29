import logging
import re
import sqlalchemy as s
import urllib.parse
from time import sleep


from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.github.util.github_task_session import GithubTaskSession
from augur.tasks.github.util.github_graphql_data_access import GithubGraphQlDataAccess
from augur.application.db.lib import get_group_by_name, get_repo_by_repo_git, get_github_repo_by_src_id, get_gitlab_repo_by_src_id
from augur.tasks.github.util.util import get_owner_repo
from augur.application.db.models.augur_operations import retrieve_owner_repos, FRONTEND_REPO_GROUP_NAME, RepoGroup, CollectionStatus
from augur.tasks.github.util.github_paginator import hit_api

from augur.application.db.models import UserRepo, Repo

def parse_org_name(string):

    match = re.match(r'^\/?([a-zA-Z0-9_-]+)\/?$', string)
    return match

def parse_org_and_repo_name(string):

    match = re.match(r'^\/?([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_-]+)\/?$', string)
    return match

@celery.task
def add_github_orgs_and_repos(user_id, group_name, orgs, repo_urls):

    logger = logging.getLogger(add_github_orgs_and_repos.__name__)

    with GithubTaskSession(logger) as session:
     
        # determine group id from name
        group = get_group_by_name(user_id, group_name)
        if not group:
            logger.error(f"Error while adding repo. Invalid group name of {group_name}. Cannot insert repos")
            return
        
        group_id = group.group_id

        # get frontend repo group
        frontend_repo_group = RepoGroup.get_by_name(session, FRONTEND_REPO_GROUP_NAME)
        if not frontend_repo_group:
            logger.error("Error while adding repo: Could not find frontend repo group so repos cannot be inserted")
            return

        repo_group_id = frontend_repo_group.repo_group_id

        # define repo_data and assoicate repos with frontend repo group
        repo_data = [(url, repo_group_id) for url in repo_urls]

        # get org repos and associate them with their org repo group
        org_repo_data = get_org_repo_data(orgs, session)
        repo_data.extend(org_repo_data)

        # break list of repos into lists of 100 so that graphql query isn't overwhelmed
        for chunk in divide_list_into_chunks(repo_data, 100):

            add_new_github_repos(chunk, group_id, session, logger)


@celery.task
def add_gitlab_repos(user_id, group_name, repo_urls):

    logger = logging.getLogger(add_github_orgs_and_repos.__name__)

    with GithubTaskSession(logger) as session:
     
        # determine group id from name
        group = get_group_by_name(user_id, group_name)
        if not group:
            logger.error(f"Error while adding repo. Invalid group name of {group_name}. Cannot insert repos")
            return
        
        group_id = group.group_id

        # get frontend repo group
        frontend_repo_group = RepoGroup.get_by_name(session, FRONTEND_REPO_GROUP_NAME)
        if not frontend_repo_group:
            logger.error("Error while adding repo: Could not find frontend repo group so repos cannot be inserted")
            return

        repo_group_id = frontend_repo_group.repo_group_id

        for url in repo_urls:

            result = get_gitlab_repo_data(session, url, logger)
            if not result:
                continue

            if "id" not in result:
                logger.error(f"Gitlab repo data returned without id. Url: {url}. Data: {result}")
                continue

            repo_src_id = result["id"]

            existing_repo = get_gitlab_repo_by_src_id(repo_src_id)
            if existing_repo:

                if existing_repo.repo_group_id != repo_group_id:
                    update_existing_repos_repo_group_id(session, existing_repo.repo_id, repo_group_id)
                
                add_existing_repo_to_group(logger, session, group_id, existing_repo.repo_id)
                continue   

            existing_repo = get_repo_by_repo_git(session, url)
            if existing_repo:

                if existing_repo.repo_group_id != repo_group_id:
                    update_existing_repos_repo_group_id(session, existing_repo.repo_id, repo_group_id)

                add_existing_repo_to_group(logger, session, group_id, existing_repo.repo_id)
                continue
            
            add_gitlab_repo(logger, session, url, repo_group_id, group_id, repo_src_id)


def add_gitlab_repo(session, url, repo_group_id, group_id):

    repo_id = Repo.insert_gitlab_repo(session, url, repo_group_id, "Frontend")
    if not repo_id:
        return False, {"status": "Repo insertion failed", "repo_url": url}

    result = UserRepo.insert(session, repo_id, group_id)
    if not result:
        return False, {"status": "repo_user insertion failed", "repo_url": url}


def get_org_repo_data(orgs, session):

    repo_data = []
    for org in orgs:

        # create repo group for org if it doesn't exist
        repo_group = RepoGroup.get_by_name(session, org)
        if not repo_group:
            repo_group = create_repo_group(session, org)

        # retrieve repo urls for org
        org_repos, _ = retrieve_owner_repos(session, org)
        if not org_repos:
            continue

        # define urls and repo_group_id of org and then add to repo_data
        org_repo_data = [(url, repo_group.repo_group_id) for url in org_repos]
        repo_data.extend(org_repo_data)

    return repo_data

def add_new_github_repos(repo_data, group_id, session, logger):

      # get data for repos to determine type, src id, and if they exist
    data = get_github_repos_data(repo_data, session, logger)

    for url, repo_group_id in repo_data:

        repo_data = data[url]
        if not repo_data:
            # skip since cause the repo is not valid (doesn't exist likely)
            continue

        repo_src_id = repo_data["databaseId"]
        repo_type = repo_data["owner"]["__typename"]

        existing_repo = get_github_repo_by_src_id(repo_src_id)
        if existing_repo:

            if existing_repo.repo_group_id != repo_group_id:
                update_existing_repos_repo_group_id(session, existing_repo.repo_id, repo_group_id)

            add_existing_repo_to_group(logger, session, group_id, existing_repo.repo_id)
            continue     

        existing_repo = get_repo_by_repo_git(session, url)
        if existing_repo:

            if existing_repo.repo_group_id != repo_group_id:
                update_existing_repos_repo_group_id(session, existing_repo.repo_id, repo_group_id)

            add_existing_repo_to_group(logger, session, group_id, existing_repo.repo_id)
            continue

        add_github_repo(logger, session, url, repo_group_id, group_id, repo_type, repo_src_id)


def add_existing_repo_to_group(logger, session, group_id, repo_id):
    
    UserRepo.insert(session, repo_id, group_id)


def divide_list_into_chunks(data, size):
    
    for i in range(0, len(data), size): 
        yield data[i:i + size]


def get_github_repos_data(repo_data, session, logger):

    repo_urls = [x[0] for x in repo_data]

    github_graphql_data_access = GithubGraphQlDataAccess(session.oauths, logger, ingore_not_found_error=True)
    
    query_parts = []
    repo_map = {}
    for i, url in enumerate(repo_urls):
        owner, repo = get_owner_repo(url)
        query_parts.append(f"""repo_{i}: repository(owner: "{owner}", name: "{repo}") {{ 
                                databaseId, owner {{ __typename }} 
                        }}""")
    
    query = f"query GetRepoIds {{    {'    '.join(query_parts)}}}"

    data = github_graphql_data_access.get_resource(query, {}, [])

    result_data = {}
    for i, url in enumerate(repo_urls):
        result_data[url] = data[f"repo_{i}"]
    
    return result_data

def get_repo_by_repo_git(session, url):

    return session.query(Repo).filter(Repo.repo_git == url).first()
    
def create_repo_group(session, owner):

    repo_group = RepoGroup(rg_name=owner.lower(), rg_description="", rg_website="", rg_recache=0, rg_type="Unknown",
            tool_source="Loaded by user", tool_version="1.0", data_source="Git")
    session.add(repo_group)
    session.commit()

    return repo_group

def add_github_repo(logger, session, url, repo_group_id, group_id, repo_type, repo_src_id):

    # These two things really need to be done in one commit in the future to prevent one existing without the other
    repo_id = Repo.insert_github_repo(session, url, repo_group_id, "Frontend", repo_type, repo_src_id)
    if not repo_id:
        logger.error("Error while adding repo: Failed to insert github repo")
        return

    result = UserRepo.insert(session, repo_id, group_id)
    if not result:
        logger.error(f"Error while adding repo: Failed to insert user repo record. A record with a repo_id of {repo_id} and a group id of {group_id} needs to be added to the user repo table so that this repo shows up in the users group")
        return
    
    CollectionStatus.insert(session, logger, repo_id)
    

def get_gitlab_repo_data(gl_session, url: str, logger) -> bool:

    REPO_ENDPOINT = "https://gitlab.com/api/v4/projects/{}/"

    owner, repo = Repo.parse_gitlab_repo_url(url)
    if not owner or not repo:
        logger.error(f"Tried to get gitlab repo data for invalid url: {url}")
        return None

    # Encode namespace and project name for the API request
    project_identifier = urllib.parse.quote(f"{owner}/{repo}", safe='')
    url = REPO_ENDPOINT.format(project_identifier)

    attempts = 0
    while attempts < 10:
        response = hit_api(gl_session.oauths, url, logger)

        if wait_in_seconds := response.headers.get("Retry-After") is not None:
            sleep(int(wait_in_seconds))

        if response.status_code == 404:
            return None

        if response.status_code == 200:
            return response.json()

        attempts += 1
        sleep(attempts*3)

    logger.error(f"Failed to get gitlab repo data after multiple attemps. Url: {url}")

    return None

def add_gitlab_repo(logger, session, url, repo_group_id, group_id, repo_src_id):

    # These two things really need to be done in one commit in the future to prevent one existing without the other
    repo_id = Repo.insert_gitlab_repo(session, url, repo_group_id, "Frontend", repo_src_id)
    if not repo_id:
        logger.error("Error while adding repo: Failed to insert github repo")
        return

    result = UserRepo.insert(session, repo_id, group_id)
    if not result:
        logger.error(f"Error while adding repo: Failed to insert user repo record. A record with a repo_id of {repo_id} and a group id of {group_id} needs to be added to the user repo table so that this repo shows up in the users group")
        return
    
    CollectionStatus.insert(session, logger, repo_id)
    
def update_existing_repos_repo_group_id(session, repo_id, new_repo_group_id):

    # NOTE: It is safe to update the repos repo group id here because we know it will always be updating to an org repo group id. We don't want this behavior from the command line though, because a user adding a repo to a repo group could remove it from it's org repo group
    update_stmt = (
        s.update(Repo)
        .where(Repo.repo_id == repo_id)
        .values(repo_group_id=new_repo_group_id)
    )
    session.execute(update_stmt)
    session.commit()

# @celery.task
# def add_org_repo_list(user_id, group_name, urls):

#     logger = logging.getLogger(add_org_repo_list.__name__)

#     with GithubTaskSession(logger) as session:
     
#         user = User.get_by_id(session, user_id)

#     invalid_urls = []
#     valid_orgs = []
#     valid_repos = []
#     for url in urls:

#         # matches https://github.com/{org}/ or http://github.com/{org}
#         if Repo.parse_github_org_url(url):
#             added = user.add_github_org(group_name, url)[0]
#             if added:
#                 valid_orgs.append(url)

#         # matches https://github.com/{org}/{repo}/ or http://github.com/{org}/{repo}
#         elif Repo.parse_github_repo_url(url)[0]:
#             added = user.add_github_repo(group_name, url)[0]
#             if added:
#                 valid_repos.append(url)

#         # matches /{org}/{repo}/ or /{org}/{repo} or {org}/{repo}/ or {org}/{repo}
#         elif (match := parse_org_and_repo_name(url)):
#             org, repo = match.groups()
#             repo_url = f"https://github.com/{org}/{repo}/"
#             added = user.add_github_repo(group_name, repo_url)[0]
#             if added:
#                 valid_repos.append(url)

#         # matches /{org}/ or /{org} or {org}/ or {org}
#         elif (match := parse_org_name(url)):
#             org = match.group(1)
#             org_url = f"https://github.com/{org}/"
#             added = user.add_github_org(group_name, org_url)[0]
#             if added:
#                 valid_orgs.append(url)

#         # matches https://gitlab.com/{org}/{repo}/ or http://gitlab.com/{org}/{repo}
#         elif Repo.parse_gitlab_repo_url(url)[0]:

#             added = user.add_gitlab_repo(group_name, url)[0]
#             if added:
#                 valid_repos.append(url)

#         else:
#             invalid_urls.append(url)

#     return valid_orgs, valid_repos, invalid_urls
