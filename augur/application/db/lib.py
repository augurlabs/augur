import re
import time
import random
import logging
import sqlalchemy as s
from sqlalchemy import func 
from sqlalchemy.exc import DataError
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError
from psycopg2.errors import DeadlockDetected
from typing import List, Any, Optional, Union

from augur.application.db.models import Config, Repo, Commit, WorkerOauth, Issue, PullRequest, PullRequestReview, ContributorsAlias,UnresolvedCommitEmail, Contributor, CollectionStatus, UserGroup, RepoGroup
from augur.tasks.util.collection_state import CollectionState
from augur.application.db import get_session, get_engine
from augur.application.db.util import execute_session_query, convert_type_of_value
from augur.application.db.session import remove_duplicates_by_uniques, remove_null_characters_from_list_of_dicts

logger = logging.getLogger("db_lib")


def get_value(section_name: str, setting_name: str) -> Optional[Any]:
    """Get the value of a setting from the config.

    Args:
        section_name: The name of the section that the setting belongs to 
        setting_name: The name of the setting

    Returns:
        The value from config if found, and None otherwise
    """

    with get_session() as session:


        # TODO temporary until added to the DB schema
        if section_name == "frontend" and setting_name == "pagination_offset":
            return 25

        try:
            query = session.query(Config).filter(Config.section_name == section_name, Config.setting_name == setting_name)
            config_setting = execute_session_query(query, 'one')
        except s.orm.exc.NoResultFound:
            return None

        setting_dict = config_setting.__dict__

        setting_dict = convert_type_of_value(setting_dict, logger)

        return setting_dict["value"]


def get_batch_size(task_type: str = None) -> int:
    """Get batch size for a task, with fallback to default.

    Args:
        task_type: Optional task type (e.g., "event", "message").
                   If provided and a specific config exists for it,
                   that value is used. Otherwise falls back to default_batch_size.

    Returns:
        Batch size integer (default: 1000)
    """
    if task_type:
        specific_key = f"github_{task_type}_batch_size"
        value = get_value("Tasks", specific_key)
        if value is not None:
            return int(value)

    default_value = get_value("Tasks", "default_batch_size")
    return int(default_value) if default_value is not None else 1000


def execute_sql(sql_text):

    engine = get_engine()

    with engine.begin() as connection:

        return_data = connection.execute(sql_text)  

    return return_data

def fetchall_data_from_sql_text(sql_text):

    engine = get_engine()

    with engine.begin() as connection:

        result = connection.execute(sql_text)
    return [dict(row) for row in result.mappings()]

def get_repo_by_repo_git(repo_git: str):

    with get_session() as session:

        query = session.query(Repo).filter(Repo.repo_git == repo_git)
        repo = execute_session_query(query, 'one')

        return repo
    
def get_repo_by_repo_id(repo_id):

    with get_session() as session:

        query = session.query(Repo).filter(Repo.repo_id == repo_id)
        repo = execute_session_query(query, 'one')

        return repo
    
def get_github_repo_by_src_id(src_id):
    
    with get_session() as session:

        query = session.query(Repo).filter(Repo.repo_src_id == src_id, Repo.repo_git.ilike(f'%https://github.com%'))
        repo = execute_session_query(query, 'first')

        return repo
    
def get_gitlab_repo_by_src_id(src_id):
    
    with get_session() as session:

        query = session.query(Repo).filter(Repo.repo_src_id == src_id, Repo.repo_git.ilike(f'%https://gitlab.com%'))
        repo = execute_session_query(query, 'first')

        return repo
        
    
def remove_working_commits_by_repo_id_and_hashes(repo_id, commit_hashes):

    remove_working_commits = s.sql.text("""DELETE FROM working_commits 
        WHERE repos_id = :repo_id AND working_commit IN :hashes
        """).bindparams(repo_id=repo_id,hashes=tuple(commit_hashes))
    
    execute_sql(remove_working_commits)  

def remove_working_commits_by_repo_id(repo_id):

    remove_working_commits = s.sql.text("""DELETE FROM working_commits WHERE repos_id=:repo_id""").bindparams(repo_id=repo_id)
    execute_sql(remove_working_commits)

def remove_commits_by_repo_id_and_hashes(repo_id, commit_hashes):

    remove_commit = s.sql.text("""DELETE FROM commits
        WHERE repo_id=:repo_id
        AND cmt_commit_hash IN :hashes""").bindparams(repo_id=repo_id,hashes=tuple(commit_hashes))
    execute_sql(remove_commit)


def remove_commits_by_repo_id(repo_id):

    remove_commits = s.sql.text("""DELETE FROM commits WHERE repo_id=:repo_id""").bindparams(repo_id=repo_id)
    execute_sql(remove_commits) 

