import unittest

from augur.tasks.github.util.github_data_access import (
    ResourceGoneException,
    UrlNotFoundException,
    GithubDataAccess,
)


class TestDecideRetryPolicy(unittest.TestCase):
    """Unit tests for GithubDataAccess._decide_retry_policy.

    This function controls whether a failed request is retried.  Introduced in
    commit 04ef1ef, it must return False for permanent error conditions
    (ResourceGoneException, UrlNotFoundException) so Celery does not waste
    retry attempts on resources that are intentionally unavailable.
    """

    def test_resource_gone_exception_is_not_retried(self):
        """HTTP 410 Gone (e.g. issues disabled) must not be retried."""
        result = GithubDataAccess._decide_retry_policy(ResourceGoneException())
        self.assertFalse(result)

    def test_url_not_found_exception_is_not_retried(self):
        """HTTP 404 Not Found must not be retried."""
        result = GithubDataAccess._decide_retry_policy(UrlNotFoundException())
        self.assertFalse(result)

    def test_generic_exception_is_retried(self):
        """Transient errors (network issues, timeouts) must be retried."""
        result = GithubDataAccess._decide_retry_policy(Exception("connection reset"))
        self.assertTrue(result)

    def test_connection_error_is_retried(self):
        """ConnectionError is a transient error and must be retried."""
        result = GithubDataAccess._decide_retry_policy(ConnectionError())
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
