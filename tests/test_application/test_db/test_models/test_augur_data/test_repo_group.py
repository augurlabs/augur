import logging
import pytest
import sqlalchemy as s

from augur.application.db.session import DatabaseSession
from tests.test_application.test_repo_load_controller.helper import *
from augur.application.db.models import RepoGroup

logger = logging.getLogger(__name__)


def test_is_valid_repo_group_id(test_db_engine):

    clear_tables = ["repo_groups"]
    clear_tables_statement = get_repo_related_delete_statements(clear_tables)

    try:

        data = {"rg_ids": [1, 2, 3], "repo_id": 1, "tool_source": "Frontend",
                "repo_url": "https://github.com/chaoss/augur"}

        with test_db_engine.connect() as connection:

            query_statements = []
            query_statements.append(clear_tables_statement)
            query_statements.append(get_repo_group_insert_statement(data["rg_ids"][0]))
            query_statements.append(get_repo_group_insert_statement(data["rg_ids"][1]))
            query_statements.append(get_repo_group_insert_statement(data["rg_ids"][2]))
            query = s.text("".join(query_statements))

            connection.execute(query)

        with DatabaseSession(logger, test_db_engine) as session:

            # valid 
            assert RepoGroup.is_valid_repo_group_id(session, data["rg_ids"][0]) is True
            assert RepoGroup.is_valid_repo_group_id(session, data["rg_ids"][1]) is True
            assert RepoGroup.is_valid_repo_group_id(session, data["rg_ids"][2]) is True

            # invalid
            assert RepoGroup.is_valid_repo_group_id(session, -1) is False
            assert RepoGroup.is_valid_repo_group_id(session, 12) is False
            assert RepoGroup.is_valid_repo_group_id(session, 11111) is False


    finally:
        with test_db_engine.connect() as connection:
            connection.execute(clear_tables_statement)

