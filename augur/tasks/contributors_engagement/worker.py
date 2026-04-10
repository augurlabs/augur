import logging
import traceback

from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurCoreRepoCollectionTask
from augur.application.db.lib import get_repo_by_repo_git
from augur.tasks.contributors_engagement.utils import (
    get_d0_engagement_data,
    get_d1_engagement_data, 
    get_d2_engagement_data,
    process_engagement_data
)


@celery.task(base=AugurCoreRepoCollectionTask)
def collect_contributor_engagement(repo_git: str, full_collection: bool = True) -> int:
    """
    Main task to collect contributor engagement data for all levels (D0, D1, D2)
    
    Args:
        repo_git: Repository git URL
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        Number of engagement records processed, or -1 on error
    """
    
    logger = logging.getLogger(collect_contributor_engagement.__name__)
    
    try:
        repo = get_repo_by_repo_git(repo_git)
        repo_id = repo.repo_id
        
        logger.info(f"Starting contributor engagement collection for repo: {repo_git}")
        
        d0_count = collect_d0_engagement(repo_git, full_collection)
        d1_count = collect_d1_engagement(repo_git, full_collection) 
        d2_count = collect_d2_engagement(repo_git, full_collection)
        
        total_processed = d0_count + d1_count + d2_count
        
        logger.info(f"Completed contributor engagement collection for {repo_git}. "
                   f"D0: {d0_count}, D1: {d1_count}, D2: {d2_count}, Total: {total_processed}")
        
        return total_processed
        
    except Exception as e:
        logger.error(f"Error collecting contributor engagement for {repo_git}: {e}")
        logger.error(f"Traceback: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
        return -1


@celery.task(base=AugurCoreRepoCollectionTask)
def collect_d0_engagement(repo_git: str, full_collection: bool = True) -> int:
    """
    Collect D0 level engagement data (basic engagement: forks, stars/watches)
    
    Args:
        repo_git: Repository git URL
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        Number of D0 engagement records processed
    """
    
    logger = logging.getLogger(collect_d0_engagement.__name__)
    
    try:
        repo = get_repo_by_repo_git(repo_git)
        repo_id = repo.repo_id
        
        logger.info(f"Collecting D0 engagement data for repo: {repo_git} ({'full' if full_collection else 'incremental'} collection)")
        
        if full_collection:
            logger.info(f"Full collection mode: clearing existing D0 engagement data for repo_id: {repo_id}")
        
        d0_data = get_d0_engagement_data(repo_id, logger, full_collection)
        
        if not d0_data:
            logger.info(f"No D0 engagement data found for repo: {repo_git}")
            return 0
        
        processed_count = process_engagement_data(
            d0_data, 
            repo_id, 
            "D0 Engagement Task", 
            logger, 
            engagement_level="d0",
            full_collection=full_collection
        )
        
        logger.info(f"Processed {processed_count} D0 engagement records for {repo_git}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error collecting D0 engagement for {repo_git}: {e}")
        logger.error(f"Traceback: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
        return 0


@celery.task(base=AugurCoreRepoCollectionTask)
def collect_d1_engagement(repo_git: str, full_collection: bool = True) -> int:
    """
    Collect D1 level engagement data (issue/review engagement)
    
    Args:
        repo_git: Repository git URL
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        Number of D1 engagement records processed
    """
    
    logger = logging.getLogger(collect_d1_engagement.__name__)
    
    try:
        repo = get_repo_by_repo_git(repo_git)
        repo_id = repo.repo_id
        
        logger.info(f"Collecting D1 engagement data for repo: {repo_git} ({'full' if full_collection else 'incremental'} collection)")
        
        if full_collection:
            logger.info(f"Full collection mode: clearing existing D1 engagement data for repo_id: {repo_id}")
        
        d1_data = get_d1_engagement_data(repo_id, logger, full_collection)
        
        if not d1_data:
            logger.info(f"No D1 engagement data found for repo: {repo_git}")
            return 0
        
        processed_count = process_engagement_data(
            d1_data, 
            repo_id, 
            "D1 Engagement Task", 
            logger, 
            engagement_level="d1",
            full_collection=full_collection
        )
        
        logger.info(f"Processed {processed_count} D1 engagement records for {repo_git}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error collecting D1 engagement for {repo_git}: {e}")
        logger.error(f"Traceback: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
        return 0


@celery.task(base=AugurCoreRepoCollectionTask)
def collect_d2_engagement(repo_git: str, full_collection: bool = True) -> int:
    """
    Collect D2 level engagement data (significant contributions)
    
    Args:
        repo_git: Repository git URL
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        Number of D2 engagement records processed
    """
    
    logger = logging.getLogger(collect_d2_engagement.__name__)
    
    try:
        repo = get_repo_by_repo_git(repo_git)
        repo_id = repo.repo_id
        
        logger.info(f"Collecting D2 engagement data for repo: {repo_git} ({'full' if full_collection else 'incremental'} collection)")
        
        if full_collection:
            logger.info(f"Full collection mode: clearing existing D2 engagement data for repo_id: {repo_id}")
        
        d2_data = get_d2_engagement_data(repo_id, logger, full_collection)
        
        if not d2_data:
            logger.info(f"No D2 engagement data found for repo: {repo_git}")
            return 0
        
        processed_count = process_engagement_data(
            d2_data, 
            repo_id, 
            "D2 Engagement Task", 
            logger, 
            engagement_level="d2",
            full_collection=full_collection
        )
        
        logger.info(f"Processed {processed_count} D2 engagement records for {repo_git}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error collecting D2 engagement for {repo_git}: {e}")
        logger.error(f"Traceback: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
        return 0
