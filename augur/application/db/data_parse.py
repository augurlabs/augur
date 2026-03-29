"""
This file contains functions that take the api response 
and return only the data that the database needs
"""
from augur.tasks.util.AugurUUID import GithubUUID, GitlabUUID
import sqlalchemy as s

from typing import List


# retrieve only the needed data for pr labels from the api response
def extract_needed_pr_label_data(labels: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:

    if len(labels) == 0:
        return []

    label_dicts = []
    for label in labels:

        label_dict = {
            # store the pr_url data on in the pr label data for now so we can relate it back to a pr later
            'pr_src_id': int(label['id']),
            'pr_src_node_id': label['node_id'],
            'pr_src_url': label['url'],
            'pr_src_description': label['name'],
            'pr_src_color': label['color'],
            'pr_src_default_bool': label['default'],
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'repo_id': repo_id
        }

        # label_obj = PullRequestLabels(**label_dict)

        label_dicts.append(label_dict)

    return label_dicts


def extract_needed_mr_label_data(labels: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:
    """
    Retrieve only the needed data for mr label data from the api response

    Arguments:
        labels: List of dictionaries of label data
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of parsed label dicts
    """

    if len(labels) == 0:
        return []

    label_dicts = []
    for label in labels:

        label_dict = {
            'pr_src_id': label['id'],
            'pr_src_node_id': None,
            'pr_src_url': None,
            'pr_src_description': label['name'],
            'pr_src_color': label['color'],
            # TODO: Populate this by making an api call for each label
            'pr_src_default_bool': None,
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'repo_id': repo_id
        }

        label_dicts.append(label_dict)

    return label_dicts


def extract_needed_pr_assignee_data(assignees: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:
    """
    Retrieve only the needed data for pr assignees from the api response

    Arguments:
        assignees: List of dictionaries of asignee data
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of parsed asignee dicts
    """

    if len(assignees) == 0:
        return []


    assignee_dicts = []
    for assignee in assignees:

        assignee_dict = {
            'contrib_id': assignee["cntrb_id"],
            'pr_assignee_src_id': int(assignee['id']),
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'repo_id': repo_id
        }

        assignee_dicts.append(assignee_dict)
 
    return assignee_dicts

def extract_needed_merge_request_assignee_data(assignees: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:
    """
    Retrieve only the needed data for merge request assignees from the api response

    Arguments:
        assignees: List of dictionaries of asignee data
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of parsed asignee dicts
    """

    if len(assignees) == 0:
        return []

    assignee_dicts = []
    for assignee in assignees:

        assignee_dict = {
                'contrib_id': assignee["cntrb_id"],
                'repo_id': repo_id,
                'pr_assignee_src_id': assignee["id"],
                'tool_source': tool_source,
                'tool_version': tool_version,
                'data_source': data_source
            }

        assignee_dicts.append(assignee_dict)
 
    return assignee_dicts



def extract_needed_pr_reviewer_data(reviewers: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:
    """
    Retrieve only the needed data for pr reviewers from the api response

    Arguments:
        reviewers: List of dictionaries of reviewer data
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of parsed reviewer dicts
    """

    if len(reviewers) == 0:
        return []

    reviewer_dicts = []
    for reviewer in reviewers:

        reviewer_dict = {
            'cntrb_id': reviewer["cntrb_id"],
            'pr_reviewer_src_id': int(float(reviewer['id'])),
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'repo_id': repo_id
        }

        reviewer_dicts.append(reviewer_dict)


    return reviewer_dicts

def extract_needed_pr_metadata(metadata_list: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:

    if len(metadata_list) == 0:
        return []

    metadata_dicts = []
    for meta in metadata_list:

        metadata_dict = {
            'pr_head_or_base': meta['pr_head_or_base'],
            'pr_src_meta_label': meta['label'],
            'pr_src_meta_ref': meta['ref'],
            'pr_sha': meta['sha'],
            # Cast as int for the `nan` user by SPG on 11/28/2021; removed 12/6/2021
            'cntrb_id': meta["cntrb_id"] if "cntrb_id" in meta else None,
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'repo_id': repo_id
        }

        metadata_dicts.append(metadata_dict)

    return metadata_dicts


def extract_pr_review_message_ref_data(comment: dict, augur_pr_review_id, github_pr_review_id, repo_id: int, tool_version: str, data_source: str) -> dict:

    pr_review_comment_message_ref = {
        # msg_id turned up null when I removed the cast to int ..
        'msg_id': comment["msg_id"],
        'pr_review_id': augur_pr_review_id,
        'pr_review_msg_url': comment['url'],
        'pr_review_src_id': int(github_pr_review_id),
        'pr_review_msg_src_id': int(comment['id']),
        'pr_review_msg_node_id': comment['node_id'],
        'pr_review_msg_diff_hunk': comment['diff_hunk'],
        'pr_review_msg_path': comment['path'],
        'pr_review_msg_position': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            # 12/6/2021 - removed casting from value check
            comment['position']
        ) else comment['position'],
        'pr_review_msg_original_position': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            # 12/6/2021 - removed casting from value check
            comment['original_position']
        ) else comment['original_position'],
        'pr_review_msg_commit_id': str(comment['commit_id']),
        'pr_review_msg_original_commit_id': str(comment['original_commit_id']),
        'pr_review_msg_updated_at': comment['updated_at'],
        'pr_review_msg_html_url': comment['html_url'],
        'pr_url': comment['pull_request_url'],
        'pr_review_msg_author_association': comment['author_association'],
        'pr_review_msg_start_line': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            # 12/6/2021 - removed casting from value check
            comment['start_line']
        ) else comment['start_line'],
        'pr_review_msg_original_start_line': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            # 12/6/2021 - removed casting from value check
            comment['original_start_line']
        ) else int(comment['original_start_line']),
        'pr_review_msg_start_side': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            str(comment['start_side'])
        ) else str(comment['start_side']),
        'pr_review_msg_line': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            # 12/6/2021 - removed casting from value check
            comment['line']
        ) else int(comment['line']),
        'pr_review_msg_original_line': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            # 12/6/2021 - removed casting from value check
            comment['original_line']
        ) else int(comment['original_line']),
        'pr_review_msg_side': s.sql.expression.null() if not (  # This had to be changed because "None" is JSON. SQL requires NULL SPG 11/28/2021
            str(comment['side'])
        ) else str(comment['side']),
        'tool_source': 'pull_request_reviews model',
        'tool_version': tool_version + "_reviews",
        'data_source': data_source,
        'repo_id': repo_id
    }

    # pr_comment_msg_ref = {
    #     'pull_request_id': pr_id,
    #     # to cast, or not to cast. That is the question. 12/6/2021
    #     'msg_id': msg_id,
    #     'pr_message_ref_src_comment_id': int(comment['id']),
    #     'pr_message_ref_src_node_id': comment['node_id'],
    #     'tool_source': tool_source,
    #     'tool_version': tool_version,
    #     'data_source': data_source,
    #     'repo_id': repo_id
    # }

    return pr_review_comment_message_ref


