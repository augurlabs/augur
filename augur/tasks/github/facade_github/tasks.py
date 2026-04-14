import logging


from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurFacadeRepoCollectionTask
from augur.tasks.github.util.github_data_access import GithubDataAccess, UrlNotFoundException
from augur.tasks.github.util.github_random_key_auth import GithubRandomKeyAuth
from augur.tasks.github.facade_github.core import *
from augur.application.db.lib import execute_sql, get_contributor_aliases_by_email, get_unresolved_commit_emails_by_email, get_repo_by_repo_git, batch_insert_contributors, get_batch_size
from augur.application.db.lib import get_session, execute_session_query
from augur.tasks.git.util.facade_worker.facade_worker.facade00mainprogram import *
from augur.application.db.lib import bulk_insert_dicts
from augur.application.db.data_parse import extract_needed_contributor_data as extract_github_contributor




def process_commit_metadata(logger, auth, contributorQueue, repo_id, platform_id, tool_source:str, tool_version:str, data_source:str):

    github_data_access = GithubDataAccess(auth, logger)

    for contributor in contributorQueue:
        # Get the email from the commit data
        email = contributor['email_raw'] if 'email_raw' in contributor else contributor['email']
    
        name = contributor['name']

        # check the email to see if it already exists in contributor_aliases
        
        # Look up email to see if resolved
        alias_table_data = get_contributor_aliases_by_email(email)
        if len(alias_table_data) >= 1:
            # Move on if email resolved
            logger.debug(
                f"Email {email} has been resolved earlier.")

            continue
        
        #Check the unresolved_commits table to avoid hitting endpoints that we know don't have relevant data needlessly
        
            
        unresolved_query_result = get_unresolved_commit_emails_by_email(email)

        if len(unresolved_query_result) >= 1:

            logger.debug(f"Commit data with email {email} has been unresolved in the past, skipping...")
            continue

        login = None
    
        #Check the contributors table for a login for the given name
        # This is being removed because anyone with a common name (i.e. dave, adam) who only puts
        # their first name or nickname on their profile is getting grouped with EVERYONE else who is doing that.
        # AE

        # contributors_with_matching_name = TODO

        # if not contributors_with_matching_name or len(contributors_with_matching_name) > 1:
        #     logger.debug("Failed local login lookup")
        # else:
        #     login = contributors_with_matching_name[0].gh_login
        

        # Try to get the login from the commit sha
        if login == None or login == "":
            login = get_login_with_commit_hash(logger, auth, contributor, repo_id)
    
        if login == None or login == "":
            logger.warning("Failed to get login from commit hash")
            # Try to get the login from supplemental data if not found with the commit hash
            login = get_login_with_supplemental_data(logger, auth,contributor)
    
        if login == None or login == "":
            logger.error("Failed to get login from supplemental data!")

            unresolved = {
                "email": email,
                "name": name,
            }
            logger.debug(f"No more username resolution methods available. Inserting data into unresolved table: {unresolved}")

            try:
                unresolved_natural_keys = ['email']
                bulk_insert_dicts(logger, unresolved, UnresolvedCommitEmail, unresolved_natural_keys)
            except Exception as e:
                logger.error(
                    f"Could not create new unresolved email {email}. Error: {e}")
            # move on to the next contributor
            continue

        url = ("https://api.github.com/users/" + login)

        try:
            user_data = github_data_access.get_resource(url)
        except UrlNotFoundException as e:
            logger.warning(f"User of {login} not found on github. Skipping...")
            continue

        # Use the email found in the commit data if api data is NULL
        emailFromCommitData = contributor['email_raw'] if 'email_raw' in contributor else contributor['email']


        # Get name from commit if not found by GitHub
        name_field = contributor['commit_name'] if 'commit_name' in contributor else contributor['name']

        cntrb = extract_github_contributor(user_data, tool_source, tool_version, data_source)
        if cntrb is None:
            continue

        # extra processing unique to facade based contributor collection
        if not cntrb.get('cntrb_canonical'):
            cntrb['cntrb_canonical'] = emailFromCommitData
        if not cntrb.get('cntrb_email'):
            cntrb['cntrb_email'] = emailFromCommitData
        
        if not cntrb.get('cntrb_full_name'):
            cntrb['cntrb_full_name'] = name_field

        
        #Executes an upsert with sqlalchemy 
        cntrb_natural_keys = ['cntrb_id']
        batch_insert_contributors(logger, [cntrb])

        try:
            # Update alias after insertion. Insertion needs to happen first so we can get the autoincrementkey
            insert_alias(logger, cntrb, emailFromCommitData)
        except LookupError as e:
            logger.error(
                ''.join(traceback.format_exception(None, e, e.__traceback__)))
            logger.error(
                f"Contributor id not able to be found in database despite the user_id existing. Something very wrong is happening. Error: {e}")
            return 
        

        #Replace each instance of a single or double quote with escape characters 
        #for postgres
        escapedEmail = email.replace('"',r'\"')
        escapedEmail = escapedEmail.replace("'",r'\'')
        # Resolve any unresolved emails if we get to this point.
        # They will get added to the alias table later
        # Do this last to absolutely make sure that the email was resolved before we remove it from the unresolved table.
        query = s.sql.text("""
            DELETE FROM unresolved_commit_emails
            WHERE email='{}'
        """.format(escapedEmail))

        logger.debug(f"Updating now resolved email {email}")

        try:
            execute_sql(query)
        except Exception as e:
            logger.error(
                f"Deleting now resolved email failed with error: {e}")
            raise e
    
        
    return


