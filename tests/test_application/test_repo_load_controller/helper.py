import sqlalchemy as s
import logging

from augur.util.repo_load_controller import ORG_REPOS_ENDPOINT

from augur.application.db.session import DatabaseSession
from augur.application.db.models import Config, User
from augur.tasks.github.util.github_paginator import hit_api
from augur.application.db.util import execute_session_query


logger = logging.getLogger(__name__)


######## Helper Functions to Get Delete statements #################

def get_delete_statement(schema, table):

    return """DELETE FROM "{}"."{}";""".format(schema, table)

def get_repo_delete_statement():

    return get_delete_statement("augur_data", "repo")

def get_repo_group_delete_statement():

    return get_delete_statement("augur_data", "repo_groups")

def get_user_delete_statement():

    return get_delete_statement("augur_operations", "users")

def get_user_repo_delete_statement():

    return get_delete_statement("augur_operations", "user_repos")

def get_user_group_delete_statement():

    return get_delete_statement("augur_operations", "user_groups")

def get_config_delete_statement():

    return get_delete_statement("augur_operations", "config")

def get_repo_related_delete_statements(table_list):
    """Takes a list of tables related to the RepoLoadController class and generates a delete statement.

    Args:
        table_list: list of table names. Valid table names are 
        "user_repos" or "user_repo", "repo" or "repos", "repo_groups" or "repo_group:, "user" or "users", and "config"

    """

    query_list = []
    if "user_repos" in table_list or "user_repo" in table_list:
        query_list.append(get_user_repo_delete_statement())

    if "user_groups" in table_list or "user_group" in table_list:
        query_list.append(get_user_group_delete_statement())

    if "repos" in table_list or "repo" in table_list:
        query_list.append(get_repo_delete_statement())

    if "repo_groups" in table_list or "repo_group" in table_list:
        query_list.append(get_repo_group_delete_statement())

    if "users" in table_list or "user" in table_list:
        query_list.append(get_user_delete_statement())

    if "config" in table_list:
        query_list.append(get_config_delete_statement())

    return " ".join(query_list)

######## Helper Functions to add github api keys from prod db to test db #################
def add_keys_to_test_db(test_db_engine):

    row = None
    section_name = "Keys"
    setting_name = "github_api_key"
    with DatabaseSession(logger) as session:
        query = session.query(Config).filter(Config.section_name==section_name, Config.setting_name==setting_name)
        row = execute_session_query(query, 'one')

    with DatabaseSession(logger, test_db_engine) as test_session:
        new_row = Config(section_name=section_name, setting_name=setting_name, value=row.value, type="str")
        test_session.add(new_row)
        test_session.commit()


######## Helper Functions to get insert statements #################

def get_repo_insert_statement(repo_id, rg_id, repo_url="place holder url"):

    return """INSERT INTO "augur_data"."repo" ("repo_id", "repo_group_id", "repo_git", "repo_path", "repo_name", "repo_added", "repo_type", "url", "owner_id", "description", "primary_language", "created_at", "forked_from", "updated_at", "repo_archived_date_collected", "repo_archived", "tool_source", "tool_version", "data_source", "data_collection_date") VALUES ({}, {}, '{}', NULL, NULL, '2022-08-15 21:08:07', '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'CLI', '1.0', 'Git', '2022-08-15 21:08:07');""".format(repo_id, rg_id, repo_url)

def get_user_repo_insert_statement(repo_id, group_id):

    return """INSERT INTO "augur_operations"."user_repos" ("repo_id", "group_id") VALUES ({}, {});""".format(repo_id, group_id)

def get_repo_group_insert_statement(rg_id):

    return """INSERT INTO "augur_data"."repo_groups" ("repo_group_id", "rg_name", "rg_description", "rg_website", "rg_recache", "rg_last_modified", "rg_type", "tool_source", "tool_version", "data_source", "data_collection_date") VALUES ({}, 'Default Repo Group', 'The default repo group created by the schema generation script', '', 0, '2019-06-03 15:55:20', 'GitHub Organization', 'load', 'one', 'git', '2019-06-05 13:36:25');""".format(rg_id)

def get_user_insert_statement(user_id, username="bil", email="default@gmail.com", password="pass"):

    return """INSERT INTO "augur_operations"."users" ("user_id", "login_name", "login_hashword", "email", "first_name", "last_name", "admin") VALUES ({}, '{}', '{}', '{}', 'bill', 'bob', false);""".format(user_id, username, User.compute_hashsed_password(password), email)

def get_user_group_insert_statement(user_id, group_name, group_id=None):

    if group_id:
        return """INSERT INTO "augur_operations"."user_groups" ("group_id", "user_id", "name") VALUES ({}, {}, '{}');""".format(group_id, user_id, group_name)

    return """INSERT INTO "augur_operations"."user_groups" ("user_id", "name") VALUES ({}, '{}');""".format(user_id, group_name)


######## Helper Functions to get retrieve data from tables #################

def get_repos(connection, where_string=None):

    query_list = []
    query_list.append('SELECT * FROM "augur_data"."repo"')

    if where_string:
        if where_string.endswith(";"):
             query_list.append(where_string[:-1])

        query_list.append(where_string)

    query_list.append(";")

    query = s.text(" ".join(query_list))

    return connection.execute(query).fetchall()

def get_user_repos(connection):

    return connection.execute(s.text("""SELECT * FROM "augur_operations"."user_repos";""")).fetchall()


######## Helper Functions to get repos in an org #################

def get_org_repos(org_name, session):

    attempts = 0
    while attempts < 10:
        result = hit_api(session.oauths, ORG_REPOS_ENDPOINT.format(org_name), logger)

        # if result is None try again
        if not result:
            attempts += 1
            continue

        response = result.json()

        if response:
            return response

    return None

def get_org_repo_count(org_name, session):

    repos = get_org_repos(org_name, session)
    return len(repos)
