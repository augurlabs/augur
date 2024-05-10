import logging


from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.init.celery_app import AugurCoreRepoCollectionTask
from augur.application.db.data_parse import *
from augur.tasks.github.util.github_paginator import GithubPaginator
from augur.tasks.github.util.github_task_session import GithubTaskManifest
from augur.tasks.util.worker_util import remove_duplicate_dicts
from augur.tasks.github.util.util import get_owner_repo
from augur.application.db.models import PullRequest, Message, Issue, PullRequestMessageRef, IssueMessageRef, Contributor, Repo



platform_id = 1


@celery.task(base=AugurCoreRepoCollectionTask)
def collect_github_messages(repo_git: str) -> None:

    logger = logging.getLogger(collect_github_messages.__name__)

    with GithubTaskManifest(logger) as manifest:

        augur_db = manifest.augur_db
            
        repo_id = augur_db.session.query(Repo).filter(
            Repo.repo_git == repo_git).one().repo_id

        owner, repo = get_owner_repo(repo_git)
        task_name = f"{owner}/{repo}: Message Task"
        message_data = retrieve_all_pr_and_issue_messages(repo_git, logger, manifest.key_auth, task_name)
        
        if message_data:
        
            process_messages(message_data, task_name, repo_id, logger, augur_db)

        else:
            logger.info(f"{owner}/{repo} has no messages")



def retrieve_all_pr_and_issue_messages(repo_git: str, logger, key_auth, task_name) -> None:

    owner, repo = get_owner_repo(repo_git)

    # url to get issue and pull request comments
    # this would probably be replaced
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments"

    # define logger for task
    logger.info(f"Collecting github comments for {owner}/{repo}")

    # This seems like a duplicate of what is above
    # url to get issue and pull request comments
    #url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments"

    # define database task session, that also holds authentication keys the GithubPaginator needs

    # HERE is where I think we would get all the data from this query and iterate over it for messages    
    ## < -------------- New Logic Here -------------->
    """Core SQL
    select repo_id, message_url from (
        select repo_id, pr_comments_url as message_url, 'pr' as type, pr_created_at as creation_date, pr_src_number as gh_number
        from pull_requests where repo_id=1 
        and pr_src_state != 'open' --order by pr_created_at desc, pr_src_id desc
        union 
        select repo_id, comments_url as message_url, 'issue' as type, created_at as creation_date, gh_issue_number as gh_number 
        from issues where repo_id=1 
        and issue_state != 'open' --order by created_at desc, gh_issue_number desc; 
        order by creation_date desc, gh_number desc
    ); 
    """

    # I think we could possibly have some logic to check how many messages there are already, and skip it if the API returns the same count
    """
    select pull_requests.repo_id, pr_comments_url as message_url, 'pr' as type, pr_created_at as creation_date, pr_src_number as gh_number, coalesce(COUNT(pull_request_message_ref.msg_id))  as existing_messages 
    from pull_requests
    left outer join pull_request_message_ref  on pull_requests.repo_id=pull_request_message_ref.repo_id and pull_requests.pull_request_id=pull_request_message_ref.pull_request_id
    where pull_requests.repo_id=1 
    and pull_requests.pr_src_state != 'open' 
    group by pull_requests.repo_id, message_url, type, creation_date, gh_number, pr_src_id --order by pr_created_at desc, pr_src_id desc 
    union 
    select issues.repo_id, comments_url as message_url, 'issue' as type, created_at as creation_date, gh_issue_number as gh_number, coalesce(COUNT(issue_message_ref.msg_id))  as existing_messages 
    from issues
    left outer join issue_message_ref  on issues.repo_id=issue_message_ref.repo_id and issues.issue_id=issue_message_ref.issue_id
    where issues.repo_id=1 
    and issues.issue_state != 'open' 
    group by issues.repo_id, message_url, type, creation_date, gh_number, gh_issue_number --order by created_at desc, gh_issue_number desc 
    order by creation_date desc, gh_number desc     
    """

    # Draft SQL Alchemy version. I just don't know where and how to get a session in the new architecture
    """ 
    augur_db.
    pr_query = (
        session.query(
            PullRequest.repo_id,
            PullRequest.pr_comments_url.label('message_url'),
            func.literal('pr').label('type'),
            PullRequest.pr_created_at.label('creation_date'),
            PullRequest.pr_src_number.label('gh_number'),
            func.coalesce(func.count(PullRequestMessageRef.msg_id), 0).label('existing_messages')
        )
        .outerjoin(PullRequestMessageRef, (PullRequest.repo_id == PullRequestMessageRef.repo_id) &
                (PullRequest.pull_request_id == PullRequestMessageRef.pull_request_id))
        .filter(PullRequest.repo_id == 1, PullRequest.pr_src_state != 'open')
        .group_by(PullRequest.repo_id, 'message_url', 'type', 'creation_date', 'gh_number')
    )

    issue_query = (
        session.query(
            Issue.repo_id,
            Issue.comments_url.label('message_url'),
            func.literal('issue').label('type'),
            Issue.created_at.label('creation_date'),
            Issue.gh_issue_number.label('gh_number'),
            func.coalesce(func.count(IssueMessageRef.msg_id), 0).label('existing_messages')
        )
        .outerjoin(IssueMessageRef, (Issue.repo_id == IssueMessageRef.repo_id) &
                (Issue.issue_id == IssueMessageRef.issue_id))
        .filter(Issue.repo_id == 1, Issue.issue_state != 'open')
        .group_by(Issue.repo_id, 'message_url', 'type', 'creation_date', 'gh_number')
    )

    combined_query = union_all(pr_query, issue_query).order_by('creation_date desc', 'gh_number desc')

    # Executing the query
    result = combined_query.all()
    for row in result:
        print(row)
        # for each row in the result, go get the related messages
        # call GH API for each PR or Issue (a row)
        # Check message count against message count row (api call)
        # If different:   
        #    process all the messages as before (logic): 
        # else: 
        #    keep going without doing anything 
    """
    # returns an iterable of all issues at this url (this essentially means you can treat the issues variable as a list of the issues)
    ## < -------------- The Section below could be indented and run for each pr or issue -------------->
    messages = GithubPaginator(url, key_auth, logger)

    num_pages = messages.get_num_pages()
    all_data = []
    for page_data, page in messages.iter_pages():

        if page_data is None:
            return all_data

        elif len(page_data) == 0:
            logger.debug(f"{repo.capitalize()} Messages Page {page} contains no data...returning")
            logger.info(
                f"{task_name}: Page {page} of {num_pages}")
            return all_data

        logger.info(f"{task_name}: Page {page} of {num_pages}")

        all_data += page_data
        

    return all_data
    

def process_messages(messages, task_name, repo_id, logger, augur_db):

    tool_source = "Pr comment task"
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
