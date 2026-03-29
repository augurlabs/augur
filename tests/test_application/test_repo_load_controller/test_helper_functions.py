import logging
import pytest
import sqlalchemy as s


from augur.application.db.session import DatabaseSession
from augur.tasks.github.util.github_task_session import GithubTaskSession
from tests.test_application.test_repo_load_controller.helper import *
from augur.application.db.models import Repo, RepoGroup, UserRepo, UserGroup

logger = logging.getLogger(__name__)






# def test_get_user_groups(test_db_engine):

#     clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
#     clear_tables_statement = get_repo_related_delete_statements(clear_tables)

#     try:
#         with test_db_engine.connect() as connection:

#             user_id_1 = 1
#             user_id_2 = 2
            

#             groups = [
#                 {
#                     "group_name": "test group 1",
#                     "group_id": 1
#                 },
#                 {
#                     "group_name": "test group 2",
#                     "group_id": 2
#                 },
#                 {
#                     "group_name": "test group 3",
#                     "group_id": 3
#                 },
#                 {
#                     "group_name": "test group 4",
#                     "group_id": 4
#                 },
#                 {
#                     "group_name": "test group 5",
#                     "group_id": 5
#                 }
#             ]

#             query_statements = []
#             query_statements.append(clear_tables_statement)
#             query_statements.append(get_user_insert_statement(user_id_1))

#             # add user with no user groups
#             query_statements.append(get_user_insert_statement(user_id_2, username="hello", email="hello@gmail.com"))

#             for group in groups:
#                 query_statements.append(get_user_group_insert_statement(user_id_1, group["group_name"], group["group_id"]))

#             connection.execute("".join(query_statements))

#         with GithubTaskSession(logger, test_db_engine) as session:

            

#             assert len(controller.get_user_groups(user_id_1)) == len(groups)

#             assert len(controller.get_user_groups(user_id_2)) == 0


#             with test_db_engine.connect() as connection:

#                 user_group_delete_statement = get_user_group_delete_statement()
#                 query = s.text(user_group_delete_statement)

#                 result = connection.execute(query)
 
#     finally:
#         with test_db_engine.connect() as connection:
#             connection.execute(clear_tables_statement)


# def test_get_user_group_repos(test_db_engine):

#     clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
#     clear_tables_statement = get_repo_related_delete_statements(clear_tables)

#     try:
#         with test_db_engine.connect() as connection:

#             user_id =1
#             user_id_2 = 2
#             group_id = 1
#             group_id_2 = 2
#             rg_id = 1
#             group_name = "test_group 1"
#             repo_ids = [1, 2, 3, 4, 5]
#             repo_urls = ["url1", "url2", "url3", "url4", "url5"]

#             query_statements = []
#             query_statements.append(clear_tables_statement)

#             # add user with a group that has multiple repos
#             query_statements.append(get_user_insert_statement(user_id))
#             query_statements.append(get_user_group_insert_statement(user_id, group_name, group_id))

#             # add user with a group that has no repos
#             query_statements.append(get_user_insert_statement(user_id_2, username="hello", email="hello@gmail.com"))
#             query_statements.append(get_user_group_insert_statement(user_id_2, group_name, group_id_2))

#             query_statements.append(get_repo_group_insert_statement(rg_id))
            
#             for i in range(0, len(repo_ids)):
#                 query_statements.append(get_repo_insert_statement(repo_ids[i], rg_id, repo_urls[i]))
#                 query_statements.append(get_user_repo_insert_statement(repo_ids[i], group_id))

#             connection.execute("".join(query_statements))

#         with GithubTaskSession(logger, test_db_engine) as session:

            

#             result = controller.get_user_group_repos(group_id)

#             assert len(result) == len(repo_ids)
#             assert set([repo.repo_id for repo in result]) == set(repo_ids)

#             result = controller.get_user_group_repos(group_id_2)

#             assert len(result) == 0


#             with test_db_engine.connect() as connection:

#                 user_repo_delete_statement = get_user_repo_delete_statement()
#                 query = s.text(user_repo_delete_statement)

#                 result = connection.execute(query)

#             assert len(controller.get_user_group_repos(group_id)) == 0
 
#     finally:
#         with test_db_engine.connect() as connection:
#             connection.execute(clear_tables_statement)


# def test_get_user_group_repos(test_db_engine):

#     clear_tables = ["user_repos", "user_groups", "repo", "repo_groups", "users"]
#     clear_tables_statement = get_repo_related_delete_statements(clear_tables)

#     try:
#         with test_db_engine.connect() as connection:

#             user_id =1
#             user_id_2 = 2
#             group_id = 1
#             group_id_2 = 2
#             rg_id = 1
#             group_name = "test_group 1"
#             repo_ids = [1, 2, 3, 4, 5]
#             repo_urls = ["url1", "url2", "url3", "url4", "url5"]

#             query_statements = []
#             query_statements.append(clear_tables_statement)

#             # add user with a group that has multiple repos
#             query_statements.append(get_user_insert_statement(user_id))
#             query_statements.append(get_user_group_insert_statement(user_id, group_name, group_id))

#             # add user with a group that has no repos
#             query_statements.append(get_user_insert_statement(user_id_2, username="hello", email="hello@gmail.com"))

#             query_statements.append(get_repo_group_insert_statement(rg_id))
            
#             for i in range(0, len(repo_ids)):
#                 query_statements.append(get_repo_insert_statement(repo_ids[i], rg_id, repo_urls[i]))
#                 query_statements.append(get_user_repo_insert_statement(repo_ids[i], group_id))

#             connection.execute("".join(query_statements))

#         with GithubTaskSession(logger, test_db_engine) as session:

            

#             # test user with a group that has multiple repos
#             result = controller.get_user_repo_ids(user_id)

#             assert len(result) == len(repo_ids)
#             assert set(result) == set(repo_ids)


#             # test user without any groups or repos
#             result = controller.get_user_repo_ids(user_id_2)

#             assert len(result) == 0

#             query_statements.append(get_user_group_insert_statement(user_id_2, group_name, group_id_2))


#             # test user with a group that doesn't have any repos
#             result = controller.get_user_repo_ids(user_id_2)

#             assert len(result) == 0

#             with test_db_engine.connect() as connection:

#                 user_repo_delete_statement = get_user_repo_delete_statement()
#                 query = s.text(user_repo_delete_statement)

#                 result = connection.execute(query)

#             assert len(controller.get_user_group_repos(group_id)) == 0
 
#     finally:
#         with test_db_engine.connect() as connection:
#             connection.execute(clear_tables_statement)




