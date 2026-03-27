import logging

from augur.tasks.github.detect_move.core import ping_github_for_repo_move, RepoMovedException, RepoGoneException
from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurCoreRepoCollectionTask, AugurSecondaryRepoCollectionTask
from augur.application.db.lib import get_repo_by_repo_git, get_session
from augur.tasks.github.util.github_random_key_auth import GithubRandomKeyAuth

from celery.exceptions import Reject


@celery.task(base=AugurCoreRepoCollectionTask)
def detect_github_repo_move_core(repo_git : str) -> None:

    logger = logging.getLogger(detect_github_repo_move_core.__name__)

    logger.info(f"Starting repo_move operation with {repo_git}")

    repo = get_repo_by_repo_git(repo_git)

    logger.info(f"Pinging repo: {repo_git}")

    key_auth = GithubRandomKeyAuth(logger)

    with get_session() as session:

        #Ping each repo with the given repo_git to make sure
        #that they are still in place.
        try:
            ping_github_for_repo_move(session, key_auth, repo, logger)
        except RepoMovedException:
            pass  # URL updated in DB; let the chain continue normally
        except RepoGoneException as e:
            raise Reject(e)


@celery.task(base=AugurSecondaryRepoCollectionTask)
def detect_github_repo_move_secondary(repo_git : str) -> None:

    logger = logging.getLogger(detect_github_repo_move_secondary.__name__)

    logger.info(f"Starting repo_move operation with {repo_git}")

    repo = get_repo_by_repo_git(repo_git)

    logger.info(f"Pinging repo: {repo_git}")

    key_auth = GithubRandomKeyAuth(logger)

    with get_session() as session:

        #Ping each repo with the given repo_git to make sure
        #that they are still in place.
        try:
            ping_github_for_repo_move(session, key_auth, repo, logger, collection_hook='secondary')
        except RepoMovedException:
            pass  # URL updated in DB; let the chain continue normally
        except RepoGoneException as e:
            raise Reject(e)
