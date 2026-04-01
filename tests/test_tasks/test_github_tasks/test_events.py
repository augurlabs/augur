from unittest.mock import MagicMock

from augur.tasks.github.events import BulkGithubEventCollection


def _make_pr_event(pr_number):
    return {
        "issue": {
            "id": 1,
            "pull_request": {
                "url": f"https://api.github.com/repos/owner/repo/pulls/{pr_number}"
            },
        },
        "actor": None,
    }


def test_process_pr_events_skips_warning_for_existing_issue_number():
    logger = MagicMock()
    collector = BulkGithubEventCollection(logger)
    collector.repo_identifier = "owner/repo"
    collector.task_name = "Bulk Github Event task"
    collector._get_map_from_pr_url_to_id = MagicMock(return_value={})
    collector._get_issue_numbers_by_repo_id = MagicMock(return_value={3383})
    collector._insert_contributors = MagicMock()
    collector._insert_pr_events = MagicMock()

    collector._process_pr_events([_make_pr_event(3383)], repo_id=1)

    logger.warning.assert_not_called()


def test_process_pr_events_warns_for_missing_pr_number():
    logger = MagicMock()
    collector = BulkGithubEventCollection(logger)
    collector.repo_identifier = "owner/repo"
    collector.task_name = "Bulk Github Event task"
    collector._get_map_from_pr_url_to_id = MagicMock(return_value={})
    collector._get_issue_numbers_by_repo_id = MagicMock(return_value=set())
    collector._insert_contributors = MagicMock()
    collector._insert_pr_events = MagicMock()

    collector._process_pr_events([_make_pr_event(9999)], repo_id=1)

    logger.warning.assert_called_once()
    assert "Could not find related pr" in logger.warning.call_args.args[0]