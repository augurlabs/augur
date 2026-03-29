import logging
import pytest
import sqlalchemy as s
from werkzeug.security import check_password_hash

from augur.application.db.session import DatabaseSession
from augur.tasks.github.util.github_task_session import GithubTaskSession
from tests.test_application.test_repo_load_controller.helper import *
from augur.application.db.models import User


logger = logging.getLogger(__name__)


def test_get_user(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            username = "user"
            user_id = 1
            email = f"{username}@gmail.com"

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_user_insert_statement(user_id, username, email))
            query = s.text("".join(query_statements))

            connection.execute(query)

        with DatabaseSession(logger, test_db_engine) as session:

            # invalid type
            assert User.get_user(session, 123) is None

            # invalid user
            assert User.get_user(session, "BestUser") is None

            # valid user
            user = User.get_user(session, username)
            assert user.user_id == user_id
            assert user.login_name == username
            assert user.email == email
  
    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)



def test_delete_user(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            user1 = {"user_id": 3, "user_name": "bare_user", "email": "bare_user@gmail.com"}
            user2 = {
                "user_id": 2, 
                "user_name": "groups_user", 
                "email": "groups_user@gmail.com", 
                "group": {
                    "group_id": 2,
                    "group_name": "second_group"
                }
            }
            user3 = {
                "user_id": 1, 
                "user_name": "full_user", 
                "email": "full_user@gmail.com",
                "group": {
                    "group_name": "group", 
                    "group_id": 1,
                    "repo": {
                        "repo_id": 1,
                        "repo_group_id": 1
                    }
                }
            }
            
            query_statements = []
            query_statements.append(clear_tables_statement)
             
            # create bare user
            query_statements.append(get_user_insert_statement(user1["user_id"], user1["user_name"], user1["email"]))

            # # create user with groups
            query_statements.append(get_user_insert_statement(user2["user_id"], user2["user_name"], user2["email"]))
            query_statements.append(get_user_group_insert_statement(user2["user_id"], user2["group"]["group_name"]))

            # # create user with groups and repos
            query_statements.append(get_repo_group_insert_statement(user3["group"]["repo"]["repo_group_id"]))
            query_statements.append(get_repo_insert_statement(user3["group"]["repo"]["repo_id"], user3["group"]["repo"]["repo_group_id"]))
            query_statements.append(get_user_insert_statement(user3["user_id"], user3["user_name"], user3["email"]))
            query_statements.append(get_user_group_insert_statement(user3["user_id"], user3["group"]["group_name"], user3["group"]["group_id"]))
            query_statements.append(get_user_repo_insert_statement(user3["group"]["repo"]["repo_id"], user3["group"]["group_id"]))

            query = s.text("".join(query_statements))

            connection.execute(query)

        with DatabaseSession(logger, test_db_engine) as session:
            
            # delete user with no groups or repos
            user1_obj = session.query(User).filter(User.user_id == user1["user_id"]).first()
            assert user1_obj.delete(session)[0] is True

            # # delete user with groups, but no repos
            user2_obj = session.query(User).filter(User.user_id == user2["user_id"]).first()
            assert user2_obj.delete(session)[0] is True
            
            # # delete user with groups and repos
            user3_obj = session.query(User).filter(User.user_id == user3["user_id"]).first()
            assert user3_obj.delete(session)[0] is True

            
    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)



def test_update_user_password(test_db_engine):

    clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:
        with test_db_engine.connect() as connection:

            username = "user"
            user_id = 1
            email = f"{username}@gmail.com"
            password = "pass"
            new_password = "be++erp@ssw0rd"

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_user_insert_statement(user_id, username, email, password))
            query = s.text("".join(query_statements))

            connection.execute(query)

        with DatabaseSession(logger, test_db_engine) as session:

            user = session.query(User).filter(User.user_id == 1).first()

            # invalid passowrd
            assert user.update_password(session, "wrong passowrd", new_password)[0] is False

            # invalid types
            assert user.update_password(session, 1, new_password)[0] is False
            assert user.update_password(session, password, 1)[0] is False

            # invalid passowrd
            assert user.update_password(session, password, new_password)[0] is True

        with DatabaseSession(logger, test_db_engine) as session:

            user = session.query(User).filter(User.user_id == 1).first()
            assert check_password_hash(user.login_hashword, new_password)

  
    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)


