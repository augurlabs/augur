from augur.tasks.github.util.github_task_session import *
import json
import time
import sqlalchemy as s
from augur.application.db.models import *
from augur.tasks.github.util.github_paginator import hit_api, process_dict_response
from augur.tasks.github.util.github_data_access import GithubDataAccess
# Debugger
from augur.tasks.github.util.github_paginator import GithubApiResult
from augur.application.db.lib import get_repo_by_repo_id, bulk_insert_dicts, execute_sql, get_contributors_by_github_user_id


##TODO: maybe have a TaskSession class that holds information about the database, logger, config, etc.

# postgresql
#'sqla+postgresql://scott:tiger@localhost/mydatabase'

"""
A few interesting ideas: Maybe get the top committers from each repo first? curl https://api.github.com/repos/chaoss/augur/contributors

"""

# Added: Defensive helper to clean None values before inserting into Redis or DB
# This was defined globally in the file, and used elsewhere (e.g., in insert_alias).
def clean_dict(d):
    """Replace None values with empty strings for safe insertion."""
    return {k: ("" if v is None else v) for k, v in d.items()}


# deprecated in favor of GithubDataAcess.get_resource()
def request_dict_from_endpoint(logger, session, url, timeout_wait=10):
    """Hit the endpoint specified by the url and return the json that it returns if it returns a dict.
    
    NOTE: This function is being deprecated in favor of GithubDataAcess.get_resource()
    No functional change in this function body; logic preserved fully.
    This function still attempts to hit a GitHub API endpoint and return a dictionary if successful.


    Returns:
        None on failure. Dict on success
    """
    attempts = 0
    response_data = None
    success = False

    while attempts < 10:
        try:
            response = hit_api(session.oauths, url, logger)
        except TimeoutError:
            logger.warning(
                f"User data request for enriching contributor data failed with {attempts} attempts! Trying again...")
            time.sleep(timeout_wait)
            continue

        if not response:
            attempts += 1
            continue

        # New (corrected anti-pattern): check if response is empty
        try:
            response_data = json.loads(response.text)
        except json.JSONDecodeError as je:
            logger.error(f"Failed to decode response text as JSON: {je}")
            attempts += 1
            continue

        if type(response_data) == dict:
            err = process_dict_response(logger, response, response_data)

            # ✅ No change here: continues retry loop on soft API error
            if err and err != GithubApiResult.SUCCESS:
                attempts += 1
                logger.warning(f"err: {err}")
                continue

            success = True
            break

        elif type(response_data) == list:
            logger.warning("Wrong type returned, trying again...")
            logger.debug(f"Returned list: {response_data}")

        elif type(response_data) == str:
            logger.warning(f"Warning! page_data was string: {response_data}")
            if "<!DOCTYPE html>" in response_data:
                logger.warning("HTML was returned, trying again...\n")
            elif len(response_data) == 0:
                logger.warning("Empty string, trying again...\n")
            else:
                try:
                    # ✅ Same logic: try to parse raw string and retry if successful
                    response_data = json.loads(response_data)

                    err = process_dict_response(logger, response, response_data)
                    if err and err != GithubApiResult.SUCCESS:
                        continue

                    success = True
                    break
                except:
                    pass

        attempts += 1

    if not success:
        return None

    return response_data


def create_endpoint_from_email(email):
    # Note: I added "+type:user" to avoid having user owned organizations be returned
    # Also stopped splitting per note above.
    url = 'https://api.github.com/search/users?q={}+in:email+type:user'.format(
        email)
    

    return url


def create_endpoint_from_commit_sha(logger, commit_sha, repo_id):
    logger.debug(
        f"Trying to create endpoint from commit hash: {commit_sha}")

    # https://api.github.com/repos/chaoss/augur/commits/53b0cc122ac9ecc1588d76759dc2e8e437f45b48


    #stmnt = s.select(Repo.repo_path, Repo.repo_name).where(Repo.repo_id == repo_id)
    result = get_repo_by_repo_id(repo_id)

    if result.repo_path is None or result.repo_name is None:
        raise KeyError

    # Else put into a more readable local var

    split_git = result.repo_git.split('/')
    repo_name_and_org = split_git[-2] + "/" + result.repo_name

    url = "https://api.github.com/repos/" + repo_name_and_org + "/commits/" + commit_sha

    logger.debug(f"Commit Hash URL: {url}")

    return url


