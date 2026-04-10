import logging
from datetime import timedelta, timezone

from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurCoreRepoCollectionTask
from augur.application.db.data_parse import *
from augur.tasks.github.util.github_data_access import GithubDataAccess, UrlNotFoundException
from augur.tasks.github.util.github_task_session import GithubTaskManifest
from augur.tasks.util.worker_util import remove_duplicate_dicts
from augur.tasks.github.util.util import get_owner_repo
from augur.application.db.models import PullRequest, Message, Issue, PullRequestMessageRef, IssueMessageRef, Contributor, Repo, CollectionStatus
from augur.application.db import get_engine, get_session
from augur.application.db.lib import get_core_data_last_collected, get_batch_size
from sqlalchemy.sql import text



platform_id = 1

@celery.task(base=AugurCoreRepoCollectionTask)
def collect_github_messages(repo_git: str, full_collection: bool) -> None:

    logger = logging.getLogger(collect_github_messages.__name__)

    with GithubTaskManifest(logger) as manifest:

        augur_db = manifest.augur_db
            
        repo_id = augur_db.session.query(Repo).filter(
            Repo.repo_git == repo_git).one().repo_id

        owner, repo = get_owner_repo(repo_git)
        task_name = f"{owner}/{repo}: Message Task"

        if full_collection:
            core_data_last_collected = None
        else:
            # subtract 2 days to ensure all data is collected 
            core_data_last_collected = (get_core_data_last_collected(repo_id) - timedelta(days=2)).replace(tzinfo=timezone.utc)

        
        if is_repo_small(repo_id):
            message_data = fast_retrieve_all_pr_and_issue_messages(repo_git, logger, manifest.key_auth, task_name, core_data_last_collected)
            
            if message_data:
                process_messages(message_data, task_name, repo_id, logger, augur_db)

            else:
                logger.info(f"{owner}/{repo} has no messages")

        else:
            process_large_issue_and_pr_message_collection(repo_id, repo_git, logger, manifest.key_auth, task_name, augur_db, core_data_last_collected)


def is_repo_small(repo_id):

    with get_session() as session:

        result = session.query(CollectionStatus).filter(CollectionStatus.repo_id == repo_id, CollectionStatus.issue_pr_sum <= 10).first()

        return result != None

def fast_retrieve_all_pr_and_issue_messages(repo_git: str, logger, key_auth, task_name, since) -> None:

    owner, repo = get_owner_repo(repo_git)

    github_data_access = GithubDataAccess(key_auth, logger)

    # url to get issue and pull request comments
    url = github_data_access.issues_endpoint_url(owner, repo) + "comments"

    if since:
        url += f"?since={since.isoformat()}"

    # define logger for task
    logger.info(f"Collecting github comments for {owner}/{repo}")
    
    message_count = github_data_access.get_resource_count(url)

    logger.info(f"{task_name}: Collecting {message_count} github messages")

    return list(github_data_access.paginate_resource(url))


def process_large_issue_and_pr_message_collection(repo_id, repo_git: str, logger, key_auth, task_name, augur_db, since) -> None:

    message_batch_size = get_batch_size("message")

    owner, repo = get_owner_repo(repo_git)

    # define logger for task
    logger.info(f"Collecting github comments for {owner}/{repo}")

    engine = get_engine()

    with engine.connect() as connection:

        if since:
             query = text(f"""
                (select pr_comments_url from pull_requests WHERE repo_id={repo_id} AND pr_comments_url IS NOT NULL AND pr_updated_at > timestamptz(timestamp '{since}') order by pr_created_at desc)
                UNION
                (select comments_url as comment_url from issues WHERE repo_id={repo_id} AND comments_url IS NOT NULL AND updated_at > timestamptz(timestamp '{since}') order by created_at desc);
            """)
        else:

            query = text(f"""
                (select pr_comments_url from pull_requests WHERE repo_id={repo_id} AND pr_comments_url IS NOT NULL order by pr_created_at desc)
                UNION
                (select comments_url as comment_url from issues WHERE repo_id={repo_id} AND comments_url IS NOT NULL order by created_at desc);
            """)
        

        result = connection.execute(query).fetchall()
    comment_urls = [x[0] for x in result if x[0] is not None]

    github_data_access = GithubDataAccess(key_auth, logger)

    logger.info(f"{task_name}: Collecting github messages for {len(comment_urls)} prs/issues")

    all_data = []
    skipped_urls = 0

    for comment_url in comment_urls:
        try:
            messages = list(github_data_access.paginate_resource(comment_url))
            all_data += messages
        except UrlNotFoundException:
            logger.info(f"{task_name}: PR or issue comment url of {comment_url} returned 404. Skipping.")
            skipped_urls += 1

        if len(all_data) >= message_batch_size:
            process_messages(all_data, task_name, repo_id, logger, augur_db)
            all_data.clear()

    if len(all_data) > 0:
        process_messages(all_data, task_name, repo_id, logger, augur_db)

    logger.info(f"{task_name}: Finished. Skipped {skipped_urls} comment URLs due to 404.")
        

