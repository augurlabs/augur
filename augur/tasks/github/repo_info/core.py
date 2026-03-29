#SPDX-License-Identifier: MIT
import json
import sqlalchemy as s
from augur.tasks.github.util.github_data_access import GithubDataAccess, UrlNotFoundException
from augur.tasks.github.util.github_graphql_data_access import GithubGraphQlDataAccess
from augur.tasks.github.util.github_paginator import hit_api
from augur.tasks.github.util.util import get_owner_repo
from augur.tasks.github.util.gh_graphql_entities import request_graphql_dict
from augur.application.db.models import *
from augur.application.db.lib import execute_sql
from augur.tasks.github.util.github_task_session import *
from augur.application.db.models.augur_data import RepoBadging
from urllib.parse import quote

def query_committers_count(key_auth, logger, owner, repo):

    data = {}
    logger.info('Querying committers count\n')
    url = f'https://api.github.com/repos/{owner}/{repo}/contributors?per_page=100'
    ## If the repository is empty there are zero committers, and the API returns nothing at all. Response 
    ## header of 200 along with an empty JSON. 
    try: 
        github_data_access = GithubDataAccess(key_auth, logger)
        try: 
            data = github_data_access.get_resource_count(url) 
        except Exception as e: 
            logger.warning(f"JSON Decode error: {e} indicating there are no committers or the repository is empty or archived.")
            data = 0 
            pass 
        if not data: 
            logger.warning("The API Returned an empty JSON object.")
        else: 
            logger.warning("Committer count data returned in JSON")
    except ValueError: 
        logger.warning("The API did not return valid JSON for committer count. This usually occurs on empty or archived repositories.")
        data=0
    
    return data 
"""
def get_repo_data(logger, url, response):
    data = {}
    try:
        data = response.json()
    except:
        data = json.loads(json.dumps(response.text))

    if 'errors' in data:
        logger.info("Error!: {}".format(data['errors']))
        raise Exception(f"Github returned error response! {data['errors']}")

    if 'id' not in data:
        logger.info("Request returned a non-data dict: {}\n".format(data))
        if data['message'] == 'Not Found':
            raise Exception(f"Github repo was not found or does not exist for endpoint: {url}\n")

    return data
""" 
def get_repo_data(logger, owner, repo):

    try:
        url = f'https://api.github.com/repos/{owner}/{repo}'
        github_data_access = GithubDataAccess(None, logger)
        result = github_data_access.get_resource(url)
        return result
    except UrlNotFoundException as e:
        message = f"GitHub repo was not found or does not exist for endpoint: {url}"
        logger.error(message)
        raise Exception(message) from e
    except Exception as e:
        logger.error(e)
        raise e

def is_forked(logger, repo_data): #/repos/:owner/:repo parent
    logger.info('Determining if the repo is forked\n')
    
    if 'fork' in repo_data:
        if 'parent' in repo_data:
            return repo_data['parent']['full_name']
        return 'Parent not available'

    return False

def is_archived(logger, repo_data):
    logger.info('Determining if the repo is archived\n')

    if 'archived' in repo_data:
        if repo_data['archived']:
            if 'updated_at' in repo_data:
                return repo_data['updated_at']
            return 'Date not available'
        return False

    return False

def grab_repo_info_from_graphql_endpoint(key_auth, logger, query):
    url = GithubGraphQlDataAccess.base_url()
    # Hit the graphql endpoint and retry 3 times in case of failure
    logger.info("Hitting endpoint: {} ...\n".format(url))
    data = request_graphql_dict(key_auth, logger, url, query)

    if not data:
        raise Exception(f"Could not get data from endpoint!")
    if 'errors' in data:
        raise Exception(f"Error!: {data['errors']}")
    
    if 'data' in data:
        data = data['data']['repository']
    else:
        logger.info("Request returned a non-data dict: {}\n".format(data))
        if data['message'] == 'Not Found':
            raise Exception(f"Github repo was not found or does not exist for endpoint: {url}\n")
    
    return data
    

