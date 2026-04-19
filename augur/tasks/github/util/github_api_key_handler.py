import httpx
import time
import random

from typing import List
from sqlalchemy.orm import Session

from augur.tasks.util.redis_list import RedisList
from augur.application.db.lib import get_value, get_worker_oauth_keys
from sqlalchemy import func 

RATE_LIMIT_URL = "https://api.github.com/rate_limit"


class NoValidKeysError(Exception):
    pass


class GithubApiKeyHandler():
    """Handles Github API key retrieval from the database and redis

    Attributes:
        logger (logging.Logger): Handles all logs
        oauth_redis_key (str): The key where the github api keys are cached in redis
        redis_key_list (RedisList): Acts like a python list, and interacts directly with the redis cache
        config_key (str): The api key that is stored in the users config table
        key: (List[str]): List of keys retrieve from database or cache
    """

    def __init__(self, logger):

        self.logger = logger

        self.oauth_redis_key = "github_oauth_keys_list"

        self.redis_key_list = RedisList(self.oauth_redis_key)

        self.config_key = self.get_config_key()

        self.keys = self.get_api_keys()

        self.logger.info(f"Retrieved {len(self.keys)} github api keys for use")

    def get_random_key(self):
        """Retrieves a random key from the list of keys

        Returns:
            A random github api key
        """

        return random.choice(self.keys)

    def get_config_key(self) -> str:
        """Retrieves the users github api key from their config table

        Returns:
            Github API key from config table
        """

        return get_value("Keys", "github_api_key")

    def get_api_keys_from_database(self) -> List[str]:
        """Retieves all github api keys from database

        Note:
            It retrieves all the keys from the database except the one defined in the users config

        Returns:
            Github api keys that are in the database
        """

        keys = get_worker_oauth_keys('github')

        filtered_keys = [item for item in keys if item != self.config_key]

        return filtered_keys

    def get_api_keys(self) -> List[str]:
        """Retrieves all valid Github API Keys

        Note:
            It checks to see if the keys are in the redis cache first.
            It removes bad keys before returning.
            If keys were taken from the database, it caches all the valid keys that were found

        Returns:
            Valid Github api keys
        """

        redis_keys = list(self.redis_key_list)

        if redis_keys:
            return redis_keys

        # Initialize keys to empty list to prevent NameError if all retries fail
        keys = []
        attempts = 0
        while attempts < 3:
            try:
                keys = self.get_api_keys_from_database()
                break
            except Exception as e:
                self.logger.warning(f"Failed to get API keys from database (attempt {attempts + 1}/3): {e}")
                time.sleep(5)
                attempts += 1

        if self.config_key is not None:
            keys += [self.config_key]

        if len(keys) == 0:
            return []
        
        keys = [key.strip() for key in keys]

        valid_keys = []
        with httpx.Client() as client:

            for key in keys:

                # removes key if it returns "Bad Credentials"
                if self.is_bad_api_key(client, key) is False:
                    valid_keys.append(key)
                else:
                    print(f"WARNING: The key '{key}' is not a valid key. Hint: If valid in past it may have expired")

        # just in case the mulitprocessing adds extra values to the list.
        # we are clearing it before we push the values we got
        self.redis_key_list.clear()

        # add all the keys to redis
        self.redis_key_list.extend(valid_keys)

        if not valid_keys:
            raise NoValidKeysError("No valid github api keys found in the config or worker oauth table")



        return valid_keys

    def is_bad_api_key(self, client: httpx.Client, oauth_key: str) -> bool:
        """Determines if a Github API is bad

        Args:
            client: makes the http requests
            oauth_key: github api key that is being tested

        Returns:
            True if key is bad. False if the key is good
        """

        headers = {'Authorization': f'token {oauth_key}'}

        data = client.request(method="GET", url=RATE_LIMIT_URL, headers=headers, timeout=180).json()

        try:
            if data["message"] == "Bad credentials":
                return True
        except KeyError:
            pass

        return False
    
    @staticmethod
    def get_key_rate_limit(client, github_key):

        headers = {'Authorization': f'token {github_key}'}

        data = client.request(method="GET", url=RATE_LIMIT_URL, headers=headers, timeout=180).json()

        if "message" in data:
            return None, None
        
        def convert_rate_limit_request(data):
            return {
            "requests_remaining": data["remaining"],
            "reset_epoch": data["reset"]
            }
        
        core_data = convert_rate_limit_request(data["resources"]["core"])
        graphql_data = convert_rate_limit_request(data["resources"]["graphql"])

        return core_data, graphql_data