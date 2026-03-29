import logging
import traceback
from datetime import timedelta, timezone, datetime

from sqlalchemy.exc import IntegrityError


from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurCoreRepoCollectionTask
from augur.application.db.data_parse import *
from augur.tasks.github.util.github_data_access import GithubDataAccess
from augur.tasks.github.util.github_random_key_auth import GithubRandomKeyAuth
from augur.tasks.github.util.util import add_key_value_pair_to_dicts, get_owner_repo
from augur.tasks.util.worker_util import remove_duplicate_dicts
from augur.application.db.models import Issue, IssueLabel, IssueAssignee
from augur.application.config import get_development_flag
from augur.application.db.lib import get_repo_by_repo_git, bulk_insert_dicts, get_core_data_last_collected, batch_insert_contributors, get_batch_size



development = get_development_flag()

@celery.task(base=AugurCoreRepoCollectionTask)
def collect_issues(repo_git: str, full_collection: bool) -> int:
    """
    Collect all issues (excluding pull requests) for a repository.

    Retrieves issues from GitHub API in batches of 1000 and inserts them along with
    related labels, assignees, and contributors.

    Args:
        repo_git: Full git URL (e.g., 'https://github.com/chaoss/augur')
        full_collection: True for all historical data, False for incremental (last collection - 2 days)

    Returns:
        Number of issues collected, or -1 on error
    """
    logger = logging.getLogger(collect_issues.__name__)

    repo_id = get_repo_by_repo_git(repo_git).repo_id

    owner, repo = get_owner_repo(repo_git)

    if full_collection:
        core_data_last_collected = None
    else:
        # Subtract 2 days to ensure all data is collected
        core_data_last_collected = (get_core_data_last_collected(repo_id) - timedelta(days=2)).replace(tzinfo=timezone.utc)

    key_auth = GithubRandomKeyAuth(logger)

    logger.info(f'this is the manifest.key_auth value: {str(key_auth)}')

    try:
        issue_data_generator = retrieve_all_issue_data(repo_git, logger, key_auth, core_data_last_collected)

        issue_batch_size = get_batch_size()

        # Process issues in batches to avoid memory spikes
        batch = []
        total_issues = 0

        for issue in issue_data_generator:
            batch.append(issue)

            if len(batch) >= issue_batch_size:
                logger.info(f"{owner}/{repo}: Processing batch of {len(batch)} issues (total so far: {total_issues + len(batch)})")
                process_issues(batch, f"{owner}/{repo}: Issue task", repo_id, logger)
                total_issues += len(batch)
                batch.clear()

        # Process remaining issues in the last batch
        if len(batch) > 0:
            logger.info(f"{owner}/{repo}: Processing final batch of {len(batch)} issues")
            process_issues(batch, f"{owner}/{repo}: Issue task", repo_id, logger)
            total_issues += len(batch)

        if total_issues == 0:
            logger.info(f"{owner}/{repo} has no issues")

        return total_issues

    except Exception as e:
        logger.error(f"Could not collect issues for repo {repo_git}\n Reason: {e} \n Traceback: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
        return -1



def retrieve_all_issue_data(repo_git: str, logger: logging.Logger, key_auth: GithubRandomKeyAuth, since: datetime | None = None):
    """
    Retrieve all issue data for a repository as a generator.

    Returns a generator to avoid materializing all issues in memory at once.
    This is critical for repos with 10,000+ issues to prevent memory spikes.

    Args:
        repo_git (str): The GitHub repository in "owner/repo" format.
        logger (logging.Logger): Logger for logging messages.
        key_auth (GithubRandomKeyAuth): Auth handler for GitHub API.
        since (datetime, optional): Only issues updated since this datetime will be retrieved.
    """
    owner, repo = get_owner_repo(repo_git)

    logger.info(f"Collecting issues for {owner}/{repo}")

    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all"

    if since:
        url += f"&since={since.isoformat()}"

    github_data_access = GithubDataAccess(key_auth, logger)

    num_pages = github_data_access.get_resource_page_count(url)
    logger.info(f"{owner}/{repo}: Retrieving {num_pages} pages of issues")

    issues_paginator = github_data_access.paginate_resource(url)

    # Return the generator directly instead of materializing it
    return issues_paginator
    
def process_issues(issues, task_name, repo_id, logger) -> None:
    
    # get repo_id or have it passed
    tool_source = "Issue Task"
    tool_version = "2.0"
    data_source = "Github API"

    issue_dicts = []
    issue_mapping_data = {}
    issue_total = len(issues)
    contributors = []
    for index, issue in enumerate(issues):

        # calls is_valid_pr_block to see if the data is a pr.
        # if it is a pr we skip it because we don't need prs 
        # in the issues table
        if is_valid_pr_block(issue) is True:
            issue_total-=1
            continue

        issue, contributor_data = process_issue_contributors(issue, tool_source, tool_version, data_source)

        contributors += contributor_data

        # create list of issue_dicts to bulk insert later
        issue_dicts.append(
            # get only the needed data for the issues table
            extract_needed_issue_data(issue, repo_id, tool_source, tool_version, data_source)
        )

         # get only the needed data for the issue_labels table
        issue_labels = extract_needed_issue_label_data(issue["labels"], repo_id,
                                                       tool_source, tool_version, data_source)

        # get only the needed data for the issue_assignees table
        issue_assignees = extract_needed_issue_assignee_data(issue["assignees"], repo_id,
                                                             tool_source, tool_version, data_source)


        mapping_data_key = issue["url"]
        issue_mapping_data[mapping_data_key] = {
                                            "labels": issue_labels,
                                            "assignees": issue_assignees,
                                            }     

    if len(issue_dicts) == 0:
        print("No issues found while processing")  
        return

    # remove duplicate contributors before inserting
    contributors = remove_duplicate_dicts(contributors)

    # insert contributors from these issues
    logger.info(f"{task_name}: Inserting {len(contributors)} contributors")
    batch_insert_contributors(logger, contributors)
                        

    # insert the issues into the issues table. 
    # issue_urls are gloablly unique across github so we are using it to determine whether an issue we collected is already in the table
    # specified in issue_return_columns is the columns of data we want returned. This data will return in this form; {"issue_url": url, "issue_id": id}
    logger.info(f"{task_name}: Inserting {len(issue_dicts)} issues")
    issue_natural_keys = ["repo_id", "gh_issue_id"]
    issue_return_columns = ["issue_url", "issue_id"]
    issue_string_columns = ["issue_title", "issue_body"]
    try:
        issue_return_data = bulk_insert_dicts(logger, issue_dicts, Issue, issue_natural_keys, return_columns=issue_return_columns, string_fields=issue_string_columns)
    except IntegrityError as e:
        logger.error(f"Ran into integrity error:{e} \n Offending data: \n{issue_dicts}")

        if development:
            raise e
    # loop through the issue_return_data so it can find the labels and 
    # assignees that corelate to the issue that was inserted labels 
    issue_label_dicts = []
    issue_assignee_dicts = []
    for data in issue_return_data:

        issue_url = data["issue_url"]
        issue_id = data["issue_id"]

        try:
            other_issue_data = issue_mapping_data[issue_url]
        except KeyError as e:
            logger.info(f"{task_name}: Cold not find other issue data. This should never happen. Error: {e}")


        # add the issue id to the lables and assignees, then add them to a list of dicts that will be inserted soon
        dict_key = "issue_id"
        issue_label_dicts += add_key_value_pair_to_dicts(other_issue_data["labels"], "issue_id", issue_id)
        issue_assignee_dicts += add_key_value_pair_to_dicts(other_issue_data["assignees"], "issue_id", issue_id)


    logger.info(f"{task_name}: Inserting other github issue data of lengths: Labels: {len(issue_label_dicts)} - Assignees: {len(issue_assignee_dicts)}")

    # inserting issue labels
    # we are using label_src_id and issue_id to determine if the label is already in the database.
    issue_label_natural_keys = ['label_src_id', 'issue_id']
    issue_label_string_fields = ["label_text", "label_description"]
    bulk_insert_dicts(logger, issue_label_dicts, IssueLabel,
                        issue_label_natural_keys, string_fields=issue_label_string_fields)

    # inserting issue assignees
    # we are using issue_assignee_src_id and issue_id to determine if the label is already in the database.
    issue_assignee_natural_keys = ['issue_assignee_src_id', 'issue_id']
    bulk_insert_dicts(logger, issue_assignee_dicts, IssueAssignee, issue_assignee_natural_keys)



def process_issue_contributors(issue, tool_source, tool_version, data_source):

    contributors = []

    issue_cntrb = extract_needed_contributor_data(issue["user"], tool_source, tool_version, data_source)
    issue["cntrb_id"] = issue_cntrb["cntrb_id"]
    contributors.append(issue_cntrb)

    for assignee in issue["assignees"]:

        issue_assignee_cntrb = extract_needed_contributor_data(assignee, tool_source, tool_version, data_source)
        assignee["cntrb_id"] = issue_assignee_cntrb["cntrb_id"]
        contributors.append(issue_assignee_cntrb)

    return issue, contributors


def is_valid_pr_block(issue):
    return (
        'pull_request' in issue and issue['pull_request']
        and isinstance(issue['pull_request'], dict) and 'url' in issue['pull_request']
    )
