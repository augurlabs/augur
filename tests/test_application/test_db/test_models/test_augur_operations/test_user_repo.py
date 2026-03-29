import logging
import pytest
import sqlalchemy as s


from augur.application.db.session import DatabaseSession
from augur.tasks.github.util.github_task_session import GithubTaskSession
from tests.test_application.test_repo_load_controller.helper import *
from augur.application.db.models import UserRepo

logger = logging.getLogger(__name__)
VALID_ORG = {"org": "CDCgov", "repo_count": 249}
DEFAULT_REPO_GROUP_ID = 1


def test_add_repo_to_user_group(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            data = {"repo_ids": [1, 2, 3], "repo_urls":["url 1", "url2", "url3"], "user_id": 2, "user_repo_group_id": 1, "user_group_ids": [1, 2], "user_group_names": ["test_group", "test_group_2"]}

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["user_repo_group_id"]))

            for i in range(0, len(data["repo_ids"])):
                query_statements.append(get_repo_insert_statement(data["repo_ids"][i], data["user_repo_group_id"], data["repo_urls"][i]))

            query_statements.append(get_user_insert_statement(data["user_id"]))

            for i in range(0, len(data["user_group_ids"])):
                query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_names"][i], data["user_group_ids"][i]))
            
            query = s.text("".join(query_statements))

            connection.execute(query)

        with DatabaseSession(logger, test_db_engine) as session:

            # add valid repo to group 0
            assert UserRepo.insert(session, data["repo_ids"][0], data["user_group_ids"][0]) is True

            # add repo again to group 0 ... should be 1 repo row still
            assert UserRepo.insert(session, data["repo_ids"][0], data["user_group_ids"][0]) is True

            # add another valid repo to group 0
            assert UserRepo.insert(session, data["repo_ids"][1], data["user_group_ids"][0]) is True

            # add same repo to group 1
            assert UserRepo.insert(session, data["repo_ids"][0], data["user_group_ids"][1]) is True

            # add different repo to group 1
            assert UserRepo.insert(session, data["repo_ids"][2], data["user_group_ids"][1]) is True

            # add with invalid repo id
            assert UserRepo.insert(session, 130000, data["user_group_ids"][1]) is False

            # add with invalid group_id
            assert UserRepo.insert(session, data["repo_ids"][0], 133333) is False

            # pass invalid tpyes
            assert UserRepo.insert(session, "130000", data["user_group_ids"][1]) is False
            assert UserRepo.insert(session, data["repo_ids"][0], "133333") is False


            # end result
            # 4 rows in table
            # 2 rows in each group


        with test_db_engine.connect() as connection:

            query = s.text("""SELECT * FROM "augur_operations"."user_repos";""")
            # WHERE "group_id"=:user_group_id AND "repo_id"=:repo_id

            result = connection.execute(query).fetchall()
            assert result is not None
            assert len(result) == 4


            query = s.text("""SELECT * FROM "augur_operations"."user_repos" WHERE "group_id"={};""".format(data["user_group_ids"][0]))

            result = connection.execute(query).fetchall()
            assert result is not None
            assert len(result) == 2


            query = s.text("""SELECT * FROM "augur_operations"."user_repos" WHERE "group_id"={};""".format(data["user_group_ids"][0]))

            result = connection.execute(query).fetchall()
            assert result is not None
            assert len(result) == 2

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)


def test_add_frontend_repos_with_invalid_repo(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            url = "https://github.com/chaoss/whitepaper"

            data = {"user_id": 2, "repo_group_id": 5, "user_group_name": "test_group", "user_group_id": 1}

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["repo_group_id"]))
            query_statements.append(get_user_insert_statement(data["user_id"]))
            query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_name"], data["user_group_id"]))

            connection.execute("".join(query_statements))

        add_keys_to_test_db(test_db_engine)

        with GithubTaskSession(logger, test_db_engine) as session:

            result = UserRepo.add_github_repo(session, url, data["user_id"], data["user_group_name"])

            assert result[1]["status"] == "Invalid repo"

        with test_db_engine.connect() as connection:

            result = get_repos(connection)
            assert result is not None
            assert len(result) == 0

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)


