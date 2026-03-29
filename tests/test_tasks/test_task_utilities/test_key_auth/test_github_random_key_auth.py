import pytest
import httpx
import random
import time
import logging

from augur.tasks.github.util.github_random_key_auth import GithubRandomKeyAuth
from augur.application.db.session import DatabaseSession

logger = logging.getLogger(__name__)

@pytest.fixture
def github_random_key_auth():

    session = DatabaseSession(logger)

    key_auth = GithubRandomKeyAuth(session)

    yield key_auth

    session.close()


def test_github_api_rate_limit_after_setting_key(github_random_key_auth):

    url = "https://api.github.com/rate_limit"

    with httpx.Client() as client:

        response = client.request(method="GET", url=url, auth=github_random_key_auth)

        rate_limit_data = response.json()

        assert rate_limit_data["resources"]["core"]["limit"] > 60