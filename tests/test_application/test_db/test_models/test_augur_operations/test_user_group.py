import logging
import pytest
import sqlalchemy as s

from augur.application.db.session import DatabaseSession
from tests.test_application.test_repo_load_controller.helper import *
from augur.application.db.models import UserGroup

logger = logging.getLogger(__name__)


def test_add_user_group(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            data = {
                "users": [
                    {
                        "id": 0,
                        "username": "user 1",
                        "email": "email 1"
                    },
                    {
                        "id": 1,
                        "username": "user 2",
                        "email": "email 2"
                    }
                ],
                "group_names": ["test_group", "test_group_2"]}

            query_statements = []
            query_statements.append(clear_tables_statement)

            for user in data["users"]:
                query_statements.append(get_user_insert_statement(user["id"], user["username"], user["email"]))
            
            query = s.text("".join(query_statements))

            connection.execute(query)

        with DatabaseSession(logger, test_db_engine) as session:

            # add valid group to user 0
            assert UserGroup.insert(session, data["users"][0]["id"], data["group_names"][0])[0] is True

            # add group again to user 0 ... should be 1 group row still
            assert UserGroup.insert(session, data["users"][0]["id"], data["group_names"][0])[0] is False

            # add another valid group to user 0
            assert UserGroup.insert(session, data["users"][0]["id"], data["group_names"][1])[0] is True

            # add same group to user 1
            assert UserGroup.insert(session, data["users"][1]["id"], data["group_names"][0])[0] is True


            # add with invalid user id
            assert UserGroup.insert(session, 130000, data["group_names"][0])[0] is False

            # pass invalid tpyes
            assert UserGroup.insert(session, "130000", data["group_names"][0])[0] is False
            assert UserGroup.insert(session, data["users"][0]["id"], 133333)[0] is False


            # end result
            # 3 groups in table
            # 1 row for user 1
            # 2 rows for user 0


        with test_db_engine.connect() as connection:

            query = s.text("""SELECT * FROM "augur_operations"."user_groups";""")

            result = connection.execute(query).fetchall()
            assert result is not None
            assert len(result) == 3

            query = s.text("""SELECT * FROM "augur_operations"."user_groups" WHERE "user_id"={};""".format(data["users"][0]["id"]))

            result = connection.execute(query).fetchall()
            assert result is not None
            assert len(result) == 2

            query = s.text("""SELECT * FROM "augur_operations"."user_groups" WHERE "user_id"={};""".format(data["users"][1]["id"]))

            result = connection.execute(query).fetchall()
            assert result is not None
            assert len(result) == 1


    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)



def test_convert_group_name_to_id(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            user_id =1

            groups = [
                {
                    "group_name": "test group 1",
                    "group_id": 1
                },
                {
                    "group_name": "test group 2",
                    "group_id": 2
                },
                {
                    "group_name": "test group 3",
                    "group_id": 3
                },
            ]

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_user_insert_statement(user_id))

            for group in groups:
                query_statements.append(get_user_group_insert_statement(user_id, group["group_name"], group["group_id"]))

            connection.execute("".join(query_statements))

        with DatabaseSession(logger, test_db_engine) as session:

            for group in groups:
                assert UserGroup.convert_group_name_to_id(session, user_id, group["group_name"]) == group["group_id"]

            # test invalid group name 
            assert UserGroup.convert_group_name_to_id(session, user_id, "hello") is None

            # test invalid user id 
            assert UserGroup.convert_group_name_to_id(session, user_id*2, groups[0]["group_name"]) is None

            # test invalid types
            assert UserGroup.convert_group_name_to_id(session, user_id, 5) is None
            assert UserGroup.convert_group_name_to_id(session, "5", groups[0]["group_name"]) is None

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)


def test_remove_user_group(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            user_id =1
            repo_id = 1
            rg_id = 1

            groups = [
                {
                    "group_name": "test group 1",
                    "group_id": 1
                },
                {
                    "group_name": "test group 2",
                    "group_id": 2
                },
                {
                    "group_name": "test group 3",
                    "group_id": 3
                },
                {
                    "group_name": "test group 4",
                    "group_id": 4
                },
                {
                    "group_name": "test group 5",
                    "group_id": 5
                }
            ]

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_user_insert_statement(user_id))

            for group in groups:
                query_statements.append(get_user_group_insert_statement(user_id, group["group_name"], group["group_id"]))

            query_statements.append(get_repo_group_insert_statement(rg_id))
            query_statements.append(get_repo_insert_statement(repo_id, rg_id))
            query_statements.append(get_user_repo_insert_statement(repo_id, groups[0]["group_id"]))

            connection.execute("".join(query_statements))

        with DatabaseSession(logger, test_db_engine) as session:

            # try to delete group that doesn't exist
            assert UserGroup.delete(session, user_id, "hello")[0] is False

            i = 0
            while(i < len(groups)-2):
                assert UserGroup.delete(session, user_id, groups[i]["group_name"])[0] is True
                i += 1

            with test_db_engine.connect() as connection:

                query = s.text("""SELECT * FROM "augur_operations"."user_groups";""")

                result = connection.execute(query).fetchall()
                assert result is not None
                assert len(result) == len(groups)-i


            while(i < len(groups)):

                assert UserGroup.delete(session, user_id, groups[i]["group_name"])[0] is True
                i += 1

            with test_db_engine.connect() as connection:

                query = s.text("""SELECT * FROM "augur_operations"."user_groups";""")

                result = connection.execute(query).fetchall()
                assert result is not None
                assert len(result) == 0

    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)
