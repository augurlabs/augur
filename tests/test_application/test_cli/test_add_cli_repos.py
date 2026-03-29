import pytest
import logging

from tests.test_application.test_repo_load_controller.helper import *
from augur.tasks.github.util.github_task_session import GithubTaskSession
from augur.util.repo_load_controller import RepoLoadController, CLI_USER_ID

DEFAULT_REPO_GROUP_ID = 1
VALID_ORG = {"org": "CDCgov", "repo_count": 249}



logger = logging.getLogger(__name__)


def test_add_cli_repos_with_invalid_repo_group_id(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            data = {"user_id": CLI_USER_ID, "repo_group_id": 5, "org_name": "operate-first", "repo_name": "operate-first-twitter", "user_group_name": "test_group", "user_group_id": 1}
            url = f"https://github.com/{data['org_name']}/{data['repo_name']}"

            query_statements = []
            query_statements.append(clear_tables_statement)

            connection.execute("".join(query_statements))

        add_keys_to_test_db(test_db_engine)

        with GithubTaskSession(logger, test_db_engine) as session:

            repo_data = {"url": url, "repo_group_id": 5}

            controller = RepoLoadController(session)
            result = controller.add_cli_repo(repo_data)
            assert result["status"] == f"Invalid repo group id specified for {repo_data['url']}, skipping."

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)


def test_add_cli_repos_with_duplicates(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            data = {"user_id": CLI_USER_ID, "repo_group_id": 5, "org_name": "operate-first", "repo_name": "operate-first-twitter", "user_group_name": "test_group", "user_group_id": 1}
            url = f"https://github.com/{data['org_name']}/{data['repo_name']}"

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["repo_group_id"]))
            query_statements.append(get_user_insert_statement(data["user_id"]))
            query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_name"], data["user_group_id"]))

            connection.execute("".join(query_statements))

        add_keys_to_test_db(test_db_engine)

        with GithubTaskSession(logger, test_db_engine) as session:

            repo_data = {"url": url, "repo_group_id": data["repo_group_id"]}

            controller = RepoLoadController(session)
            controller.add_cli_repo(repo_data)
            controller.add_cli_repo(repo_data)

        with test_db_engine.connect() as connection:

            result = get_repos(connection)

            assert result is not None
            assert len(result) == 1
            assert dict(result[0])["repo_git"] == url

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)


def test_add_cli_org_with_valid_org(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            data = {"user_id": CLI_USER_ID, "repo_group_id": 5, "org_name": VALID_ORG["org"], "user_group_name": "test_group", "user_group_id": 1}

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["repo_group_id"]))
            query_statements.append(get_user_insert_statement(data["user_id"]))
            query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_name"], data["user_group_id"]))

            connection.execute("".join(query_statements))

        repo_count = None

        add_keys_to_test_db(test_db_engine)

        with GithubTaskSession(logger, test_db_engine) as session:

            controller = RepoLoadController(session)

            result = controller.add_cli_org(data["org_name"])

            assert result["status"] == "Org added"
            
            result2 = controller.add_cli_org("Invalid org")
            assert result2["status"] == "No organization found"


        with test_db_engine.connect() as connection:

            result = get_repos(connection)
            assert result is not None
            assert len(result) == VALID_ORG["repo_count"]

            user_repo_result = get_user_repos(connection)
            assert user_repo_result is not None
            assert len(user_repo_result) == VALID_ORG["repo_count"]

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)

    



