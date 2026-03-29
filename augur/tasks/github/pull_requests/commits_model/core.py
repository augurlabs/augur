import sqlalchemy as s
from augur.tasks.github.util.github_data_access import GithubDataAccess, UrlNotFoundException ## URLNotFoundException added to deal with percolation of 404 errors when the commits are not anywhere for a PR already captured. 
from augur.application.db.models import *
from augur.tasks.github.util.util import get_owner_repo
from augur.application.db.util import execute_session_query
from augur.application.db.lib import get_secondary_data_last_collected, get_updated_prs, get_batch_size




def pull_request_commits_model(repo_id,logger, augur_db, key_auth, full_collection=False):

    pr_commit_batch_size = get_batch_size()

    if full_collection:
        # query existing PRs and the respective url we will append the commits url to
        pr_url_sql = s.sql.text("""
                SELECT DISTINCT pr_url, pull_requests.pull_request_id
                FROM pull_requests--, pull_request_meta
                WHERE repo_id = :repo_id
            """).bindparams(repo_id=repo_id)
        pr_urls = []
        #pd.read_sql(pr_number_sql, self.db, params={})

        pr_urls = augur_db.fetchall_data_from_sql_text(pr_url_sql)#session.execute_sql(pr_number_sql).fetchall()
    
    else:
        last_collected = get_secondary_data_last_collected(repo_id).date()
        prs = get_updated_prs(repo_id, last_collected)
        pr_urls = [pr.pr_url for pr in prs]

        pr_urls = []
        for pr in prs:
            pr_urls.append({
                'pr_url': pr.pr_url,
                'pull_request_id': pr.pull_request_id
            })

    
    query = augur_db.session.query(Repo).filter(Repo.repo_id == repo_id)
    repo = execute_session_query(query, 'one')

    owner, name = get_owner_repo(repo.repo_git)

    task_name = f"{owner}/{name} Pr commits"

    logger.info(f"Getting pull request commits for repo: {repo.repo_git}")

    github_data_access = GithubDataAccess(key_auth, logger)

    pr_commits_natural_keys = ["pull_request_id", "repo_id", "pr_cmt_sha"]
    all_data = []
    for index,pr_info in enumerate(pr_urls):
        logger.info(f'{task_name}: Querying commits for pull request #{index + 1} of {len(pr_urls)}')

        commits_url = pr_info['pr_url'] + '/commits?state=all'

        if not pr_info.get('pr_url'):
            logger.warning(f"{task_name}: No pr_url found for pull request info: {pr_info}. Skipping.")
            continue

        commits_url = pr_info['pr_url'] + '/commits?state=all'

        try:
            for page_data in github_data_access.paginate_resource(commits_url):
                logger.info(f"{task_name}: Processing pr commit with hash {page_data['sha']}")
                pr_commit_row = {
                    'pull_request_id': pr_info['pull_request_id'],
                    'pr_cmt_sha': page_data['sha'],
                    'pr_cmt_node_id': page_data['node_id'],
                    'pr_cmt_message': page_data['commit']['message'],
                    'tool_source': 'pull_request_commits_model',
                    'tool_version': '0.41',
                    'data_source': 'GitHub API',
                    'repo_id': repo.repo_id,
                }
                all_data.append(pr_commit_row)

                if len(all_data) >= pr_commit_batch_size:
                    logger.info(f"{task_name}: Inserting {len(all_data)} rows")
                    augur_db.insert_data(all_data,PullRequestCommit,pr_commits_natural_keys)
                    all_data.clear()
        except UrlNotFoundException:
            logger.info(f"{task_name}: PR with url of {pr_info['pr_url']} returned 404 on commit data. Skipping.")
            continue

    if len(all_data) > 0:
        logger.info(f"{task_name}: Inserting {len(all_data)} rows")
        augur_db.insert_data(all_data,PullRequestCommit,pr_commits_natural_keys)
            