def insert_alias(logger, contributor, email):
    """Insert cntrb_id and email of the corresponding record into the alias table.
    Another database call to get the contributor id is needed because it's an
    autokeyincrement accessed by multiple workers. Same principle as enrich_cntrb_id method.
    Args:
        logger: Logger instance.
        contributor (dict): Contributor record containing 'gh_user_id' and optionally 'cntrb_canonical'.
        email (str): Email address to create the alias for.
    Raises:
        LookupError: If the contributor cannot be found in the database by gh_user_id.
    """

    contributor_table_data = get_contributors_by_github_user_id(contributor["gh_user_id"])

    # Handle potential failures
    if len(contributor_table_data) == 1:
        logger.debug(
            f"cntrb_id {contributor_table_data[0].cntrb_id} found in database and assigned to enriched data")
    elif len(contributor_table_data) == 0:
        logger.error("Couldn't find contributor in database. Something has gone very wrong. Augur ran into a contributor whose login can be found in the contributor's table, but cannot be retrieved via the user_id that was gotten using the same login.")
        raise LookupError
    else:
        logger.warning(
            f"There are more than one contributors in the table with gh_user_id={contributor['gh_user_id']}")

    logger.debug(f"Creating alias for email: {email}")

    # Insert a new alias that corresponds to where the contributor was found
    # Use the email of the new alias for canonical_email if the api returns NULL
    # TODO: It might be better to have the canonical_email allowed to be NULL because right now it has a null constraint.
    alias = {
        "cntrb_id": contributor_table_data[0].cntrb_id,
        "alias_email": email,
        "canonical_email": contributor['cntrb_canonical'] if 'cntrb_canonical' in contributor and contributor['cntrb_canonical'] is not None else email,
        # "tool_source": ...
        # "tool_version": ...
        # "data_source": ...
    }

    # Sanitize data to prevent Redis/DB errors on None values
    alias_clean = clean_dict(alias)

    # Insert new alias
    bulk_insert_dicts(logger, alias_clean, ContributorsAlias, ['alias_email'])

    return

def resolve_if_login_existing(logger, contributor) -> bool:
    """Takes the user data from the endpoint as arg.
    Updates the alias table if the login is already in the contributor's table with the new email.

    Returns:
        bool: Whether the login was found in the contributors table.
    """
    # check if login exists in contributors table
    select_cntrbs_query = s.sql.text("""
        SELECT cntrb_id from contributors
        WHERE cntrb_login = :gh_login_value
    """)

    # Bind parameter
    select_cntrbs_query = select_cntrbs_query.bindparams(
        gh_login_value=contributor['cntrb_login'])
    result = execute_sql(select_cntrbs_query)

    # if yes
    if len(result.fetchall()) >= 1:
        # self.insert_alias(contributor, email) Functions should do one thing ideally.
        return True

    # If not found, return false
    return False
"""
No longer used after orm upsert implement
def update_contributor(self, cntrb, max_attempts=3):

    # Get primary key so that we can update
    contributor_table_data = self.db.execute(
        s.sql.select([s.column('cntrb_id'), s.column('cntrb_canonical')]).where(
            self.contributors_table.c.gh_user_id == cntrb["gh_user_id"]
        )
    ).fetchall()

    attempts = 0

    # make sure not to overwrite canonical email if it isn't NULL

    canonical_email = contributor_table_data[0]['cntrb_canonical']
    # check if the contributor has a NULL canonical email or not
    #self.logger.info(f"The value of the canonical email is : {canonical_email}")

    if canonical_email is not None:
        del cntrb["cntrb_canonical"]
        self.logger.info(
            f"Existing canonical email {canonical_email} found in database and will not be overwritten.")

    while attempts < max_attempts:
        try:
            # Using with on a sqlalchemy connection prevents 'Connection refused' error
            # Ensures all database requests use the same connection
            with self.db.connect() as connection:
                # Use primary key to update the correct data.
                # It is important that non null data is not overwritten.
                connection.execute(self.contributors_table.update().where(
                    self.contributors_table.c.cntrb_id == contributor_table_data[0]['cntrb_id']
                ).values(cntrb))
            break  # break if success.
        except Exception as e:
            self.logger.info(
                f"Ran into exception updating contributor with data: {cntrb}. Error: {e}")
            # give a delay so that we have a greater chance of success.
            time.sleep(1)

        attempts += 1
"""