def process_messages(messages, task_name, repo_id, logger, augur_db):

    tool_version = "2.0"
    data_source = "Github API"

    message_dicts = []
    message_ref_mapping_data = {}
    contributors = []

    if messages is None:
        logger.debug(f"{task_name}: Messages was Nonetype...exiting")
        return

    if len(messages) == 0:
        logger.info(f"{task_name}: No messages to process")

    # create mapping from issue url to issue id of current issues
    issue_url_to_id_map = {}
    issues = augur_db.session.query(Issue).filter(Issue.repo_id == repo_id).all()
    for issue in issues:
        issue_url_to_id_map[issue.issue_url] = issue.issue_id

    # create mapping from pr url to pr id of current pull requests
    pr_issue_url_to_id_map = {}
    prs = augur_db.session.query(PullRequest).filter(PullRequest.repo_id == repo_id).all()
    for pr in prs:
        pr_issue_url_to_id_map[pr.pr_issue_url] = pr.pull_request_id


    message_len = len(messages)
    for index, message in enumerate(messages):

        if index % 1000 == 0:
            if message_len > 1000:
                logger.info(f"{task_name}: Processing 1000 messages")
            else:
                logger.info(f"{task_name}: Processing {message_len-index} messages")

        related_pr_or_issue_found = False

        # determine whether this is an issue or PR message so we can set the correct tool_source in metadata
        if is_issue_message(message["html_url"]):
            tool_source = "Issue comment task"
        else:
            tool_source = "Pr comment task"

        # this adds the cntrb_id to the message data
        # the returned contributor will be added to the contributors list later, if the related issue or pr are found
        # this logic is used so we don't insert a contributor when the related message isn't inserted
        message, contributor = process_github_comment_contributors(message, tool_source, tool_version, data_source)

        if is_issue_message(message["html_url"]):

            try:
                issue_id = issue_url_to_id_map[message["issue_url"]]
                related_pr_or_issue_found = True
            except KeyError:
                logger.info(f"{task_name}: Could not find related pr")
                logger.info(f"{task_name}: We were searching for: {message['id']}")
                logger.info(f"{task_name}: Skipping")
                continue

            issue_message_ref_data = extract_needed_issue_message_ref_data(message, issue_id, repo_id, tool_source, tool_version, data_source)

            message_ref_mapping_data[message["id"]] = {
                "msg_ref_data": issue_message_ref_data,
                "is_issue": True
            }

        else:

            try:
                pull_request_id = pr_issue_url_to_id_map[message["issue_url"]]
                related_pr_or_issue_found = True
            except KeyError:
                logger.info(f"{task_name}: Could not find related pr")
                logger.info(f"{task_name}: We were searching for: {message['issue_url']}")
                logger.info(f"{task_name}: Skipping")
                continue

            pr_message_ref_data = extract_needed_pr_message_ref_data(message, pull_request_id, repo_id, tool_source, tool_version, data_source)


            message_ref_mapping_data[message["id"]] = {
                "msg_ref_data": pr_message_ref_data,
                "is_issue": False
            }

        if related_pr_or_issue_found:

            message_dicts.append(
                            extract_needed_message_data(message, platform_id, repo_id, tool_source, tool_version, data_source)
            )

            if contributor is not None:

                contributors.append(contributor)

    contributors = remove_duplicate_dicts(contributors)

    logger.info(f"{task_name}: Inserting {len(contributors)} contributors")
    augur_db.insert_data(contributors, Contributor, ["cntrb_id"])

    logger.info(f"{task_name}: Inserting {len(message_dicts)} messages")
    message_natural_keys = ["platform_msg_id", "pltfrm_id"]
    message_return_columns = ["msg_id", "platform_msg_id"]
    message_string_fields = ["msg_text"]
    message_return_data = augur_db.insert_data(message_dicts, Message, message_natural_keys, 
                                                return_columns=message_return_columns, string_fields=message_string_fields)
    if message_return_data is None:
        return

    pr_message_ref_dicts = []
    issue_message_ref_dicts = []
    for data in message_return_data:

        augur_msg_id = data["msg_id"]
        platform_message_id = data["platform_msg_id"]

        ref = message_ref_mapping_data[platform_message_id]
        message_ref_data = ref["msg_ref_data"]
        message_ref_data["msg_id"] = augur_msg_id

        if ref["is_issue"] is True:
            issue_message_ref_dicts.append(message_ref_data)
        else:
            pr_message_ref_dicts.append(message_ref_data)

    logger.info(f"{task_name}: Inserting {len(pr_message_ref_dicts)} pr messages ref rows")
    pr_message_ref_natural_keys = ["pull_request_id", "pr_message_ref_src_comment_id"]
    augur_db.insert_data(pr_message_ref_dicts, PullRequestMessageRef, pr_message_ref_natural_keys)

    logger.info(f"{task_name}: Inserting {len(issue_message_ref_dicts)} issue messages ref rows")
    issue_message_ref_natural_keys = ["issue_id", "issue_msg_ref_src_comment_id"]
    augur_db.insert_data(issue_message_ref_dicts, IssueMessageRef, issue_message_ref_natural_keys)

    logger.info(f"{task_name}: Inserted {len(message_dicts)} messages. {len(issue_message_ref_dicts)} from issues and {len(pr_message_ref_dicts)} from prs")


def is_issue_message(html_url):

    return '/pull/' not in html_url


def process_github_comment_contributors(message, tool_source, tool_version, data_source):

    contributor = extract_needed_contributor_data(message["user"], tool_source, tool_version, data_source)
    if contributor:
        message["cntrb_id"] = contributor["cntrb_id"]
    else:
        message["cntrb_id"] = None

    return message, contributor


# this function finds a dict in a list of dicts. 
# This is done by searching all the dicts for the given key that has the specified value
def find_dict_in_list_of_dicts(data, key, value):

    return next((item for item in data if item[key] == value), None)