def extract_pr_event_data(event: dict, pr_id: int, gh_src_id: int, platform_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:

    pr_event = {
        'pull_request_id': pr_id,
        'cntrb_id': event["cntrb_id"] if "cntrb_id" in event else None,
        'action': event['event'],
        'action_commit_hash': None,
        'created_at': event['created_at'],
        'issue_event_src_id': event["id"],
        'node_id': event['node_id'],
        'node_url': event['url'],
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source,
        'pr_platform_event_id': gh_src_id,
        'platform_id': platform_id,
        'repo_id': repo_id
    }

    return pr_event


def extract_issue_event_data(event: dict, issue_id: int, platform_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:

    issue_event = {
        'issue_event_src_id': int(event['id']),
        'issue_id': issue_id,
        'node_id': event['node_id'],
        'node_url': event['url'],
        'cntrb_id': event["cntrb_id"] if "cntrb_id" in event else None,
        'created_at': event['created_at'] if (
            event['created_at']
        ) else None,
        'action': event['event'],
        'action_commit_hash': event['commit_id'],
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source,
        'repo_id': repo_id,
        'platform_id': platform_id
    }

    return issue_event


def extract_needed_issue_assignee_data(assignees: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:

    if len(assignees) == 0:
        return []


    assignee_dicts = []
    for assignee in assignees:

        assignee_dict = {
            'cntrb_id': assignee["cntrb_id"], # # this is added to the data by the function process_issue_contributors in issue_tasks.py
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'issue_assignee_src_id': int(assignee['id']),
            'issue_assignee_src_node': assignee['node_id'],
            'repo_id': repo_id 
        }

        assignee_dicts.append(assignee_dict)

    return assignee_dicts

def extract_needed_gitlab_issue_assignee_data(assignees: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:
    """
    Retrieve only the needed data for gitlab issue assignees from the api response

    Arguments:
        assignees: List of dictionaries of gitlab assignee data
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of parsed assignee dicts
    """

    if len(assignees) == 0:
        return []

    assignee_dicts = []
    for assignee in assignees:

        assignee_dict = {
            "cntrb_id": assignee["cntrb_id"],
            "tool_source": tool_source,
            "tool_version": tool_version,
            "data_source": data_source,
            "issue_assignee_src_id": assignee['id'],
            "issue_assignee_src_node": None,
            "repo_id": repo_id
        }

        assignee_dicts.append(assignee_dict)

    return assignee_dicts



# retrieve only the needed data for pr labels from the api response
def extract_needed_issue_label_data(labels: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:

    if len(labels) == 0:
        return []

    label_dicts = []
    for label in labels:

        label_dict = {
            'label_text': label['name'],
            'label_description': label['description'] if 'description' in label else None,
            'label_color': label['color'],
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'label_src_id': int(label['id']),
            'label_src_node_id': label['node_id'],
            'repo_id': repo_id 
        }

        # label_obj = PullRequestLabels(**label_dict)

        label_dicts.append(label_dict)

    return label_dicts


def extract_needed_gitlab_issue_label_data(labels: List[dict], repo_id: int, tool_source: str, tool_version: str, data_source: str) -> List[dict]:
    """
    Retrieve only the needed data for gitlab issue labels from the api response

    Arguments:
        labels: List of dictionaries of gitlab issue label data
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of parsed label dicts
    """

    if len(labels) == 0:
        return []

    label_dicts = []
    for label in labels:

        label_dict = {
            "label_text": label["name"],
            "label_description": label.get("description", None),
            "label_color": label['color'],
            "tool_source": tool_source,
            "tool_version": tool_version,
            "data_source": data_source,
            "label_src_id": label['id'],
            "label_src_node_id": None, 
            "repo_id": repo_id
        }

        label_dicts.append(label_dict)

    return label_dicts



def extract_needed_issue_message_ref_data(message: dict, issue_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:
    """
    Retrieve only the needed data for pr labels from the api response

    Arguments:
        message: Message data dict
        issue_id: id of the issue
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        Dict of message ref data.
    """

    message_ref_dict = {
        'issue_id': issue_id,
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source,
        'issue_msg_ref_src_comment_id': int(message['id']),
        'issue_msg_ref_src_node_id': message['node_id'],
        'repo_id': repo_id
    }

    return message_ref_dict

# retrieve only the needed data for pr labels from the api response
def extract_needed_pr_message_ref_data(comment: dict, pull_request_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:

    message_ref_dict = {
            'pull_request_id': pull_request_id,
            'pr_message_ref_src_comment_id': int(comment['id']),
            'pr_message_ref_src_node_id': comment['node_id'],
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
            'repo_id': repo_id
    }
                

    return message_ref_dict
     

def extract_needed_pr_data(pr, repo_id, tool_source, tool_version):
    """
    Retrieve only the needed data for the pr api response

    Arguments:
        pr: PR data dict
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data

    
    Returns:
        Parsed pr dict
    """

    pr = {
        'repo_id': repo_id,
        'pr_url': pr['url'],
        # 1-22-2022 inconsistent casting; sometimes int, sometimes float in bulk_insert
        'pr_src_id': int(str(pr['id']).encode(encoding='UTF-8').decode(encoding='UTF-8')),
        # 9/20/2021 - This was null. No idea why.
        'pr_src_node_id': pr['node_id'],
        'pr_html_url': pr['html_url'],
        'pr_diff_url': pr['diff_url'],
        'pr_patch_url': pr['patch_url'],
        'pr_issue_url': pr['issue_url'],
        'pr_augur_issue_id': None,
        'pr_src_number': pr['number'],
        'pr_src_state': pr['state'],
        'pr_src_locked': pr['locked'],
        'pr_src_title': str(pr['title']),
        'pr_augur_contributor_id': pr["cntrb_id"],
        ### Changed to int cast based on error 12/3/2021 SPG (int cast above is first change on 12/3)
        'pr_body': str(pr['body']).encode(encoding='UTF-8', errors='backslashreplace').decode(encoding='UTF-8', errors='ignore') if (
            pr['body']
        ) else None,
        'pr_created_at': pr['created_at'],
        'pr_updated_at': pr['updated_at'],
        'pr_closed_at': None if not (
            pr['closed_at']
        ) else pr['closed_at'],
        'pr_merged_at': None if not (
            pr['merged_at']
        ) else pr['merged_at'],
        'pr_merge_commit_sha': pr['merge_commit_sha'],
        'pr_teams': None,
        'pr_milestone': None,
        'pr_commits_url': pr['commits_url'],
        'pr_review_comments_url': pr['review_comments_url'],
        'pr_review_comment_url': pr['review_comment_url'],
        'pr_comments_url': pr['comments_url'],
        'pr_statuses_url': pr['statuses_url'],
        'pr_meta_head_id': None if not (
            pr['head']
        ) else pr['head']['label'],
        'pr_meta_base_id': None if not (
            pr['base']
        ) else pr['base']['label'],
        'pr_src_issue_url': pr['issue_url'],
        'pr_src_comments_url': pr['comments_url'],
        'pr_src_review_comments_url': pr['review_comments_url'],
        'pr_src_commits_url': pr['commits_url'],
        'pr_src_statuses_url': pr['statuses_url'],
        'pr_src_author_association': pr['author_association'],
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': 'GitHub API'
    }

    return pr

def extract_needed_issue_data(issue: dict, repo_id: int, tool_source: str, tool_version: str, data_source: str):
    """
    Retrieve only the needed data for the issue api response

    Arguments:
        issue: Issue data dict
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: platform source

    
    Returns:
        Parsed issue dict
    """

    dict_data = {
        'cntrb_id': None, # this the contributor who closed the issue
        'repo_id': repo_id,
        'reporter_id': issue["cntrb_id"], # this is the contributor who opened the issue
        'pull_request': None,
        'pull_request_id': None,
        'created_at': issue['created_at'],
        'issue_title': str(issue['title']).encode(encoding='UTF-8', errors='backslashreplace').decode(encoding='UTF-8', errors='ignore') if (
            issue['title']
        ) else None,
        # 'issue_body': issue['body'].replace('0x00', '____') if issue['body'] else None,
        'issue_body': str(issue['body']).encode(encoding='UTF-8', errors='backslashreplace').decode(encoding='UTF-8', errors='ignore') if (
            issue['body']
        ) else None,
        'comment_count': issue['comments'],
        'updated_at': issue['updated_at'],
        'closed_at': issue['closed_at'],
        'repository_url': issue['repository_url'],
        'issue_url': issue['url'],
        'labels_url': issue['labels_url'],
        'comments_url': issue['comments_url'],
        'events_url': issue['events_url'],
        'html_url': issue['html_url'],
        'issue_state': issue['state'],
        'issue_node_id': issue['node_id'],
        'gh_issue_id': issue['id'],
        'gh_issue_number': issue['number'],
        'gh_user_id': issue['user']['id'],
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source
        }

    return dict_data

def extract_needed_message_data(comment: dict, platform_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str):

    dict_data = {
        'pltfrm_id': platform_id,
        'msg_text': str(comment['body']).encode(encoding='UTF-8', errors='backslashreplace').decode(encoding='UTF-8', errors='ignore') if (
            comment['body']
        ) else None,
        'msg_timestamp': comment['created_at'],
        'cntrb_id': comment["cntrb_id"],
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source,
        'repo_id': repo_id,
        'platform_msg_id': int(comment['id']),
        'platform_node_id': comment['node_id']
    }

    return dict_data

def extract_needed_contributor_data(contributor, tool_source, tool_version, data_source):

    if not contributor:
        return None

    cntrb_id = GithubUUID()
    cntrb_id["user"] = int(contributor["id"])

    # Extract all available profile fields using .get() so we never miss or crash on
    # optional keys. Email is only present when the user has made it public or when
    # the request is appropriately authenticated (see GitHub API docs).
    email = contributor.get('email')

    # TODO get and store an owner id

    contributor = {
            "cntrb_id": cntrb_id.to_UUID(),
            "cntrb_login": contributor['login'],
            "cntrb_created_at": contributor.get('created_at'),
            "cntrb_email": email,
            "cntrb_company": contributor.get('company'),
            "cntrb_location": contributor.get('location'),
            # "cntrb_type": , dont have a use for this as of now ... let it default to null
            "cntrb_canonical": email,
            "cntrb_full_name": contributor.get('name'),
            "gh_user_id": contributor['id'],
            "gh_login": str(contributor['login']),  ## cast as string by SPG on 11/28/2021 due to `nan` user
            "gh_url": contributor.get('url'),
            "gh_html_url": contributor.get('html_url'),
            "gh_node_id": contributor.get('node_id'),
            "gh_avatar_url": contributor.get('avatar_url'),
            "gh_gravatar_id": contributor.get('gravatar_id'),
            "gh_followers_url": contributor.get('followers_url'),
            "gh_following_url": contributor.get('following_url'),
            "gh_gists_url": contributor.get('gists_url'),
            "gh_starred_url": contributor.get('starred_url'),
            "gh_subscriptions_url": contributor.get('subscriptions_url'),
            "gh_organizations_url": contributor.get('organizations_url'),
            "gh_repos_url": contributor.get('repos_url'),
            "gh_events_url": contributor.get('events_url'),
            "gh_received_events_url": contributor.get('received_events_url'),
            "gh_type": contributor.get('type'),
            "gh_site_admin": contributor.get('site_admin'),
            "cntrb_last_used" : contributor.get('updated_at'),
            "tool_source": tool_source,
            "tool_version": tool_version,
            "data_source": data_source
        }

    return contributor

def extract_needed_gitlab_contributor_data(contributor, tool_source, tool_version,  data_source):

    if not contributor:
        return None

    cntrb_id = GitlabUUID()   
    cntrb_id["user"] = contributor["id"]

    contributor = {
            "cntrb_id": cntrb_id.to_UUID(),
            "cntrb_login": contributor['username'],
            "cntrb_created_at": contributor['created_at'] if 'created_at' in contributor else None,
            "cntrb_email": contributor['email'] if 'email' in contributor else None,
            "cntrb_company": contributor['company'] if 'company' in contributor else None,
            "cntrb_location": contributor['location'] if 'location' in contributor else None,
            # "cntrb_type": , dont have a use for this as of now ... let it default to null
            "cntrb_canonical": contributor['email'] if 'email' in contributor else None,
            "gh_user_id": contributor['id'],
            "gh_login": str(contributor['username']),  ## cast as string by SPG on 11/28/2021 due to `nan` user
            "gh_url": contributor['web_url'],
            "gh_html_url": None,
            "gh_node_id": None,
            "gh_avatar_url": contributor['avatar_url'],
            "gh_gravatar_id": None,
            "gh_followers_url": None,
            "gh_following_url": None,
            "gh_gists_url": None,
            "gh_starred_url": None,
            "gh_subscriptions_url": None,
            "gh_organizations_url": None,
            "gh_repos_url": None,
            "gh_events_url": None,
            "gh_received_events_url": None,
            "gh_type": None,
            "gh_site_admin": None,
            "cntrb_last_used" : None,
            "cntrb_full_name" : None,
            "tool_source": tool_source,
            "tool_version": tool_version,
            "data_source": data_source
        }

    return contributor


def extract_needed_clone_history_data(clone_history_data:List[dict], repo_id:int):

    if len(clone_history_data) == 0:
        return []

    clone_data_dicts = []
    for clone in clone_history_data:
        clone_data_dict = {
            'repo_id': repo_id,
            'clone_data_timestamp': clone['timestamp'],
            'count_clones': clone['count'],
            'unique_clones': clone['uniques']
        }
        clone_data_dicts.append(clone_data_dict)

    return clone_data_dicts

def extract_needed_pr_review_data(review, pull_request_id, repo_id, platform_id, tool_version, data_source):

    review_row =  {
                'pull_request_id': pull_request_id,
                'cntrb_id': review["cntrb_id"],
                'pr_review_author_association': review['author_association'],
                'pr_review_state': review['state'],
                'pr_review_body': str(review['body']).encode(encoding='UTF-8',errors='backslashreplace').decode(encoding='UTF-8',errors='ignore') if (
                    review['body']
                ) else None,
                'pr_review_submitted_at': review['submitted_at'] if (
                    'submitted_at' in review
                ) else None,
                'pr_review_src_id': int(float(review['id'])), #12/3/2021 cast as int due to error. # Here, `pr_review_src_id` is mapped to `id` SPG 11/29/2021. This is fine. Its the review id.
                'pr_review_node_id': review['node_id'],
                'pr_review_html_url': review['html_url'],
                'pr_review_pull_request_url': review['pull_request_url'],
                'pr_review_commit_id': review['commit_id'] if 'commit_id' in review else None,
                'tool_source': 'pull_request_reviews model',
                'tool_version': tool_version+ "_reviews",
                'data_source': data_source,
                'repo_id': repo_id,
                'platform_id': platform_id 
            }

    return review_row

def extract_needed_pr_data_from_gitlab_merge_request(pr, repo_id, tool_source, tool_version):
    """
    Retrieve only the needed data for the pr gitlab api response

    Arguments:
        pr: PR data dict
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data

    
    Returns:
        Parsed pr dict
    """
    pr_closed_datetime = pr['closed_at']
    pr_merged_datetime = pr['merged_at']

    if not pr_closed_datetime:
        pr_closed_datetime = pr_merged_datetime

    pr_dict = {
        'repo_id': repo_id,
        'pr_url': pr['web_url'],
        'pr_src_id': pr['id'],
        'pr_src_node_id': None,
        'pr_html_url': pr['web_url'],
        'pr_diff_url': None,
        'pr_patch_url': None,
        'pr_issue_url': None,
        'pr_augur_issue_id': None,
        'pr_src_number': pr['iid'],
        'pr_src_state': pr['state'],
        'pr_src_locked': pr['discussion_locked'],
        'pr_src_title': pr['title'],
        'pr_augur_contributor_id': pr["cntrb_id"],
        'pr_body': pr['description'],
        'pr_created_at': pr['created_at'],
        'pr_updated_at': pr['updated_at'],
        'pr_closed_at': pr_closed_datetime,
        'pr_merged_at': pr_merged_datetime,
        'pr_merge_commit_sha': pr['merge_commit_sha'],
        'pr_teams': None,
        'pr_milestone': pr['milestone'].get('title') if pr['milestone'] else None,
        'pr_commits_url': None,
        'pr_review_comments_url': None,
        'pr_review_comment_url': None,
        'pr_comments_url': None,
        'pr_statuses_url': None,
        'pr_meta_head_id': None,
        'pr_meta_base_id': None,
        'pr_src_issue_url': None,
        'pr_src_comments_url': None,  
        'pr_src_review_comments_url': None,  
        'pr_src_commits_url': None, 
        'pr_src_statuses_url': None,
        'pr_src_author_association': None,
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': 'Gitlab API'
    }

    return pr_dict


def extract_needed_issue_data_from_gitlab_issue(issue: dict, repo_id: int, tool_source: str, tool_version: str, data_source: str):
    """
    Retrieve only the needed data for the issue gitlab api response

    Arguments:
        issue: Issue data dict
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: platform source

    
    Returns:
        Parsed issue dict
    """

    issue_dict = {
            "repo_id": repo_id,
            "reporter_id": issue['cntrb_id'],
            "pull_request": None,
            "pull_request_id": None,
            "created_at": issue['created_at'],
            "issue_title": issue['title'],
            "issue_body": issue['description'] if 'description' in issue else None,
            "comment_count": issue['user_notes_count'],
            "updated_at": issue['updated_at'],
            "closed_at": issue['closed_at'],
            "repository_url": issue['_links']['project'],
            "issue_url": issue['_links']['self'],
            "labels_url": None,
            "comments_url": issue['_links']['notes'],
            "events_url": None,
            "html_url": issue['_links']['self'],
            "issue_state": issue['state'],
            "issue_node_id": None,
            "gh_issue_id": issue['id'],
            "gh_issue_number": issue['iid'],
            "gh_user_id": issue['author']['id'],
            "tool_source": tool_source,
            "tool_version": tool_version,
            "data_source": data_source
    }

    return issue_dict
    


def extract_gitlab_mr_event_data(event: dict, pr_id: int, platform_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:
    """
    Retrieve only the needed data for the mr event gitlab api response

    Arguments:
        event: Event data dict
        pr_id: id of the pr
        platform_id: id of the platform
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: platform source

    
    Returns:
        Parsed event dict
    """

    mr_event = {
        'pull_request_id': pr_id,
        'cntrb_id': None,
        'action': event['action_name'],
        'action_commit_hash': None,
        'created_at': event['created_at'],
        'issue_event_src_id': event['target_id'],
        'repo_id': repo_id,
        'platform_id': platform_id,
        'node_id': None,
        'node_url': None,
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source
    }

    return mr_event

def extract_gitlab_issue_event_data(event: dict, issue_id: int, platform_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:
    """
    Retrieve only the needed data for the issue event gitlab api response

    Arguments:
        event: Event data dict
        issue_id: id of the issue
        platform_id: id of the platform
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: platform source

    
    Returns:
        Parsed event dict
    """

    issue_event = {
        "issue_event_src_id": event['target_id'],
        "issue_id": issue_id,
        "node_id": None,
        "node_url": None,
        "cntrb_id": None,
        "created_at": event['created_at'],
        "action": event["action_name"],
        "action_commit_hash": None,
        "platform_id": platform_id,
        "repo_id" : repo_id,
        "tool_source": tool_source,
        "tool_version": tool_version,
        "data_source": data_source
    }

    return issue_event


def extract_needed_mr_reviewer_data(data: List[dict], pull_request_id, tool_source: str, tool_version: str, data_source: str) -> List[dict]:
    """
    Retrieve only the needed data for pr reviewers from the api response

    Arguments:
        data: List of dictionaries that contain mr reviewer data to parse
        pull_request_id: id of the PR
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of extracted relevant data from needed mr reviwer data
    """

    if len(data) == 0:
        return []
    
    reviewer_dicts = []
    for x in data:

        for _ in x["suggested_approvers"]:

            reviewer_dict = {
                'pull_request_id': pull_request_id,
                'cntrb_id': None,
                'tool_source': tool_source,
                'tool_version': tool_version,
                'data_source': data_source
            }

            reviewer_dicts.append(reviewer_dict)

    return reviewer_dicts


def extract_needed_mr_commit_data(commit, repo_id, pull_request_id, tool_source, tool_version, data_source):
    """
    Retrieve only the needed data for mr commit data from the api response

    Arguments:
        commit: commit data dictionary
        repo_id: augur id of the repository
        pull_request_id: id of the PR
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        Dictionary of the extracted commit data
    """

    commit = {
        'pull_request_id': pull_request_id,
        'pr_cmt_sha': commit['id'],
        'pr_cmt_node_id': None,
        'pr_cmt_message': commit['message'],
        'repo_id': repo_id,
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source,
    }

    return commit


def extract_needed_mr_file_data(gitlab_file_data, repo_id, pull_request_id, tool_source, tool_version, data_source):
    """
    Retrieve only the needed data for mr file data from the api response

    Arguments:
        gitlab_file_data: file data dictionary
        repo_id: augur id of the repository
        pull_request_id: id of the PR
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of dicts of parsed gitlab file changes
    """
    files = []

    changes = gitlab_file_data["changes"]
    for file_changes in changes:
        try:
            deletes = int(file_changes['diff'].split('@@')[1].strip().split(' ')[0].split(',')[1])
            adds = int(file_changes['diff'].split('@@')[1].strip().split(' ')[1].split(',')[1])
        except Exception:
            deletes = 0
            adds = 0

        file_dict = {
            'pull_request_id': pull_request_id,
            'repo_id': repo_id,
            'pr_file_additions': adds,
            'pr_file_deletions': deletes,
            'pr_file_path': file_changes['old_path'],
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source,
        }

        files.append(file_dict)

    return files


def extract_needed_mr_metadata(mr_dict, repo_id, pull_request_id, tool_source, tool_version, data_source):
    """
    Retrieve only the needed data for mr metadata from the api response

    Arguments:
        mr_dict: mr data dictionary
        repo_id: augur id of the repository
        pull_request_id: id of the PR
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        List of dicts of parsed mr metadata
    """

    diff_refs = mr_dict.get('diff_refs', {})

    head = {'sha': diff_refs.get('head_sha', None),
            'ref': mr_dict['target_branch'],
            'label': str(mr_dict['target_project_id']) + ':' + mr_dict['target_branch'],
            'author': mr_dict['author']['username'],
            'repo': str(mr_dict['target_project_id'])
            }

    base = {'sha': diff_refs.get('base_sha', None),
            'ref': mr_dict['source_branch'],
            'label': str(mr_dict['source_project_id']) + ':' + mr_dict['source_branch'],
            'author': mr_dict['author']['username'],
            'repo': str(mr_dict['source_project_id'])
            }

    pr_meta_dict = {
        'head': head,
        'base': base
    }
    all_meta = []
    for pr_side, pr_meta_data in pr_meta_dict.items():
        pr_meta = {
            'pull_request_id': pull_request_id,
            'repo_id': repo_id,
            'pr_head_or_base': pr_side,
            'pr_src_meta_label': pr_meta_data['label'],
            'pr_src_meta_ref': pr_meta_data['ref'],
            'pr_sha': pr_meta_data['sha'],
            'cntrb_id': None,
            'tool_source': tool_source,
            'tool_version': tool_version,
            'data_source': data_source
        }
        all_meta.append(pr_meta)

    return all_meta


def extract_needed_gitlab_issue_message_ref_data(message: dict, issue_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:
    """
    Extract the message id for a given message on an issue from an api response
    and connect it to the relevant repo id.

    Arguments:
        message: message data dict
        issue_id: id of the issue
        repo_id: augur id of the repository
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        Dict containing the message ref id as well as the repo id.
    """

    message_ref_dict = {
        'issue_id': issue_id,
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source,
        'issue_msg_ref_src_comment_id': int(message['id']),
        'issue_msg_ref_src_node_id': None,
        'repo_id': repo_id
    }

    return message_ref_dict


def extract_needed_gitlab_message_data(comment: dict, platform_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str):
    """
    Extract specific metadata for a comment from an api response
    and connect it to the relevant platform id.

    Arguments:
        comment: comment data dict
        platform_id: augur id of the relevant platform
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        Dict containing parsed comment text and metadata
    """

    comment_dict = {
        "repo_id": repo_id,
        "pltfrm_id": platform_id,
        "msg_text": comment['body'],
        "msg_timestamp": comment['created_at'],
        "cntrb_id": comment["cntrb_id"],
        "platform_msg_id": int(comment['id']),
        "tool_source": tool_source,
        "tool_version": tool_version,
        "data_source": data_source
    }

    return comment_dict

def extract_needed_gitlab_mr_message_ref_data(comment: dict, pull_request_id: int, repo_id: int, tool_source: str, tool_version: str, data_source: str) -> dict:
    """
    Retrieve only the needed data for pr labels from the api response

    Arguments:
        comment: comment data dict
        pull_request_id: id of the PR
        repo_id: augur id of the repository
        platform_id: augur id of the relevant platform
        tool_source: The part of augur that processed the data
        tool_version: The version of the augur task that processed the data
        data_source: The source of the data 

    
    Returns:
        Dict containing the comment, pr and repo id of the parsed comment data.
    """

    pr_msg_ref = {
        'pull_request_id': pull_request_id,
        'pr_message_ref_src_comment_id': comment['id'],
        'repo_id': repo_id,
        'pr_message_ref_src_node_id': None,
        'tool_source': tool_source,
        'tool_version': tool_version,
        'data_source': data_source
    }
                
    return pr_msg_ref 

