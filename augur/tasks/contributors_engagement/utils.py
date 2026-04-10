import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from augur.application.db.lib import get_session, bulk_insert_dicts
from augur.application.db.models import ContributorEngagement, Contributor


class QueryLoader:
    """Utility class to load and manage SQL queries from external files"""
    
    def __init__(self, queries_file_path: str = "queries.sql"):
        self.queries_file_path = queries_file_path
        self._queries = {}
        self._load_queries()
    
    def _load_queries(self):
        """Load all queries from the SQL file"""
        if not os.path.exists(self.queries_file_path):
            raise FileNotFoundError(f"Queries file not found: {self.queries_file_path}")
        
        with open(self.queries_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Split content by query name comments
        sections = content.split('-- name: ')
        
        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            query_name = lines[0].strip()
            
            # Find description if it exists
            description = ""
            query_start_idx = 1
            if len(lines) > 1 and lines[1].startswith('-- description: '):
                description = lines[1].replace('-- description: ', '').strip()
                query_start_idx = 2
            
            # Extract query content (everything after the name and description)
            query_lines = []
            for line in lines[query_start_idx:]:
                # Stop if we hit another query definition
                if line.startswith('-- name: '):
                    break
                query_lines.append(line)
            
            query_content = '\n'.join(query_lines).strip()
            
            # Remove trailing semicolon and clean up
            if query_content.endswith(';'):
                query_content = query_content[:-1].strip()
            
            self._queries[query_name] = {
                'description': description,
                'query': query_content
            }
    
    def get_query(self, query_name: str) -> str:
        """Get a query by name"""
        if query_name not in self._queries:
            raise ValueError(f"Query '{query_name}' not found in {self.queries_file_path}")
        return self._queries[query_name]['query']
    
    def get_query_description(self, query_name: str) -> str:
        """Get a query description by name"""
        if query_name not in self._queries:
            raise ValueError(f"Query '{query_name}' not found in {self.queries_file_path}")
        return self._queries[query_name]['description']
    
    def list_queries(self) -> List[str]:
        """List all available query names"""
        return list(self._queries.keys())

import time

def wait_for_db_ready(retries=10, delay=3, logger=None):
    for attempt in range(retries):
        try:
            with get_session() as session:
                session.execute(text("SELECT 1"))
            if logger:
                logger.info("Database is ready.")
            return True
        except Exception as e:
            if logger:
                logger.warning(f"Database not ready (attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)
    if logger:
        logger.error("Database not ready after retries.")
    return False

# Initialize global query loader
import pathlib

queries_file_path = str(pathlib.Path(__file__).parent / "queries.sql")
query_loader = QueryLoader(queries_file_path=queries_file_path)

def get_d0_engagement_data(repo_id: int, logger: logging.Logger, full_collection: bool = True) -> List[Dict[str, Any]]:
    """
    Get D0 level engagement data (basic engagement: forks, stars/watches)
    
    Args:
        repo_id: Repository ID
        logger: Logger instance
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        List of dictionaries containing D0 engagement data
    """
    
    logger.info(f"Executing D0 engagement query for repo_id: {repo_id} (full_collection: {full_collection})")
    
    # Wait for DB to be ready before running the query
    if not wait_for_db_ready(logger=logger):
        logger.error("Database not ready, aborting D0 engagement query.")
        return []

    # Get the base query
    base_query = query_loader.get_query('d0_engagement_query')
    
    # Apply time filter
    time_filter = ""
    if not full_collection:
        time_filter = "AND cr.created_at >= NOW() - INTERVAL '30 days'"
    
    # Format the query with time filter
    d0_query = text(base_query.format(time_filter=time_filter))
    
    try:
        with get_session() as session:
            result = session.execute(d0_query, {"repo_id": repo_id})
            data = [dict(row._mapping) for row in result.fetchall()]
            logger.info(f"Retrieved {len(data)} D0 engagement records ({'full' if full_collection else 'incremental'} collection)")
            return data
    except Exception as e:
        logger.error(f"Error executing D0 engagement query: {e}")
        return []


def get_d1_engagement_data(repo_id: int, logger: logging.Logger, full_collection: bool = True) -> List[Dict[str, Any]]:
    """
    Get D1 level engagement data (issue/review engagement)
    
    Args:
        repo_id: Repository ID
        logger: Logger instance
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        List of dictionaries containing D1 engagement data
    """
    
    logger.info(f"Executing D1 engagement query for repo_id: {repo_id} (full_collection: {full_collection})")
    
    # Wait for DB to be ready before running the query
    if not wait_for_db_ready(logger=logger):
        logger.error("Database not ready, aborting D0 engagement query.")
        return []

    # Get the base query
    base_query = query_loader.get_query('d1_engagement_query')
    
    # Apply time filter
    time_filter = "1 year"
    if not full_collection:
        time_filter = "30 days"
    
    # Format the query with time filter
    d1_query = text(base_query.format(time_filter=time_filter))
    
    try:
        with get_session() as session:
            result = session.execute(d1_query, {"repo_id": repo_id})
            data = [dict(row._mapping) for row in result.fetchall()]
            logger.info(f"Retrieved {len(data)} D1 engagement records ({'full' if full_collection else 'incremental'} collection)")
            return data
    except Exception as e:
        logger.error(f"Error executing D1 engagement query: {e}")
        return []


def get_d2_engagement_data(repo_id: int, logger: logging.Logger, full_collection: bool = True) -> List[Dict[str, Any]]:
    """
    Get D2 level engagement data (significant contributions)
    
    Args:
        repo_id: Repository ID
        logger: Logger instance
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        List of dictionaries containing D2 engagement data
    """
    
    logger.info(f"Executing D2 engagement query for repo_id: {repo_id} (full_collection: {full_collection})")
    
    # Wait for DB to be ready before running the query
    if not wait_for_db_ready(logger=logger):
        logger.error("Database not ready, aborting D0 engagement query.")
        return []

    # Get the base query
    base_query = query_loader.get_query('d2_engagement_query')
    
    # Apply time filters based on collection type
    if not full_collection:
        pr_merged_time_filter = "AND pr.pr_merged_at >= NOW() - INTERVAL '90 days'"
        issue_time_filter = "AND i.created_at >= NOW() - INTERVAL '90 days'"
        comment_time_filter = "AND m.msg_timestamp >= NOW() - INTERVAL '90 days'"
        pr_commits_time_filter = "AND pr.pr_created_at >= NOW() - INTERVAL '90 days'"
        comment_pr_time_filter = "AND m.msg_timestamp >= NOW() - INTERVAL '90 days'"
    else:
        pr_merged_time_filter = ""
        issue_time_filter = ""
        comment_time_filter = ""
        pr_commits_time_filter = ""
        comment_pr_time_filter = ""
    
    # Format the query with time filters
    d2_query = text(base_query.format(
        pr_merged_time_filter=pr_merged_time_filter,
        issue_time_filter=issue_time_filter,
        comment_time_filter=comment_time_filter,
        pr_commits_time_filter=pr_commits_time_filter,
        comment_pr_time_filter=comment_pr_time_filter
    ))
    
    try:
        with get_session() as session:
            result = session.execute(d2_query, {"repo_id": repo_id})
            data = [dict(row._mapping) for row in result.fetchall()]
            logger.info(f"Retrieved {len(data)} D2 engagement records ({'full' if full_collection else 'incremental'} collection)")
            return data
    except Exception as e:
        logger.error(f"Error executing D2 engagement query: {e}")
        return []


def process_engagement_data(
    engagement_data: List[Dict[str, Any]], 
    repo_id: int, 
    task_name: str, 
    logger: logging.Logger,
    engagement_level: str,
    full_collection: bool = True
) -> int:
    """
    Process and insert engagement data into the database
    
    Args:
        engagement_data: List of engagement data dictionaries
        repo_id: Repository ID
        task_name: Name of the task for logging
        logger: Logger instance
        engagement_level: Level of engagement (d0, d1, d2)
        full_collection: Whether to perform full collection or incremental
        
    Returns:
        Number of records processed
    """
    
    if not engagement_data:
        logger.info(f"{task_name}: No engagement data to process")
        return 0
    
    logger.info(f"{task_name}: Processing {len(engagement_data)} {engagement_level} engagement records ({'full' if full_collection else 'incremental'} collection)")
    
    tool_source = "Contributor Engagement Task"
    tool_version = "1.0"
    data_source = "Augur Database"
    
    processed_records = []
    
    for record in engagement_data:
        engagement_record = {
            "repo_id": repo_id,
            "cntrb_id": record.get("cntrb_id"),
            "username": record.get("username", ""),
            "full_name": record.get("full_name"),
            "country": record.get("country"),
            "platform": record.get("platform", "Unknown"),
            "tool_source": tool_source,
            "tool_version": tool_version,
            "data_source": data_source
        }
        
        if engagement_level == "d0":
            engagement_record.update({
                "d0_forked": record.get("forked", False),
                "d0_starred_or_watched": record.get("starred_or_watched", False),
                "d0_engagement_timestamp": record.get("engagement_timestamp")
            })
        elif engagement_level == "d1":
            engagement_record.update({
                "d1_first_issue_created_at": record.get("first_issue_created_at"),
                "d1_first_pr_opened_at": record.get("first_pr_opened_at"),
                "d1_first_pr_commented_at": record.get("first_pr_commented_at")
            })
        elif engagement_level == "d2":
            engagement_record.update({
                "d2_has_merged_pr": record.get("has_merged_pr", False),
                "d2_created_many_issues": record.get("created_many_issues", False),
                "d2_total_comments": record.get("total_comments", 0),
                "d2_has_pr_with_many_commits": record.get("has_pr_with_many_commits", False),
                "d2_commented_on_multiple_prs": record.get("commented_on_multiple_prs", False)
            })
        
        processed_records.append(engagement_record)
    
    try:
        natural_keys = ["repo_id", "cntrb_id"]
        string_fields = ["username", "full_name", "platform"]
        
        bulk_insert_dicts(
            logger, 
            processed_records, 
            ContributorEngagement, 
            natural_keys,
            string_fields=string_fields
        )
        
        logger.info(f"{task_name}: Successfully inserted {len(processed_records)} {engagement_level} engagement records ({'full' if full_collection else 'incremental'} collection)")
        return len(processed_records)
        
    except Exception as e:
        logger.error(f"{task_name}: Error inserting {engagement_level} engagement data: {e}")
        return 0


def create_materialized_views(logger: logging.Logger) -> bool:
    """
    Create materialized views for D0, D1, D2 engagement levels
    
    Args:
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    
    logger.info("Creating contributor engagement materialized views")
    
    # Get materialized view creation queries
    d0_view_sql = text(query_loader.get_query('create_d0_materialized_view'))
    d1_view_sql = text(query_loader.get_query('create_d1_materialized_view'))
    d2_view_sql = text(query_loader.get_query('create_d2_materialized_view'))
    
    try:
        with get_session() as session:
            session.execute(d0_view_sql)
            session.execute(d1_view_sql)
            session.execute(d2_view_sql)
            session.commit()
            
            logger.info("Successfully created contributor engagement materialized views")
            return True
            
    except Exception as e:
        logger.error(f"Error creating materialized views: {e}")
        return False


def refresh_materialized_views(logger: logging.Logger) -> bool:
    """
    Refresh the contributor engagement materialized views
    
    Args:
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    
    logger.info("Refreshing contributor engagement materialized views")
    
    # Get refresh queries
    refresh_queries = [
        text(query_loader.get_query('refresh_d0_materialized_view')),
        text(query_loader.get_query('refresh_d1_materialized_view')),
        text(query_loader.get_query('refresh_d2_materialized_view'))
    ]
    
    try:
        with get_session() as session:
            for query in refresh_queries:
                session.execute(query)
            session.commit()
            
            logger.info("Successfully refreshed contributor engagement materialized views")
            return True
            
    except Exception as e:
        logger.error(f"Error refreshing materialized views: {e}")
        return False