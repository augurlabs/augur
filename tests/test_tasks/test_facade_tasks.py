# SPDX-License-Identifier: MIT

import sys
import types
import importlib.util
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stub out all heavy Augur/DB dependencies so the test needs no live environment.
# ---------------------------------------------------------------------------

def _stub(name, is_package=False, path=None):
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    if is_package:
        mod.__path__ = [str(path)] if path else []
        mod.__package__ = name
    sys.modules[name] = mod
    return mod


AUGUR_ROOT = Path(__file__).parents[2] / "augur"

# Packages that need real __path__ so Python can locate sub-modules on disk
_real_packages = {
    "augur":            AUGUR_ROOT,
    "augur.tasks":      AUGUR_ROOT / "tasks",
    "augur.tasks.git":  AUGUR_ROOT / "tasks" / "git",
}
for _name, _path in _real_packages.items():
    _stub(_name, is_package=True, path=_path)

# Stub packages with no real path needed
for _pkg in [
    "psycopg2",
    "augur.application", "augur.application.db",
    "augur.tasks.init",
    "augur.tasks.util",
    "augur.tasks.github", "augur.tasks.github.util", "augur.tasks.github.facade_github",
    "augur.tasks.git.util", "augur.tasks.git.util.facade_worker",
    "augur.tasks.git.util.facade_worker.facade_worker",
    "augur.tasks.git.dependency_tasks",
    "augur.tasks.git.dependency_libyear_tasks",
    "augur.tasks.git.scc_value_tasks",
]:
    _stub(_pkg, is_package=True)

# Leaf stubs
for _leaf in [
    "psycopg2.errors",
    "augur.application.db.lib", "augur.application.db.session",
    "augur.application.db.models", "augur.application.db.data_parse",
    "augur.application.config",
    "augur.tasks.init.celery_app",
    "augur.tasks.util.collection_state", "augur.tasks.util.collection_util",
    "augur.tasks.github.util.github_task_session",
    "augur.tasks.github.facade_github.tasks",
    "augur.tasks.git.util.facade_worker.facade_worker.config",
    "augur.tasks.git.util.facade_worker.facade_worker.utilitymethods",
    "augur.tasks.git.util.facade_worker.facade_worker.analyzecommit",
    "augur.tasks.git.util.facade_worker.facade_worker.repofetch",
    "augur.tasks.git.dependency_tasks.tasks",
    "augur.tasks.git.dependency_libyear_tasks.tasks",
    "augur.tasks.git.scc_value_tasks.tasks",
]:
    _stub(_leaf)

# Minimum attributes consumed at module level in facade_tasks.py

_db_lib = sys.modules["augur.application.db.lib"]
for _fn in [
    "get_session", "get_repo_by_repo_git", "get_repo_by_repo_id",
    "remove_working_commits_by_repo_id_and_hashes", "get_working_commits_by_repo_id",
    "facade_bulk_insert_commits", "bulk_insert_dicts", "get_missing_commit_message_hashes",
]:
    setattr(_db_lib, _fn, MagicMock())

_db_models = sys.modules["augur.application.db.models"]
_db_models.Repo = MagicMock()
_db_models.CollectionStatus = MagicMock()
_db_models.CommitMessage = MagicMock()

_util_methods = sys.modules["augur.tasks.git.util.facade_worker.facade_worker.utilitymethods"]
for _fn in [
    "trim_commits", "get_absolute_repo_path", "get_parent_commits_set",
    "get_existing_commits_set", "get_repo_commit_count",
    "update_facade_scheduling_fields", "get_facade_weight_with_commit_count",
]:
    setattr(_util_methods, _fn, MagicMock())

_analyze = sys.modules["augur.tasks.git.util.facade_worker.facade_worker.analyzecommit"]
_analyze.analyze_commit = MagicMock()

_cs = sys.modules["augur.tasks.util.collection_state"]
_cs.CollectionState = MagicMock()

_cu = sys.modules["augur.tasks.util.collection_util"]
_cu.get_collection_status_repo_git_from_filter = MagicMock()

_ci = sys.modules["augur.tasks.init.celery_app"]
_ci.celery_app = MagicMock()
_ci.AugurFacadeRepoCollectionTask = MagicMock()
_ci.AugurSecondaryRepoCollectionTask = MagicMock()

_fc = sys.modules["augur.tasks.git.util.facade_worker.facade_worker.config"]
_fc.FacadeHelper = MagicMock()

_rf = sys.modules["augur.tasks.git.util.facade_worker.facade_worker.repofetch"]
_rf.GitCloneError = type("GitCloneError", (Exception,), {})
_rf.git_repo_initialize = MagicMock()
_rf.git_repo_updates = MagicMock()

sys.modules["augur.tasks.github.facade_github.tasks"].insert_facade_contributors = MagicMock()

for _attr, _mod in [
    ("process_dependency_metrics",         "augur.tasks.git.dependency_tasks.tasks"),
    ("process_libyear_dependency_metrics", "augur.tasks.git.dependency_libyear_tasks.tasks"),
    ("process_scc_value_metrics",          "augur.tasks.git.scc_value_tasks.tasks"),
]:
    setattr(sys.modules[_mod], _attr, MagicMock())