def get_working_commits_by_repo_id(repo_id):

    query = s.sql.text("""SELECT working_commit FROM working_commits WHERE repos_id=:repo_id
    """).bindparams(repo_id=repo_id)

    try:
        working_commits = fetchall_data_from_sql_text(query)
    except:
        working_commits = []

    return working_commits

def get_missing_commit_message_hashes(repo_id):

    fetch_missing_hashes_sql = s.sql.text("""
    SELECT DISTINCT cmt_commit_hash FROM commits
    WHERE repo_id=:repo_id 
    AND cmt_commit_hash NOT IN 
    (SELECT DISTINCT cmt_hash FROM commit_messages WHERE repo_id=:repo_id);
    """).bindparams(repo_id=repo_id)

    try:
        missing_commit_hashes = fetchall_data_from_sql_text(fetch_missing_hashes_sql)
    except:
        missing_commit_hashes = []
    
    return missing_commit_hashes

def get_worker_oauth_keys(platform: str):

    with get_session() as session:

        results = session.query(WorkerOauth).filter(WorkerOauth.platform == platform).order_by(func.random()).all()

        return [row.access_token for row in results]
    
def get_active_repo_count(collection_type):

    with get_session() as session:
    
        return session.query(CollectionStatus).filter(getattr(CollectionStatus,f"{collection_type}_status" ) == CollectionState.COLLECTING.value).count()