def repo_info_model(key_auth, repo_orm_obj, logger):
    logger.info("Beginning filling the repo_info model for repo: " + repo_orm_obj.repo_git + "\n")

    owner, repo = get_owner_repo(repo_orm_obj.repo_git)

    query = """query($repo: String!, $owner: String!) {
                repository(name: $repo, owner: $owner) {
                    updatedAt
                    hasIssuesEnabled
                    issues(states: OPEN) {
                    totalCount
                    }
                    hasWikiEnabled
                    forkCount
                    defaultBranchRef {
                    name
                    }
                    watchers {
                    totalCount
                    }
                    id
                    licenseInfo {
                    name
                    url
                    }
                    stargazers {
                    totalCount
                    }
                    codeOfConduct {
                    name
                    url
                    }
                    issue_count: issues {
                    totalCount
                    }
                    issues_closed: issues(states: CLOSED) {
                    totalCount
                    }
                    pr_count: pullRequests {
                    totalCount
                    }
                    pr_open: pullRequests(states: OPEN) {
                    totalCount
                    }
                    pr_closed: pullRequests(states: CLOSED) {
                    totalCount
                    }
                    pr_merged: pullRequests(states: MERGED) {
                    totalCount
                    }
                    defaultBranchRef {
                    target {
                        ... on Commit {
                        history {
                            totalCount
                        }
                        }
                    }
                    }
                }
                }
                """
    
    github_graphql_data_access = GithubGraphQlDataAccess(key_auth, logger)

    variables = {
        "owner": owner,
        "repo": repo
    }

    result_keys = ["repository"]

    data = github_graphql_data_access.get_resource(query, variables, result_keys)

    # Get committers count info that requires seperate endpoint  
    committers_count = query_committers_count(key_auth, logger, owner, repo)

    # Put all data together in format of the table
    logger.info(f'Inserting repo info for repo with id:{repo_orm_obj.repo_id}, owner:{owner}, name:{repo}\n')
    rep_inf = {
        'repo_id': repo_orm_obj.repo_id,
        'last_updated': data['updatedAt'] if 'updatedAt' in data else None,
        'issues_enabled': data['hasIssuesEnabled'] if 'hasIssuesEnabled' in data else None,
        'open_issues': data['issues']['totalCount'] if data['issues'] else None,
        'pull_requests_enabled': None,
        'wiki_enabled': data['hasWikiEnabled'] if 'hasWikiEnabled' in data else None,
        'pages_enabled': None,
        'fork_count': data['forkCount'] if 'forkCount' in data else None,
        'default_branch': data['defaultBranchRef']['name'] if data['defaultBranchRef'] else None,
        'watchers_count': data['watchers']['totalCount'] if data['watchers'] else None,
        'license': data['licenseInfo']['name'] if data['licenseInfo'] else None,
        'stars_count': data['stargazers']['totalCount'] if data['stargazers'] else None,
        'committers_count': committers_count,
        'issue_contributors_count': None,
        'changelog_file': None,
        'contributing_file': None,
        'license_file': data['licenseInfo']['url'] if data['licenseInfo'] else None,
        'code_of_conduct_file': data['codeOfConduct']['url'] if data['codeOfConduct'] else None,
        'security_issue_file': None,
        'security_audit_file': None,
        'status': None,
        'keywords': None,
        'commit_count': data['defaultBranchRef']['target']['history']['totalCount'] if data['defaultBranchRef'] else None,
        'issues_count': data['issue_count']['totalCount'] if data['issue_count'] else None,
        'issues_closed': data['issues_closed']['totalCount'] if data['issues_closed'] else None,
        'pull_request_count': data['pr_count']['totalCount'] if data['pr_count'] else None,
        'pull_requests_open': data['pr_open']['totalCount'] if data['pr_open'] else None,
        'pull_requests_closed': data['pr_closed']['totalCount'] if data['pr_closed'] else None,
        'pull_requests_merged': data['pr_merged']['totalCount'] if data['pr_merged'] else None,
        'tool_source': 'Repo_info Model',
        'tool_version': '0.50.0',
        'data_source': "Github"
    }

    #result = bulk_insert_dicts(rep_inf,RepoInfo,['repo_info_id']) #result = self.db.execute(self.repo_info_table.insert().values(rep_inf))
    insert_statement = s.sql.text("""INSERT INTO repo_info (repo_id,last_updated,issues_enabled,
			open_issues,pull_requests_enabled,wiki_enabled,pages_enabled,fork_count,
			default_branch,watchers_count,license,stars_count,
			committers_count,issue_contributors_count,changelog_file, contributing_file, license_file, code_of_conduct_file, security_issue_file,
            security_audit_file, status, keywords, commit_count, issues_count, issues_closed, pull_request_count, pull_requests_open, pull_requests_closed, pull_requests_merged,
            tool_source, tool_version, data_source)
			VALUES (:repo_id,:last_updated,:issues_enabled,
			:open_issues,:pull_requests_enabled,:wiki_enabled,:pages_enabled,:fork_count,
			:default_branch,:watchers_count,:license,:stars_count,
			:committers_count,:issue_contributors_count,:changelog_file, :contributing_file, :license_file, :code_of_conduct_file, :security_issue_file,
            :security_audit_file,:status, :keywords, :commit_count, :issues_count,:issues_closed, :pull_request_count, :pull_requests_open, :pull_requests_closed, :pull_requests_merged,
            :tool_source, :tool_version, :data_source)
			""").bindparams(**rep_inf)

    execute_sql(insert_statement)

    # Note that the addition of information about where a repository may be forked from, and whether a repository is archived, updates the `repo` table, not the `repo_info` table.
    repo_data = get_repo_data(logger, owner, repo)

    forked = is_forked(logger, repo_data)
    archived = is_archived(logger, repo_data)
    archived_date_collected = None
    if archived is not False:
        archived_date_collected = archived
        archived = 1
    else:
        archived = 0

    update_repo_data = s.sql.text("""UPDATE repo SET forked_from=:forked, repo_archived=:archived, repo_archived_date_collected=:archived_date_collected WHERE repo_id=:repo_id""").bindparams(forked=forked, archived=archived, archived_date_collected=archived_date_collected, repo_id=repo_orm_obj.repo_id)
    execute_sql(update_repo_data)

    logger.info(f"Inserted info for {owner}/{repo}\n")


def badges_model(logger,repo_git,repo_id,db):
    """ Data collection and storage method
        Query the CII API and store the result in the DB for the badges model

        This is a github task because it only covers github repos, this is not 
        part of the regular repo info model because it uses a differant api + github.
    """
    cii_endpoint = "https://bestpractices.coreinfrastructure.org/projects.json?pq="

    
    #https://github.com/chaoss/grimoirelab-hatstall
    logger.info(f"Collecting badge data for {repo_git}")
    git_url_extension = quote(repo_git[0:-4])

    url = cii_endpoint + git_url_extension
    logger.debug(f"Hitting CII endpoint: {url}")

    #Hit cii api with no api key.
    response = hit_api(None, url, logger)

    try:
        response_data = response.json()
    except:
        response_data = json.loads(json.dumps(response.text))

    #Insert any data that was returned
    if len(response_data) > 0:
        RepoBadging.insert(db, repo_id, response_data)
    else:
        logger.info(f"Could not find CII data for {repo_git}")