# Load facade_tasks directly from the source file, bypassing package machinery
_facade_tasks_path = AUGUR_ROOT / "tasks" / "git" / "facade_tasks.py"
_spec = importlib.util.spec_from_file_location(
    "augur.tasks.git.facade_tasks", _facade_tasks_path
)
_facade_tasks_mod = importlib.util.module_from_spec(_spec)
sys.modules["augur.tasks.git.facade_tasks"] = _facade_tasks_mod
_spec.loader.exec_module(_facade_tasks_mod)

facade_phase = _facade_tasks_mod.facade_phase

from celery import chain, signature   # noqa: E402
from celery.canvas import group        # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_GIT = "https://github.com/test/repo"


def _task_mock(name):
    """Return (task_mock, real_signature) — real signatures so chain() works."""
    sig = signature(name)   # lightweight real Celery Signature, no broker needed
    task = MagicMock(name=name)
    task.si.return_value = sig
    return task, sig


@pytest.fixture
def mock_facade_helper():
    helper = MagicMock()
    helper.limited_run = 0
    helper.run_analysis = 1
    helper.pull_repos = 1
    helper.run_facade_contributors = 1
    helper.commit_messages = 0
    return helper


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_facade_phase_returns_chain(mock_facade_helper):
    """facade_phase must return a celery chain, not a group."""
    clone_task, _ = _task_mock("git_repo_updates_facade_task")
    count_task, _ = _task_mock("git_update_commit_count_weight")
    contrib_task, _ = _task_mock("insert_facade_contributors")
    dep_task, _ = _task_mock("process_dependency_metrics")
    libyear_task, _ = _task_mock("process_libyear_dependency_metrics")
    scc_task, _ = _task_mock("process_scc_value_metrics")

    with patch.object(_facade_tasks_mod, "FacadeHelper", return_value=mock_facade_helper), \
         patch.object(_facade_tasks_mod, "git_repo_updates_facade_task", clone_task), \
         patch.object(_facade_tasks_mod, "git_update_commit_count_weight", count_task), \
         patch.object(_facade_tasks_mod, "generate_analysis_sequence", return_value=[]), \
         patch.object(_facade_tasks_mod, "insert_facade_contributors", contrib_task), \
         patch.object(_facade_tasks_mod, "process_dependency_metrics", dep_task), \
         patch.object(_facade_tasks_mod, "process_libyear_dependency_metrics", libyear_task), \
         patch.object(_facade_tasks_mod, "process_scc_value_metrics", scc_task):

        result = facade_phase(REPO_GIT, full_collection=True)

    # Celery's chain() and the pipe operator both produce chain-like objects
    # (chain or _chain) — what matters is it is NOT a group.
    assert not isinstance(result, group), (
        "facade_phase must not use group() — that causes dependency tasks "
        "to race against the git clone (issue #3767)"
    )
    assert hasattr(result, "tasks"), "result should be a sequential chain with .tasks"


def test_facade_phase_dependency_tasks_follow_clone(mock_facade_helper):
    """Dependency analysis tasks must be sequenced after the git clone task.

    Regression test for https://github.com/chaoss/augur/issues/3767:
    process_dependency_metrics, process_libyear_dependency_metrics, and
    process_scc_value_metrics were previously inside a Celery group() alongside
    the facade core chain, causing them to fire concurrently with the git clone
    and raise FileNotFoundError on directories not yet written to disk.
    """
    clone_task, clone_sig = _task_mock("git_repo_updates_facade_task")
    count_task, _ = _task_mock("git_update_commit_count_weight")
    contrib_task, _ = _task_mock("insert_facade_contributors")
    dep_task, dep_sig = _task_mock("process_dependency_metrics")
    libyear_task, libyear_sig = _task_mock("process_libyear_dependency_metrics")
    scc_task, scc_sig = _task_mock("process_scc_value_metrics")

    with patch.object(_facade_tasks_mod, "FacadeHelper", return_value=mock_facade_helper), \
         patch.object(_facade_tasks_mod, "git_repo_updates_facade_task", clone_task), \
         patch.object(_facade_tasks_mod, "git_update_commit_count_weight", count_task), \
         patch.object(_facade_tasks_mod, "generate_analysis_sequence", return_value=[]), \
         patch.object(_facade_tasks_mod, "insert_facade_contributors", contrib_task), \
         patch.object(_facade_tasks_mod, "process_dependency_metrics", dep_task), \
         patch.object(_facade_tasks_mod, "process_libyear_dependency_metrics", libyear_task), \
         patch.object(_facade_tasks_mod, "process_scc_value_metrics", scc_task):

        result = facade_phase(REPO_GIT, full_collection=True)

    tasks = list(result.tasks)
    clone_idx   = tasks.index(clone_sig)
    dep_idx     = tasks.index(dep_sig)
    libyear_idx = tasks.index(libyear_sig)
    scc_idx     = tasks.index(scc_sig)

    assert dep_idx > clone_idx, \
        "process_dependency_metrics must run after git clone, not in parallel"
    assert libyear_idx > clone_idx, \
        "process_libyear_dependency_metrics must run after git clone, not in parallel"
    assert scc_idx > clone_idx, \
        "process_scc_value_metrics must run after git clone, not in parallel"
