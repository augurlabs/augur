"""Utility functions that are useful for several Github tasks"""
from typing import Any, List, Tuple
import logging
import urllib.parse
import json
import httpx
from augur.tasks.github.util.github_random_key_auth import GithubRandomKeyAuth
from augur.tasks.github.util.github_graphql_data_access import GithubGraphQlDataAccess
from augur.application.db.lib import get_repo_by_repo_git
from augur.tasks.util.worker_util import calculate_date_weight_from_timestamps


def sanity_check_email(possible_email:str) -> str:
    """Accept a string that might contain an email and attempt to validate it
    This was built for performing some basic sanity checking before attempting to use
    the information in an email address for processing.

    It is built to be simple without new libraries for now
    since the intent is more for basic sanity checks to aid in parsing a known format.
    It is not (yet) fully RFC-compliant.

    If it becomes heavily used, we should defer to a well-made library

    Args:
        possible_email (str): a string that might contain an email

    Returns:
        str: a string representing what should (mostly) be a valid email address. None is returned if no valid email could be found.
    """
    
    try:
        if possible_email is None:
            return None
        
        candidate_email = str(possible_email)


        at_pos = candidate_email.find("@")
        if at_pos == -1:
            # email cannot possibly be valid without an @ sign
            return None

        preceeding_space = candidate_email.rfind(" ", 0)
        following_space = candidate_email.find(" ", at_pos)
        search_result = (preceeding_space != -1, following_space != -1)

        if search_result == (True, True):
            # spaces were on either side
            candidate_email = candidate_email[preceeding_space, following_space + 1]
        elif  search_result == (False, True):
            # space after
            candidate_email = candidate_email[:following_space + 1]
        elif  search_result == (True, False):
            # space after
            candidate_email = candidate_email[preceeding_space:]
        # otherwise, there were no spaces, so the string stays the same.

        if not candidate_email.isascii():
            # non-ascii is pretty uncommon, especially for narrow usecases like
            # checking for an existing domain like the github noreply domain.
            # if this is insufficient, a library may be a better option.

            return None

        return candidate_email
    except Exception:
        return None

def get_repo_src_id(owner, repo, logger):
    

    query = """query($repo: String!, $owner: String!) {
                    repository(name: $repo, owner: $owner) {
                        databaseId
                    }
                }
                """
    
    key_auth = GithubRandomKeyAuth(logger)
    
    github_graphql_data_access = GithubGraphQlDataAccess(key_auth, logger)

    variables = {
        "owner": owner,
        "repo": repo
    }

    result_keys = ["repository", "databaseId"]

    repo_src_id = github_graphql_data_access.get_resource(query, variables, result_keys)

    return repo_src_id



# This function adds a key value pair to a list of dicts and returns the modified list of dicts back
def add_key_value_pair_to_dicts(data: List[dict], key: str, value: Any) -> List[dict]:
    """Adds a key value pair to a list of dicts

    Args:
        data: list of dicts that is being modified
        key: key that is being added to dicts
        value: value that is being added to dicts

    Returns:
        list of dicts with the key value pair added
    """

    for item in data:

        item[key] = value

    return data

def get_owner_repo(git_url: str) -> Tuple[str, str]:
    """Gets the owner and repository names of a repository from a git url

    Args:
        git_url: the git url of a repository

    Returns:
        the owner and repository names in that order
    """
    split = git_url.split('/')

    owner = split[-2]
    repo = split[-1]

    if '.git' == repo[-4:]:
        repo = repo[:-4]

    return owner, repo

def get_gitlab_repo_identifier(owner, repo):

    return urllib.parse.quote(f"{owner}/{repo}", safe='')


def parse_json_response(logger: logging.Logger, response: httpx.Response) -> dict:
    # try to get json from response
    try:
        return response.json()
    except json.decoder.JSONDecodeError as e:
        logger.warning(f"invalid return. Response was: {response.text}. Exception: {e}")
        return json.loads(json.dumps(response.text))

def get_repo_weight_by_issue(logger,repo_git):
    """
    Retrieve the sum of the number of issues and prs in a repository from a graphql query.

    Arguments:
        logger: logger object
        repo_git: repository url
    
    Returns:
        Sum of issues and prs for that repo
    """

    from augur.tasks.github.util.gh_graphql_entities import GitHubRepo as GitHubRepoGraphql

    owner,name = get_owner_repo(repo_git)

    key_auth = GithubRandomKeyAuth(logger)

    repo_graphql = GitHubRepoGraphql(logger, key_auth, owner, name)
    number_of_issues_and_prs = len(repo_graphql.get_issues_collection()) + len(repo_graphql.get_pull_requests_collection())
    
    return number_of_issues_and_prs

#Get the weight for each repo for the core collection hook
def get_repo_weight_core(logger,repo_git):
    
    repo = get_repo_by_repo_git(repo_git)

    if not repo:
        raise Exception(f"Task with repo_git of {repo_git} but could not be found in Repo table")
    
    #try to get the collection status if it exists at this point
    try:
        status = repo.collection_status[0]
        time_factor = calculate_date_weight_from_timestamps(repo.repo_added,status.core_data_last_collected)
    except IndexError:
        time_factor = calculate_date_weight_from_timestamps(repo.repo_added,None)


    #Don't go below zero.
    return max(0,get_repo_weight_by_issue(logger, repo_git) - time_factor)

