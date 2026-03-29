import logging

from augur.tasks.github.detect_move.core import ping_github_for_repo_move, RepoMovedException, RepoGoneException
from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurCoreRepoCollectionTask, AugurSecondaryRepoCollectionTask
from augur.application.db.lib import get_repo_by_repo_git, get_session
from augur.application.db.models import Repo
from augur.tasks.github.util.github_random_key_auth import GithubRandomKeyAuth
from augur.tasks.util.collection_state import CollectionState

from celery.exceptions import Reject


@celery.task(bind=True, base=AugurCoreRepoCollectionTask)
def detect_github_repo_move_core(self, repo_git : str) -> None:

    logger = logging.getLogger(detect_github_repo_move_core.__name__)

    logger.info(f"Starting repo_move operation with {repo_git}")

    repo = get_repo_by_repo_git(repo_git)

    logger.info(f"Pinging repo: {repo_git}")

    key_auth = GithubRandomKeyAuth(logger)

    with get_session() as session:

        try:
            ping_github_for_repo_move(session, key_auth, repo, logger)
        except RepoMovedException as e:
            if e.new_url:
                # Cancel downstream tasks — they were built with the old URL baked
                # into their .si() signatures and are not yet on the broker.
                self.request.chain = None

                # DB already has the new URL; reset status so the scheduler
                # re-collects this repo with the correct URL in the next cycle.
                moved_repo = session.query(Repo).filter(Repo.repo_git == e.new_url).first()
                if moved_repo:
                    status = moved_repo.collection_status[0]
                    status.core_status = CollectionState.PENDING.value
                    status.core_task_id = None
                    session.commit()
                return
            raise Reject(e)
        except RepoGoneException as e:
            raise Reject(e)


@celery.task(bind=True, base=AugurSecondaryRepoCollectionTask)
def detect_github_repo_move_secondary(self, repo_git : str) -> None:

    logger = logging.getLogger(detect_github_repo_move_secondary.__name__)

    logger.info(f"Starting repo_move operation with {repo_git}")

    repo = get_repo_by_repo_git(repo_git)

    logger.info(f"Pinging repo: {repo_git}")

    key_auth = GithubRandomKeyAuth(logger)

    with get_session() as session:

        try:
            ping_github_for_repo_move(session, key_auth, repo, logger, collection_hook='secondary')
        except RepoMovedException as e:
            if e.new_url:
                # Cancel downstream tasks — they were built with the old URL baked
                # into their .si() signatures and are not yet on the broker.
                self.request.chain = None

                # DB already has the new URL; reset status so the scheduler
                # re-collects this repo with the correct URL in the next cycle.
                moved_repo = session.query(Repo).filter(Repo.repo_git == e.new_url).first()
                if moved_repo:
                    status = moved_repo.collection_status[0]
                    status.secondary_status = CollectionState.PENDING.value
                    status.secondary_task_id = None
                    session.commit()
                return
            raise Reject(e)
        except RepoGoneException as e:
            raise Reject(e)