def facade_bulk_insert_commits(logger, records):

    with get_session() as session:

        try:
            session.execute(
                    s.insert(Commit),
                    records,
                )
            session.commit()
        except Exception as e:
            session.rollback()
            
            if len(records) > 1:
                #split list into halves and retry insert until we isolate offending record
                firsthalfRecords = records[:len(records)//2]
                secondhalfRecords = records[len(records)//2:]

                facade_bulk_insert_commits(logger, firsthalfRecords)
                facade_bulk_insert_commits(logger, secondhalfRecords)
            elif len(records) == 1:
                commit_record = records[0]
                #replace incomprehensible dates with epoch.
                #2021-10-11 11:57:46 -0500
                
                # placeholder_date = "1970-01-01 00:00:15 -0500"
                placeholder_date = commit_record['cmt_author_timestamp']

                postgres_valid_timezones = {
                    -1200, -1100, -1000, -930, -900, -800, -700,
                    -600, -500, -400, -300, -230, -200, -100, 000,
                    100, 200, 300, 330, 400, 430, 500, 530, 545, 600,
                    630, 700, 800, 845, 900, 930, 1000, 1030, 1100, 1200,
                    1245, 1300, 1400
                }
                
                # Reconstruct timezone portion of the date string to UTC
                placeholder_date_segments = re.split(" ", placeholder_date)
                tzdata = placeholder_date_segments.pop()

                if ":" in tzdata:
                    tzdata = tzdata.replace(":", "")

                if int(tzdata) not in postgres_valid_timezones:
                    tzdata = "+0000"
                else:
                    raise e

                placeholder_date_segments.append(tzdata)

                placeholder_date = " ".join(placeholder_date_segments)

                #Check for improper utc timezone offset
                #UTC timezone offset should be between -14:00 and +14:00

                # analyzecommit.generate_commit_record() defines the keys on the commit_record dictionary
                commit_record['cmt_author_timestamp'] = placeholder_date
                commit_record['cmt_committer_timestamp'] = placeholder_date
                
                logger.warning(f"commit with invalid timezone set to UTC: {commit_record['cmt_commit_hash']}")

                session.execute(
                    s.insert(Commit),
                    [commit_record],
                )
                session.commit()
            else:
                raise e

def batch_insert_contributors(logger, data: Union[List[dict], dict], batch_size = 1000) -> Optional[List[dict]]:

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]

        bulk_insert_dicts(logger, batch, Contributor, ['cntrb_id'])
    
    return None



def bulk_insert_dicts(logger, data_input: Union[List[dict], dict], table, natural_keys: List[str], return_columns: Optional[List[str]] = None, string_fields: Optional[List[str]] = None, on_conflict_update:bool = True) -> Optional[List[dict]]:
    """ Provides bulk-insert/update (upsert) capabilitites for adding bulk data (as a column:value dict mapping) into a specific table

    Args:
        logger (_type_): the logger to use
        data_input (Union[List[dict], dict]): the dicts to upsert (must match the column names as defined in the schema for the table)
        table (_type_): the table to upsert the data into
        natural_keys (List[str]): the columns that define the natural unique keys for the data
        return_columns (Optional[List[str]], optional): list of the column names to return. Defaults to None.
        string_fields (Optional[List[str]], optional): list of keys in the incoming dicts that should be cleaned to handle bad characters postgres doesnt like. Defaults to None.
        on_conflict_update (bool, optional): whether to update on conflict. Defaults to True.

    Raises:
        e: _description_
        e: _description_
        Exception: _description_
        e: _description_
        e: _description_
        Exception: _description_

    Returns:
        Optional[List[dict]]: the original data with each item filtered to only contain the columns specified by `return_columns`, if present. 
    """

    if isinstance(data_input, list) is False:
        
        # if a dict is passed to data then 
        # convert it to a list with one value
        if isinstance(data_input, dict) is True:
            data = [data_input]
        
        else:
            logger.error("Data must be a list or a dict")
            return None
    else:
        data = list(data_input)

    if len(data) == 0:
        # self.logger.info("Gave no data to insert, returning...")
        return None

    if isinstance(data[0], dict) is False: 
        logger.error("Must be list of dicts")
        return None

    # remove any duplicate data 
    # this only counts something as a duplicate if every field is the same
    data = remove_duplicates_by_uniques(data, natural_keys)

    # remove null data from string fields
    if string_fields and isinstance(string_fields, list):
        data = remove_null_characters_from_list_of_dicts(data, string_fields)

    # creates list of arguments to tell sqlalchemy what columns to return after the data is inserted
    returning_args = []
    if return_columns:
        for column in return_columns:
            argument = getattr(table, column)
            returning_args.append(argument)

    # creates insert on table
    # that returns cols specificed in returning_args
    # and inserts the data specified in data
    # NOTE: if return_columns does not have an values this still works
    stmnt = postgresql.insert(table).returning(*returning_args).values(data)


    if on_conflict_update:

        # create a dict that the on_conflict_do_update method requires to be able to map updates whenever there is a conflict. See sqlalchemy docs for more explanation and examples: https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#updating-using-the-excluded-insert-values
        setDict = {}
        base_table = getattr(table, "__table__", table)
        for key in data[0].keys():
            existing_col = getattr(base_table.c, key)
            setDict[key] = func.coalesce(getattr(stmnt.excluded, key), existing_col)
            
        stmnt = stmnt.on_conflict_do_update(
            #This might need to change
            index_elements=natural_keys,
            
            #Columns to be updated
            set_ = setDict
        )

    else:
        stmnt = stmnt.on_conflict_do_nothing(
            index_elements=natural_keys
        )


    # print(str(stmnt.compile(dialect=postgresql.dialect())))
    attempts = 0
    # creates list from 1 to 10 / changed to 10-30 because deadlocks are taking longer
    sleep_time_list = list(range(10,66))
    deadlock_detected = False

    engine = get_engine()

    # if there is no data to return then it executes the insert then returns nothing
    if not return_columns:

        while attempts < 10:
            try:
                #begin keyword is needed for sqlalchemy 2.x
                #this is because autocommit support was removed in 2.0
                with engine.begin() as connection:
                    connection.execute(stmnt)
                    break
            except OperationalError as e:
                # print(str(e).split("Process")[1].split(";")[0])
                if isinstance(e.orig, DeadlockDetected):
                    deadlock_detected = True
                    sleep_time = random.choice(sleep_time_list)
                    logger.debug(f"Deadlock detected on {table.__table__} table...trying again in {round(sleep_time)} seconds: transaction size: {len(data)}")
                    time.sleep(sleep_time)

                    attempts += 1
                    continue
                
                raise e

            except Exception as e:
                #self.logger.info(e)
                if len(data) == 1:
                    raise e
                
                time.sleep(3)
                first_half = data[:len(data)//2]
                second_half = data[len(data)//2:]

                bulk_insert_dicts(logger, first_half, table, natural_keys, return_columns, string_fields, on_conflict_update)
                bulk_insert_dicts(logger, second_half,table, natural_keys, return_columns, string_fields, on_conflict_update)

        else:
            logger.error("Unable to insert data in 10 attempts")
            raise Exception("Unable to insert and return data in 10 attempts")

        if deadlock_detected is True:
            logger.error("Made it through even though Deadlock was detected")

        # success 
        return None
    

    # othewise it gets the requested return columns and returns them as a list of dicts
    while attempts < 10:
        try:
            with engine.begin() as connection:
                return_data_tuples = connection.execute(stmnt)
                break
        except OperationalError as e:
            if isinstance(e.orig, DeadlockDetected):
                sleep_time = random.choice(sleep_time_list)
                logger.debug(f"Deadlock detected on {table.__table__} table...trying again in {round(sleep_time)} seconds: transaction size: {len(data)}")
                time.sleep(sleep_time)

                attempts += 1
                continue   

            raise e

        except Exception as e:
            if len(data) == 1:
                raise e
            
            time.sleep(3)
            first_half = data[:len(data)//2]
            second_half = data[len(data)//2:]

            bulk_insert_dicts(logger, first_half, table, natural_keys, return_columns, string_fields, on_conflict_update)
            bulk_insert_dicts(logger, second_half, table, natural_keys, return_columns, string_fields, on_conflict_update)

    else:
        logger.error("Unable to insert and return data in 10 attempts")
        raise Exception("")

    if deadlock_detected is True:
        logger.error("Made it through even though Deadlock was detected")

    return_data = [dict(row) for row in return_data_tuples.mappings()]
    
    #no longer working in sqlalchemy 2.x
    #for data_tuple in return_data_tuples:
    #    return_data.append(dict(data_tuple))

    # using on confilict do nothing does not return the 
    # present values so this does gets the return values
    if not on_conflict_update:

        conditions = []
        for column in natural_keys:

            column_values = [value[column] for value in data]

            column = getattr(table, column)

            conditions.append(column.in_(tuple(column_values)))

        with get_session() as session:

            result = (
                session.query(table).filter(*conditions).all()
            )

        for row in result:

            return_dict = {}
            for field in return_columns:

                return_dict[field] = getattr(row, field)

            return_data.append(return_dict)


    return return_data



def get_issues_by_repo_id(repo_id):

    with get_session() as session:

        return session.query(Issue).filter(Issue.repo_id == repo_id).all()
    
def get_pull_requests_by_repo_id(repo_id):

    with get_session() as session:

        return session.query(PullRequest).filter(PullRequest.repo_id == repo_id).all()
    
def get_pull_request_reviews_by_repo_id(repo_id):

    with get_session() as session:

        return session.query(PullRequestReview).filter(PullRequestReview.repo_id == repo_id).all()
    
def get_contributor_aliases_by_email(email):

    with get_session() as session:

        return session.query(ContributorsAlias).filter_by(alias_email=email).all()

def get_unresolved_commit_emails_by_email(email):

    with get_session() as session:

        return session.query(UnresolvedCommitEmail).filter_by(email=email).all()
 
def get_contributors_by_github_user_id(id):

    with get_session() as session:

        # Look into this, where it was used was doing .all() but this query should really only return one
        return session.query(Contributor).filter_by(gh_user_id=id).all()

def update_issue_closed_cntrbs_by_repo_id(repo_id):

    engine = get_engine()

    get_ranked_issues = s.text(f"""
        WITH RankedIssues AS (
            SELECT repo_id, issue_id, cntrb_id, 
                ROW_NUMBER() OVER(PARTITION BY issue_id ORDER BY created_at DESC) AS rn
            FROM issue_events 
            WHERE "action" = 'closed'
        )
                                            
        SELECT issue_id, cntrb_id from RankedIssues where rn=1 and repo_id={repo_id} and cntrb_id is not NULL
    """)

    with engine.connect() as conn:
        result = conn.execute(get_ranked_issues).fetchall()

    update_data = []
    for row in result:
        update_data.append(
            {
            'issue_id': row[0], 
            'cntrb_id': row[1], 
            'repo_id': repo_id
            }
        )

    if update_data:
        with engine.begin() as connection:
            update_stmt = s.text("""
                UPDATE issues
                SET cntrb_id = :cntrb_id
                WHERE issue_id = :issue_id
                AND repo_id = :repo_id
            """)
            connection.execute(update_stmt, update_data)

def get_core_data_last_collected(repo_id):
    
    with get_session() as session:
        try:
           return session.query(CollectionStatus).filter(CollectionStatus.repo_id == repo_id).one().core_data_last_collected 
        except s.orm.exc.NoResultFound:
            return None

def get_secondary_data_last_collected(repo_id):
    
    with get_session() as session:
        try:
           return session.query(CollectionStatus).filter(CollectionStatus.repo_id == repo_id).one().secondary_data_last_collected 
        except s.orm.exc.NoResultFound:
            return None
        
def get_updated_prs(repo_id, since):
    
    with get_session() as session:
        return session.query(PullRequest).filter(PullRequest.repo_id == repo_id, PullRequest.pr_updated_at >= since).order_by(PullRequest.pr_src_number).all()
    
def get_updated_issues(repo_id, since):

    with get_session() as session:
        return session.query(Issue).filter(Issue.repo_id == repo_id, Issue.updated_at >= since).order_by(Issue.gh_issue_number).all()
            


def get_group_by_name(user_id, group_name):


    with get_session() as session:
        
        try:
            user_group = session.query(UserGroup).filter(UserGroup.user_id == user_id, UserGroup.name == group_name).one()
        except s.orm.exc.NoResultFound:
            return None

        return user_group
    
def get_repo_group_by_name(name):


    with get_session() as session:
        
        return  session.query(RepoGroup).filter(RepoGroup.rg_name == name).first()
        
