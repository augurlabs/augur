import logging
import pytest
import sqlalchemy as s

from augur.tasks.util.worker_util import *

logger = logging.getLogger(__name__)

def test_remove_duplicates_by_uniques(test_db_engine):

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    data_2 = {"cntrb_login": "amazing", "gh_user_id": 1700, "gh_login": "hello", "cntrb_id": "01003f7a-8500-0000-0000-000123002000"}
    data_3 = {"cntrb_login": "cool_guy", "gh_user_id": 230, "gh_login": "lame_guy", "cntrb_id": "01003f7a-8511-0000-0000-000123875000"}
    data_4 = {"cntrb_login": "great", "gh_user_id": 230, "gh_login": "boring", "cntrb_id": "01003f7a-8511-0000-0000-000123000000"}
    all_data = [data_4, data_1, data_3, data_1, data_2, data_1, data_3, data_4, data_2]

    assert len(remove_duplicates_by_uniques(all_data, ["cntrb_id"])) == 4

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000123002000"}
    data_2 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "hello", "cntrb_id": "01003f7a-8500-0000-0000-000123002000"}

    assert len(remove_duplicates_by_uniques([data_1, data_2], ["cntrb_id", "gh_user_id"])) == 1

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    data_2 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "hello", "cntrb_id": "01003f7a-8500-0000-0000-000123002000"}
    data_3 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "hello", "cntrb_id": "01003f7a-8500-0000-0000-000123042000"}

    assert len(remove_duplicates_by_uniques([data_1, data_2], ["cntrb_id", "gh_user_id", "gh_login"])) == 2



    