def link_commits_to_contributor(logger, facade_helper, contributorQueue):

    # # iterate through all the commits with emails that appear in contributors and give them the relevant cntrb_id.
    for cntrb in contributorQueue:
        logger.debug(
            f"These are the emails and cntrb_id's  returned: {cntrb}")

        query = s.sql.text("""
                UPDATE commits 
                SET cmt_ght_author_id=:cntrb_id
                WHERE 
                (cmt_author_raw_email=:cntrb_email
                OR cmt_author_email=:cntrb_email)
                AND cmt_ght_author_id is NULL
        """).bindparams(cntrb_id=cntrb["cntrb_id"],cntrb_email=cntrb["email"])

        #engine.execute(query, **data)
        facade_helper.insert_or_update_data(query)          
        
    
    return


# Update the contributors table from the data facade has gathered.
@celery.task(base=AugurFacadeRepoCollectionTask, bind=True)
def insert_facade_contributors(self, repo_git):

    tool_source = "Insert Contributors task"
    tool_version = "2.0"
    data_source = "Github API"

    # Set platform id to 1 since this task is github specific
    platform_id = 1

    logger = logging.getLogger(insert_facade_contributors.__name__)
    repo = get_repo_by_repo_git(repo_git)
    repo_id = repo.repo_id
    facade_helper = FacadeHelper(logger)

    # Find commits not yet linked to a contributor (cmt_ght_author_id IS NULL),
    # skipping emails already marked unresolvable.

    logger.info(
    "Beginning process to insert contributors from facade commits for repo w entry info: {}\n".format(repo_id))
    new_contrib_sql = s.sql.text("""
        SELECT DISTINCT
            commits.cmt_author_name AS NAME,
            commits.cmt_commit_hash AS hash,
            commits.cmt_author_raw_email AS email_raw
        FROM
            augur_data.commits
        WHERE
            commits.repo_id = :repo_id AND
            commits.cmt_ght_author_id IS NULL AND
            commits.cmt_author_raw_email NOT IN (
                SELECT email FROM augur_data.unresolved_commit_emails
            )
    """).bindparams(repo_id=repo_id)

    #Execute statement with session.
    result = execute_sql(new_contrib_sql)

    # Fetch all results immediately to close the database cursor/connection
    # This prevents holding the connection open during GitHub API calls
    rows = result.mappings().fetchall()

    #print(new_contribs)

    #json.loads(pd.read_sql(new_contrib_sql, self.db, params={
    #             'repo_id': repo_id}).to_json(orient="records"))


    key_auth = GithubRandomKeyAuth(logger)

    facade_batch_size = get_batch_size()

    # Process results in batches to reduce memory usage
    batch = []

    for row in rows:
        batch.append(dict(row))

        if len(batch) >= facade_batch_size:
            process_commit_metadata(logger, key_auth, batch, repo_id, platform_id, tool_source, tool_version, data_source)
            batch.clear()

    # Process remaining items in batch
    if batch:
        process_commit_metadata(logger, key_auth, batch, repo_id, platform_id, tool_source, tool_version, data_source)

    logger.debug("DEBUG: Got through the new_contribs")
    
    # Match unlinked commits to contributors via email from any source (cntrb_email, canonical email, or alias).
    resolve_email_to_cntrb_id_sql = s.sql.text("""
        WITH email_to_contributor AS (
            SELECT cntrb_email AS email, cntrb_id
            FROM augur_data.contributors
            WHERE cntrb_email IS NOT NULL

            UNION ALL

            SELECT cntrb_canonical AS email, cntrb_id
            FROM augur_data.contributors
            WHERE cntrb_canonical IS NOT NULL

            UNION ALL

            SELECT alias_email AS email, cntrb_id
            FROM augur_data.contributors_aliases
            WHERE alias_email IS NOT NULL
        ),
        deduplicated AS (
            SELECT DISTINCT ON (email) email, cntrb_id
            FROM email_to_contributor
            ORDER BY email
        )
        SELECT
            d.cntrb_id,
            c.cmt_author_email AS email
        FROM
            augur_data.commits c
        INNER JOIN
            deduplicated d
            ON c.cmt_author_email = d.email
        WHERE
            c.cmt_ght_author_id IS NULL AND
            c.repo_id = :repo_id
    """).bindparams(repo_id=repo_id)


    result = execute_sql(resolve_email_to_cntrb_id_sql)

    # Fetch all results immediately to close the database cursor/connection
    # This prevents holding the connection open during database UPDATE operations
    rows = result.mappings().fetchall()

    # Process results in batches to reduce memory usage
    batch = []

    for row in rows:
        batch.append(dict(row))

        if len(batch) >= facade_batch_size:
            link_commits_to_contributor(logger, facade_helper, batch)
            batch.clear()

    # Process remaining items in batch
    if batch:
        link_commits_to_contributor(logger, facade_helper, batch)

    return

