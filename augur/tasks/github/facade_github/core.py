from augur.tasks.github.facade_github.contributor_interfaceable.contributor_interface import * 
from augur.tasks.github.util.util import get_owner_repo
from augur.tasks.github.util.github_task_session import *
from augur.application.db.models import *
from augur.tasks.util.AugurUUID import GithubUUID
from augur.application.db.lib import bulk_insert_dicts, batch_insert_contributors
from augur.application.db.data_parse import extract_needed_contributor_data as extract_github_contributor
from augur.tasks.github.util.github_data_access import GithubDataAccess




def query_github_contributors(logger, key_auth, github_url, tool_source:str, tool_version:str, data_source:str):

    """ Data collection function
    Query the GitHub API for contributors
    """

    # Set platform id to 1 since it is a github method
    platform_id = 1

    # Extract owner/repo from the url for the endpoint
    try:
        owner, name = get_owner_repo(github_url)
    except IndexError as e:
        logger.error(f"Encountered bad url: {github_url}")
        raise e

    # Set the base of the url and place to hold contributors to insert
    contributors_url = (
        f"https://api.github.com/repos/{owner}/{name}/" +
        "contributors?state=all"
    )

    # Get contributors that we already have stored
    #   Set our duplicate and update column map keys (something other than PK) to
    #   check dupicates/needed column updates with
    table = 'contributors'
    table_pkey = 'cntrb_id'
    update_col_map = {'cntrb_email': 'email'}
    duplicate_col_map = {'cntrb_login': 'login'}

    github_data_access = GithubDataAccess(key_auth, logger)

    contributor_count = github_data_access.get_resource_count(contributors_url)

    logger.info("Count of contributors needing insertion: " + str(contributor_count) + "\n")

    if contributor_count == 0:
        return

    for repo_contributor in github_data_access.paginate_resource(contributors_url):
        try:
            # Need to hit this single contributor endpoint to get extra data including...
            #   `created at`
            #   i think that's it
            cntrb_url = ("https://api.github.com/users/" + repo_contributor['login'])

            
            logger.info("Hitting endpoint: " + cntrb_url + " ...\n")
            #r = hit_api(session.oauths, cntrb_url, logger)
            #contributor = r.json()

            contributor = github_data_access.get_resource(cntrb_url)

            cntrb = extract_github_contributor(contributor, tool_source, tool_version, data_source)

            #insert cntrb to table.
            #session.logger.info(f"Contributor:  {cntrb}  \n")
            batch_insert_contributors(logger, [cntrb])
            
        except Exception as e:
            logger.error("Caught exception: {}".format(e))
            logger.error("Cascading Contributor Anomalie from missing repo contributor data: {} ...\n".format(cntrb_url))
            raise e

# Get all the committer data for a repo.
# Used by facade in facade03analyzecommit
def grab_committer_list(logger, key_auth, repo_git, tool_source: str, tool_version: str, data_source: str, platform="github" ):

    # Create API endpoint from repo_id
    query_github_contributors(logger, key_auth, repo_git, tool_source, tool_version, data_source)
    