def fetch_username_from_email(logger, auth, commit) -> dict | None:
    """Try every distinct email found within a commit for possible username resolution.
    Add email to garbage table if can't be resolved.
    
    #   \param contributor is the raw database entry
 
    Args:
        logger (_type_): logging instance to use
        auth (_type_): Keymanager instance to use for auth
        commit (_type_): _description_

    Returns:
        dict: A dictionary of response data from github with potential logins on success.
#           None on failure
    """

    # Default to failed state
    login_json = None

    logger.info(f"Here is the commit: {commit}")

    email_raw = commit.get('email_raw')
    if not email_raw or not isinstance(email_raw, str) or len(email_raw.strip()) <= 2:
        logger.warning("Commit does not contain a valid 'email_raw' value.")
        return login_json  # Don't bother with emails that are blank or less than 2 characters

    try:
        url = create_endpoint_from_email(email_raw)
    except Exception as e:
        logger.error(
            f"Couldn't resolve email url with given data. Reason: {e}")
        # If the method throws an error it means that we can't hit the endpoint so we can't really do much
        return login_json

    try:
        github_data_access = GithubDataAccess(auth, logger, feature="search")
        login_json = github_data_access.get_resource(url)
    except Exception as e:
        logger.error(f"Couldn't resolve email URL with given data. Reason: {e}")
        # If the method throws an error it means that we can't hit the endpoint so we can't really do much
        return None

    # Check if the email result got anything, if it failed try a name search.
    if login_json is None or 'total_count' not in login_json or login_json['total_count'] == 0:
        logger.warning(
            f"Could not resolve the username from {email_raw}")
        logger.debug(f"email api url {url}")

        return None

    return login_json


def get_login_with_supplemental_data(logger, auth, commit_data):
    """Return the login given commit data using the supplemental data in the commit (email).

    Args:
        logger: Logger instance.
        auth: GithubRandomKeyAuth instance for API authentication.
        commit_data (dict): Commit record containing 'email_raw'.

    Returns:
        str: GitHub login username on success. None if unresolved.
    """

    # Try to get login from all possible emails
    # Is None upon failure.
    login_json = fetch_username_from_email(logger,auth,commit_data)

    # total_count is the count of username's found by the endpoint.
    # This Checks if the email result got anything.
    # If it fails, dont place it in unresolved yet as we may add more steps later
    if login_json is None or 'total_count' not in login_json:
        logger.error(
            "Search query returned an empty response. Could not resolve the username from the email. Moving on...\n")
        return None
    if login_json['total_count'] == 0:
        logger.error(
            "Search query did not return any results, adding commit's table remains null...\n")

        return None

    # Grab first result and make sure it has the highest match score
    try:
        match = login_json['items'][0]
    except IndexError as e:
        logger.error(f"Ran into error {e} when parsing users with search url: {url}\n return dict: {login_json}")
        return None

    for item in login_json['items']:
        if item['score'] > match['score']:
            match = item

    logger.debug(
        "When searching for a contributor, we found the following users: {}\n".format(match))

    return match['login']

def get_login_with_commit_hash(logger, auth, commit_data, repo_id):

    # Get endpoint for login from hash
    url = create_endpoint_from_commit_sha(
        logger, commit_data['hash'], repo_id)

    #TODO: here.
    # Send api request
    github_data_access = GithubDataAccess(auth, logger)
    login_json = github_data_access.get_resource(url)

    # TODO: Why are we returning None if 'sha' is not in response if we aren't even using it?
    if login_json is None or 'sha' not in login_json:
        logger.debug(f"Search query returned empty data. Moving on. Data: {login_json}")
        return None

    try:
        match = login_json['author']['login']
    except:
        match = None

    return match