def test_add_frontend_repos_with_duplicates(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            url = "https://github.com/operate-first/operate-first-twitter"

            data = {"user_id": 2, "repo_group_id": DEFAULT_REPO_GROUP_ID, "user_group_name": "test_group", "user_group_id": 1}

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["repo_group_id"]))
            query_statements.append(get_user_insert_statement(data["user_id"]))
            query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_name"], data["user_group_id"]))

            connection.execute("".join(query_statements))
        
        add_keys_to_test_db(test_db_engine)

        with GithubTaskSession(logger, test_db_engine) as session:

            result = UserRepo.add_github_repo(session, url, data["user_id"], data["user_group_name"])
            result2 = UserRepo.add_github_repo(session, url, data["user_id"], data["user_group_name"])

            # add repo with invalid group name
            result3 = UserRepo.add_github_repo(session, url, data["user_id"], "Invalid group name")

            assert result[1]["status"] == "Repo Added"
            assert result2[1]["status"] == "Repo Added"
            assert result3[1]["status"] == "Invalid group name"

        with test_db_engine.connect() as connection:

            result = get_repos(connection)
            assert result is not None
            assert len(result) == 1
            assert dict(result[0])["repo_git"] == url

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)


def test_remove_frontend_repo(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            url = "https://github.com/operate-first/operate-first-twitter"

            data = {"user_id": 2, "repo_id": 5, "repo_group_id": DEFAULT_REPO_GROUP_ID, "user_group_name": "test_group", "user_group_id": 1}

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["repo_group_id"]))
            query_statements.append(get_user_insert_statement(data["user_id"]))
            query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_name"], data["user_group_id"]))
            query_statements.append(get_repo_insert_statement(data["repo_id"], data["repo_group_id"], repo_url="url"))
            query_statements.append(get_user_repo_insert_statement(data["repo_id"], data["user_group_id"]))
            
            connection.execute("".join(query_statements))
        
        add_keys_to_test_db(test_db_engine)

        with GithubTaskSession(logger, test_db_engine) as session:

            # remove valid user repo
            result = UserRepo.delete(session, data["repo_id"], data["user_id"], data["user_group_name"])
            assert result[1]["status"] == "Repo Removed"

            with test_db_engine.connect() as connection:

                repos = get_user_repos(connection)
                assert len(repos) == 0
        
            # remove invalid group
            result = UserRepo.delete(session, data["repo_id"], data["user_id"], "invalid group")
            assert result[1]["status"] == "Invalid group name"

            # pass invalid data types
            result = UserRepo.delete(session, "5", data["user_id"], data["user_group_name"])
            assert result[1]["status"] == "Invalid types"

            result = UserRepo.delete(session, data["repo_id"], "1", data["user_group_name"])
            assert result[1]["status"] == "Invalid types"

            result = UserRepo.delete(session, data["repo_id"], data["user_id"], 5)
            assert result[1]["status"] == "Invalid types"

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)



def test_add_frontend_org_with_invalid_org(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:

        data = {"user_id": 2, "repo_group_id": DEFAULT_REPO_GROUP_ID, "org_name": "chaosssss", "user_group_name": "test_group", "user_group_id": 1}

        with test_db_engine.connect() as connection:

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["repo_group_id"]))
            query_statements.append(get_user_insert_statement(data["user_id"]))
            query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_name"], data["user_group_id"]))

            connection.execute("".join(query_statements))

        add_keys_to_test_db(test_db_engine)
        with GithubTaskSession(logger, test_db_engine) as session:

            url = f"https://github.com/{data['org_name']}/"
            result = UserRepo.add_github_org_repos(session, url, data["user_id"], data["user_group_name"])
            assert result[1]["status"] == "Invalid owner url"

            # test with invalid group name
            result = UserRepo.add_github_org_repos(session, url, data["user_id"], "Invalid group name")
            assert result[1]["status"] == "Invalid group name"

        with test_db_engine.connect() as connection:

            result = get_repos(connection)
            assert result is not None
            assert len(result) == 0

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)



def test_add_frontend_org_with_valid_org(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users", "config"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            data = {"user_id": 2, "repo_group_id": DEFAULT_REPO_GROUP_ID, "org_name": VALID_ORG["org"], "user_group_name": "test_group", "user_group_id": 1}

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["repo_group_id"]))
            query_statements.append(get_user_insert_statement(data["user_id"]))
            query_statements.append(get_user_group_insert_statement(data["user_id"], data["user_group_name"], data["user_group_id"]))

            connection.execute("".join(query_statements))

        add_keys_to_test_db(test_db_engine)

        with GithubTaskSession(logger, test_db_engine) as session:

            url = "https://github.com/{}/".format(data["org_name"])
            result = UserRepo.add_github_org_repos(session, url, data["user_id"], data["user_group_name"])
            assert result[1]["status"] == "Org repos added"

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
