import logging
import unittest
from unittest.mock import MagicMock, patch

from celery.exceptions import Ignore

from augur.tasks.github.util.github_data_access import ResourceGoneException


logger = logging.getLogger(__name__)


class TestCollectIssuesResourceGone(unittest.TestCase):
    """Unit tests for collect_issues handling of ResourceGoneException.

    When a repository has GitHub Issues intentionally disabled the GitHub API
    returns HTTP 410 Gone, which raises ResourceGoneException.  The Celery task
    must convert that into celery.exceptions.Ignore so that the enclosing
    chord/chain is not aborted and the rest of the repo's data (commits, PRs,
    contributors, releases) is still collected.
    """

    @patch("augur.tasks.github.issues.get_batch_size", return_value=1000)
    @patch("augur.tasks.github.issues.GithubRandomKeyAuth")
    @patch("augur.tasks.github.issues.GithubDataAccess")
    @patch("augur.tasks.github.issues.get_repo_by_repo_git")
    def test_raises_ignore_when_issues_disabled_on_page_count(
        self,
        mock_get_repo,
        mock_gda_class,
        mock_key_auth_class,
        mock_get_batch_size,
    ):
        """ResourceGoneException during get_resource_page_count must become Ignore."""

        mock_repo = MagicMock()
        mock_repo.repo_id = 1
        mock_get_repo.return_value = mock_repo

        mock_gda = MagicMock()
        mock_gda.get_resource_page_count.side_effect = ResourceGoneException(
            "Issues are disabled for this repository"
        )
        mock_gda_class.return_value = mock_gda

        from augur.tasks.github.issues import collect_issues

        with self.assertRaises(Ignore):
            collect_issues.run("https://github.com/example/no-issues-repo", full_collection=True)

    @patch("augur.tasks.github.issues.get_batch_size", return_value=1000)
    @patch("augur.tasks.github.issues.GithubRandomKeyAuth")
    @patch("augur.tasks.github.issues.GithubDataAccess")
    @patch("augur.tasks.github.issues.get_repo_by_repo_git")
    def test_raises_ignore_when_issues_disabled_during_pagination(
        self,
        mock_get_repo,
        mock_gda_class,
        mock_key_auth_class,
        mock_get_batch_size,
    ):
        """ResourceGoneException raised during pagination must also become Ignore."""

        mock_repo = MagicMock()
        mock_repo.repo_id = 1
        mock_get_repo.return_value = mock_repo

        mock_gda = MagicMock()
        mock_gda.get_resource_page_count.return_value = 1
        mock_gda.paginate_resource.side_effect = ResourceGoneException(
            "Issues are disabled for this repository"
        )
        mock_gda_class.return_value = mock_gda

        from augur.tasks.github.issues import collect_issues

        with self.assertRaises(Ignore):
            collect_issues.run("https://github.com/example/no-issues-repo", full_collection=True)

    @patch("augur.tasks.github.issues.get_batch_size", return_value=1000)
    @patch("augur.tasks.github.issues.GithubRandomKeyAuth")
    @patch("augur.tasks.github.issues.GithubDataAccess")
    @patch("augur.tasks.github.issues.get_repo_by_repo_git")
    def test_unrelated_exception_returns_minus_one(
        self,
        mock_get_repo,
        mock_gda_class,
        mock_key_auth_class,
        mock_get_batch_size,
    ):
        """Unrelated exceptions must not be swallowed — existing -1 path stays intact."""

        mock_repo = MagicMock()
        mock_repo.repo_id = 1
        mock_get_repo.return_value = mock_repo

        mock_gda = MagicMock()
        mock_gda.get_resource_page_count.side_effect = ConnectionError("Network unreachable")
        mock_gda_class.return_value = mock_gda

        from augur.tasks.github.issues import collect_issues

        result = collect_issues.run("https://github.com/example/some-repo", full_collection=True)
        self.assertEqual(result, -1)


class TestCollectEventsResourceGone(unittest.TestCase):
    """Unit tests for collect_events handling of ResourceGoneException.

    The issues/events endpoint returns 410 when Issues are disabled on a repo.
    collect_events must raise Ignore rather than failing, so that the secondary
    collection group keeps running for the rest of the repo's data.
    """

    @patch("augur.tasks.github.events.GithubRandomKeyAuth")
    @patch("augur.tasks.github.events.GithubDataAccess")
    @patch("augur.tasks.github.events.get_owner_repo", return_value=("example", "no-issues-repo"))
    def test_raises_ignore_when_issues_endpoint_gone(
        self,
        mock_get_owner_repo,
        mock_gda_class,
        mock_key_auth_class,
    ):
        """ResourceGoneException from bulk_events_collection_endpoint_contains_all_data
        must be caught and converted to Ignore."""

        mock_gda = MagicMock()
        mock_gda.get_resource_page_count.side_effect = ResourceGoneException(
            "Issues are disabled for this repository"
        )
        mock_gda_class.return_value = mock_gda

        from augur.tasks.github.events import collect_events

        with self.assertRaises(Ignore):
            collect_events.run("https://github.com/example/no-issues-repo", full_collection=True)


class TestCollectMessagesResourceGone(unittest.TestCase):
    """Unit tests for collect_github_messages handling of ResourceGoneException.

    The issues/comments endpoint returns 410 when Issues are disabled.
    collect_github_messages must raise Ignore rather than failing.
    """

    @patch("augur.tasks.github.messages.GithubTaskManifest")
    def test_raises_ignore_when_issues_comments_gone(self, mock_manifest_class):
        """ResourceGoneException raised during message retrieval must become Ignore."""

        mock_manifest = MagicMock()
        mock_manifest.__enter__ = MagicMock(return_value=mock_manifest)
        mock_manifest.__exit__ = MagicMock(return_value=False)

        mock_repo_obj = MagicMock()
        mock_repo_obj.repo_id = 1
        mock_manifest.augur_db.session.query.return_value.filter.return_value.one.return_value = mock_repo_obj

        mock_manifest_class.return_value = mock_manifest

        with patch("augur.tasks.github.messages.is_repo_small", return_value=True), \
             patch("augur.tasks.github.messages.fast_retrieve_all_pr_and_issue_messages",
                   side_effect=ResourceGoneException("Issues are disabled for this repository")):

            from augur.tasks.github.messages import collect_github_messages

            with self.assertRaises(Ignore):
                collect_github_messages.run(
                    "https://github.com/example/no-issues-repo", full_collection=True
                )


if __name__ == "__main__":
    unittest.main()
