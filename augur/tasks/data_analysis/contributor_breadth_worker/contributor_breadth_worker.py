#SPDX-License-Identifier: MIT
import logging
import sqlalchemy as s
from datetime import datetime

from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.github.util.github_data_access import GithubDataAccess, UrlNotFoundException
from augur.application.db.models import ContributorRepo
from augur.application.db.lib import bulk_insert_dicts
from augur.tasks.github.util.github_random_key_auth import GithubRandomKeyAuth

### This worker scans all the platform users in Augur, and pulls their platform activity 
### logs. Those are then used to analyze what repos each is working in (which will include repos not
### tracked in the Augur instance.)
### Logic: For each unique platform contributor, gather non duplicate events, using the GitHub "id"
### for the event API (GitLab coming!)

@celery.task(bind=True)
def contributor_breadth_model(self) -> None:

    engine = self.app.engine

    logger = logging.getLogger(__name__)

    tool_source = 'Contributor Breadth Worker'
    tool_version = '0.0.1'
    data_source = 'GitHub API'

    key_auth = GithubRandomKeyAuth(logger)

    # This version of the query pulls contributors who have not had any data collected yet
    # To the top of the list
    cntrb_login_query = s.sql.text("""
            SELECT DISTINCT
                gh_login,
                cntrb_id 
            FROM
                (
                SELECT DISTINCT
                    gh_login,
                    cntrb_id,
                    data_collection_date 
                FROM
                    (
                    SELECT DISTINCT
                        contributors.gh_login,
                        contributors.cntrb_id,
                        contributor_repo.data_collection_date :: DATE 
                    FROM
                        contributor_repo
                        RIGHT OUTER JOIN contributors ON contributors.cntrb_id = contributor_repo.cntrb_id 
                        AND contributors.gh_login IS NOT NULL 
                    ORDER BY
                        contributor_repo.data_collection_date :: DATE NULLS FIRST 
                    ) A 
                ORDER BY
                data_collection_date DESC NULLS FIRST 
                ) b
    """)

    with engine.connect() as connection:
        result = connection.execute(cntrb_login_query)

    current_cntrb_logins = [dict(row) for row in result.mappings()]

    cntrb_newest_events_query = s.sql.text("""
        SELECT c.gh_login, MAX(cr.created_at) as newest_event_date
        FROM contributor_repo AS cr
        JOIN contributors AS c ON cr.cntrb_id = c.cntrb_id
        GROUP BY c.gh_login;
    """)

    with engine.connect() as connection:
        cntrb_newest_events_list = connection.execute(cntrb_newest_events_query)
    
    cntrb_newest_events_list = [dict(row) for row in cntrb_newest_events_list.mappings()]

    cntrb_newest_events_map = {}
    for cntrb_event in cntrb_newest_events_list:

        gh_login = cntrb_event["gh_login"]
        newest_event_date = cntrb_event["newest_event_date"]
        
        cntrb_newest_events_map[gh_login] = newest_event_date

    github_data_access = GithubDataAccess(key_auth, logger)

    index = 1
    total = len(current_cntrb_logins)
    for cntrb in current_cntrb_logins:

        logger.info(f"Processing cntrb {index} of {total}")
        index += 1

        repo_cntrb_url = f"https://api.github.com/users/{cntrb['gh_login']}/events"

        newest_event_in_db = datetime(1970, 1, 1)
        if cntrb["gh_login"] in cntrb_newest_events_map:
            newest_event_in_db = cntrb_newest_events_map[cntrb["gh_login"]]
            

        cntrb_events = []
        try:
            for event in github_data_access.paginate_resource(repo_cntrb_url):

                cntrb_events.append(event)

                event_age = datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                if event_age < newest_event_in_db:
                    logger.info("Found cntrb events we already have...skipping the rest")
                    break

            if len(cntrb_events) == 0:
                logger.info("There are no cntrb events, or new events for this user.\n")
                continue

        except UrlNotFoundException as e:
            logger.warning(e)
            continue

        events = process_contributor_events(cntrb, cntrb_events, logger, tool_source, tool_version, data_source)

        logger.info(f"Inserting {len(events)} events")
        natural_keys = ["event_id", "tool_version"]
        bulk_insert_dicts(logger, events, ContributorRepo, natural_keys)  


def process_contributor_events(cntrb, cntrb_events, logger, tool_source, tool_version, data_source):

    cntrb_repos_insert = []
    for event_id_api in cntrb_events:
        
        repo = event_id_api.get("repo")
        
        if not repo or not repo.get("url"):
            logger.warning(
                "Skipping GitHub event due to empty repo or missing repo.url",
                extra={
                    "event_id": event_id_api.get("id"),
                    "event_type": event_id_api.get("type"),
                    "public": event_id_api.get("public"),
                    "repo": repo,
                },
            )
            continue
        
        cntrb_repos_insert.append({
            "cntrb_id": cntrb['cntrb_id'],
            "repo_git": repo['url'],
            "tool_source": tool_source,
            "tool_version": tool_version,
            "data_source": data_source,
            "repo_name": repo['name'],
            "gh_repo_id": repo['id'],
            "cntrb_category": event_id_api.get('type'),
            "event_id": int(event_id_api['id']),
            "created_at": event_id_api.get('created_at')
        })

    return cntrb_repos_insert
