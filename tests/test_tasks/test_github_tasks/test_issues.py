import logging
import unittest
from unittest.mock import MagicMock, patch

from celery.exceptions import Ignore

from augur.tasks.github.util.github_data_access import ResourceGoneException


logger = logging.getLogger(__name__)


class TestCollectIssuesResourceGone(unittest.TestCase):
    """Unit tests for collect_issues handling of ResourceGoneException.

    Covers the case where a repository has GitHub Issues intentionally disabled
    (GitHub returns HTTP 410 Gone). The task must raise celery.exceptions.Ignore
    so that Celery marks it as skipped rather than failed, preventing cascade
    failure of the enclosing chord/chain for that repo.
    """

    @patch("augur.tasks.github.issues.get_batch_size", return_value=1000)
    @patch("augur.tasks.github.issues.GithubRandomKeyAuth")
    @patch("augur.tasks.github.issues.GithubDataAccess")
    @patch("augur.tasks.github.issues.get_repo_by_repo_git")
    def test_raises_ignore_when_issues_disabled(
        self,
        mock_get_repo,
        mock_gda_class,
        mock_key_auth_class,
        mock_get_batch_size,
    ):
        """When the GitHub API returns 410 for an issues-disabled repo,
        collect_issues must raise Ignore instead of propagating an error."""

        repo_git = "https://github.com/example/no-issues-repo"

        mock_repo = MagicMock()
        mock_repo.repo_id = 1
        mock_get_repo.return_value = mock_repo

        mock_gda_instance = MagicMock()
        mock_gda_instance.get_resource_page_count.side_effect = ResourceGoneException(
            "Issues are disabled for this repository"
        )
        mock_gda_class.return_value = mock_gda_instance

        # Import here to avoid triggering Celery app setup at module load time
        from augur.tasks.github.issues import collect_issues

        with self.assertRaises(Ignore):
            collect_issues.run(repo_git, full_collection=True)

    @patch("augur.tasks.github.issues.get_batch_size", return_value=1000)
    @patch("augur.tasks.github.issues.GithubRandomKeyAuth")
    @patch("augur.tasks.github.issues.GithubDataAccess")
    @patch("augur.tasks.github.issues.get_repo_by_repo_git")
    def test_raises_ignore_when_resource_gone_during_pagination(
        self,
        mock_get_repo,
        mock_gda_class,
        mock_key_auth_class,
        mock_get_batch_size,
    ):
        """ResourceGoneException raised during pagination (after page count succeeds)
        must also be caught and converted to Ignore."""

        repo_git = "https://github.com/example/no-issues-repo"

        mock_repo = MagicMock()
        mock_repo.repo_id = 1
        mock_get_repo.return_value = mock_repo

        mock_gda_instance = MagicMock()
        mock_gda_instance.get_resource_page_count.return_value = 1
        mock_gda_instance.paginate_resource.side_effect = ResourceGoneException(
            "Issues are disabled for this repository"
        )
        mock_gda_class.return_value = mock_gda_instance

        from augur.tasks.github.issues import collect_issues

        with self.assertRaises(Ignore):
            collect_issues.run(repo_git, full_collection=True)

    @patch("augur.tasks.github.issues.get_batch_size", return_value=1000)
    @patch("augur.tasks.github.issues.GithubRandomKeyAuth")
    @patch("augur.tasks.github.issues.GithubDataAccess")
    @patch("augur.tasks.github.issues.get_repo_by_repo_git")
    def test_non_resource_gone_exception_still_returns_minus_one(
        self,
        mock_get_repo,
        mock_gda_class,
        mock_key_auth_class,
        mock_get_batch_size,
    ):
        """Unrelated exceptions must not be swallowed — they should return -1
        as before, leaving the existing error-handling path intact."""

        repo_git = "https://github.com/example/some-repo"

        mock_repo = MagicMock()
        mock_repo.repo_id = 1
        mock_get_repo.return_value = mock_repo

        mock_gda_instance = MagicMock()
        mock_gda_instance.get_resource_page_count.side_effect = ConnectionError(
            "Network unreachable"
        )
        mock_gda_class.return_value = mock_gda_instance

        from augur.tasks.github.issues import collect_issues

        result = collect_issues.run(repo_git, full_collection=True)
        self.assertEqual(result, -1)


if __name__ == "__main__":
    unittest.main()
