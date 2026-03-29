import logging
import os
import json
import httpx
import pytest
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

from augur.tasks.github.util.github_api_key_handler import GithubApiKeyHandler
from augur.application.db.session import DatabaseSession
from augur.tasks.init.redis_connection import get_redis_connection

@pytest.fixture
def httpx_client():

    with httpx.Client() as client:

        yield client

@pytest.fixture
def key_handler(test_db_session):

    redis = get_redis_connection()
    
    redis.flushdb()

    yield GithubApiKeyHandler(logger)

def test_get_config_key(key_handler, test_db_engine):

    try:
        data = {"github_api_key": "asdfdfkey"}
        with test_db_engine.connect() as connection:

            query = text("""INSERT INTO "augur_operations"."config" ("id", "section_name", "setting_name", "value", "type") VALUES (3, 'Keys', 'github_api_key', :github_api_key, 'str');""")

            connection.execute(query, **data)

        config_key = key_handler.get_config_key()

        assert config_key == data["github_api_key"]
    
    finally:
        with test_db_engine.connect() as connection:
            connection.execute("""DELETE FROM augur_operations.config""")

def test_get_config_key_with_none_specified(key_handler, test_db_engine):

    config_key = key_handler.get_config_key()

    assert config_key == None


def test_get_api_keys_from_database(key_handler, test_db_engine):

    # to make sure that it doensn't add the config key twice, if the config key is also in the worker_oauth table
    key_handler.config_key = "asdfdfkey"

    try:
        keys = ["asdfdfkey", "jloire", "zdfdr", "asdrxer"]
        data = [{"api_key": key} for key in keys]
        with test_db_engine.connect() as connection:

            for value in data:

                query = text("""INSERT INTO "augur_operations"."worker_oauth" ("name", "consumer_key", "consumer_secret", "access_token", "access_token_secret", "repo_directory", "platform") VALUES ('test_key', '0', '0', :api_key, '0', NULL, 'github');""")

                connection.execute(query, **value)

        db_keys = key_handler.get_api_keys_from_database()

        assert type(db_keys) == list
        assert len(db_keys) == 3
        
        for key in db_keys:
            assert key in keys

    finally:
        with test_db_engine.connect() as connection:
            connection.execute("""DELETE FROM augur_operations.worker_oauth""")

api_key_list = ["asdfdfkey", "jloire", "zdfdr", "asdrxer"]
@pytest.mark.parametrize("api_key", api_key_list)
def test_is_bad_api_key(key_handler, httpx_client, api_key):

    assert key_handler.is_bad_api_key(httpx_client, api_key) == True


def test_get_api_keys(key_handler, test_db_engine):

    # to make sure that it doensn't add the config key twice, if the config key is also in the worker_oauth table
    # we could use get_config_key, but that would make the test unreliable
    config_key = "asdfdfkey"
    key_handler.config_key = config_key

    try:
        keys = ["asdfdfkey", "jloire", "zdfdr", "asdrxer"]
        data = [{"api_key": key} for key in keys]
        with test_db_engine.connect() as connection:

            for value in data:

                query = text("""INSERT INTO "augur_operations"."worker_oauth" ("name", "consumer_key", "consumer_secret", "access_token", "access_token_secret", "repo_directory", "platform") VALUES ('test_key', '0', '0', :api_key, '0', NULL, 'github');""")

                connection.execute(query, **value)

        db_keys = key_handler.get_api_keys()

        assert type(db_keys) == list
        assert len(db_keys) == 0

    finally:
        with test_db_engine.connect() as connection:
            connection.execute("""DELETE FROM augur_operations.worker_oauth""")