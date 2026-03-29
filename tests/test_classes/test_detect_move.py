import pytest
from unittest.mock import MagicMock, patch
from celery.exceptions import Reject

from augur.tasks.github.detect_move.core import (
    RepoMovedException,
    RepoGoneException,
    ping_github_for_repo_move,
)


def _make_response(status_code, headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = ""
    resp.json = MagicMock(return_value={})
    return resp


def _make_repo(repo_git="https://github.com/old-owner/old-repo"):
    repo = MagicMock()
    repo.repo_git = repo_git
    repo.repo_id = 1
    repo.description = ""
    return repo


def _session_mock():
    m = MagicMock()
    m.__enter__ = MagicMock(return_value=MagicMock())
    m.__exit__ = MagicMock(return_value=False)
    return m


@patch("augur.tasks.github.detect_move.core.update_repo_with_dict")
@patch("augur.tasks.github.detect_move.core.extract_owner_and_repo_from_endpoint")
@patch("augur.tasks.github.detect_move.core.hit_api")
def test_ping_301_raises_repo_moved_exception(mock_hit, mock_extract, mock_update):
    mock_hit.return_value = _make_response(
        301, headers={"location": "https://api.github.com/repos/new-owner/new-repo"}
    )
    mock_extract.return_value = ("new-owner", "new-repo")
    mock_update.return_value = "https://github.com/new-owner/new-repo"

    with pytest.raises(RepoMovedException) as exc_info:
        ping_github_for_repo_move(MagicMock(), MagicMock(), _make_repo(), MagicMock())

    assert exc_info.value.new_url == "https://github.com/new-owner/new-repo"


@patch("augur.tasks.github.detect_move.core.execute_session_query")
@patch("augur.tasks.github.detect_move.core.update_repo_with_dict")
@patch("augur.tasks.github.detect_move.core.hit_api")
def test_ping_404_raises_repo_gone_exception(mock_hit, mock_update, mock_query):
    mock_hit.return_value = _make_response(404)
    mock_update.return_value = "https://github.com/old-owner/old-repo"
    mock_query.return_value = MagicMock()

    with pytest.raises(RepoGoneException):
        ping_github_for_repo_move(MagicMock(), MagicMock(), _make_repo(), MagicMock())


@patch("augur.tasks.github.detect_move.core.hit_api")
def test_ping_200_returns_none(mock_hit):
    mock_hit.return_value = _make_response(200)
    assert ping_github_for_repo_move(MagicMock(), MagicMock(), _make_repo(), MagicMock()) is None


@patch("augur.tasks.github.detect_move.tasks.GithubRandomKeyAuth")
@patch("augur.tasks.github.detect_move.tasks.get_session")
@patch("augur.tasks.github.detect_move.tasks.get_repo_by_repo_git")
@patch("augur.tasks.github.detect_move.tasks.ping_github_for_repo_move")
def test_core_task_cancels_chain_and_resets_status_on_move(mock_ping, mock_get_repo, mock_get_session, mock_key_auth):
    """
    When a repo has moved, the task must:
    1. Set request.chain = None so downstream tasks (queued with old URL) are cancelled.
    2. Reset core_status to PENDING so the scheduler re-collects with the new URL.
    3. Return cleanly (no exception).
    """
    from augur.tasks.github.detect_move.tasks import detect_github_repo_move_core
    from augur.tasks.util.collection_state import CollectionState

    new_url = "https://github.com/new-owner/new-repo"
    mock_ping.side_effect = RepoMovedException("moved", new_url=new_url)
    mock_get_repo.return_value = _make_repo()

    mock_status = MagicMock()
    mock_moved_repo = MagicMock()
    mock_moved_repo.collection_status = [mock_status]

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_moved_repo
    mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

    task_self = MagicMock()
    task_self.request = MagicMock()

    result = detect_github_repo_move_core.__wrapped__(task_self, "https://github.com/old-owner/old-repo")

    assert task_self.request.chain is None
    assert mock_status.core_status == CollectionState.PENDING.value
    assert mock_status.core_task_id is None
    assert result is None


@patch("augur.tasks.github.detect_move.tasks.GithubRandomKeyAuth")
@patch("augur.tasks.github.detect_move.tasks.get_session")
@patch("augur.tasks.github.detect_move.tasks.get_repo_by_repo_git")
@patch("augur.tasks.github.detect_move.tasks.ping_github_for_repo_move")
def test_core_task_rejects_on_repo_gone(mock_ping, mock_get_repo, mock_get_session, mock_key_auth):
    from augur.tasks.github.detect_move.tasks import detect_github_repo_move_core

    mock_ping.side_effect = RepoGoneException("gone")
    mock_get_repo.return_value = _make_repo()
    mock_get_session.return_value = _session_mock()

    with pytest.raises(Reject):
        detect_github_repo_move_core.__wrapped__(MagicMock(), "https://github.com/old-owner/old-repo")
