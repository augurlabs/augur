# SPDX-License-Identifier: MIT
import logging
import click
import sqlalchemy as s
from datetime import datetime
import httpx
from collections import Counter

from augur.application.cli import test_connection, test_db_connection 

from augur.application.db.engine import DatabaseEngine
from augur.tasks.github.util.github_api_key_handler import GithubApiKeyHandler


logger = logging.getLogger(__name__)

@click.group("github", short_help="Github utilities")
def cli():
    pass

@cli.command("api-keys")
@test_connection
@test_db_connection
def update_api_key():
    """
    Get the ratelimit of Github API keys
    """

    with DatabaseEngine() as engine, engine.connect() as connection:

        get_api_keys_sql = s.sql.text(
            """
            SELECT value as github_key from config Where section_name='Keys' AND setting_name='github_api_key'
            UNION All
            SELECT access_token as github_key from worker_oauth where platform='github' ORDER BY github_key DESC;
            """
        )

        result = connection.execute(get_api_keys_sql).fetchall()
        keys = [x[0] for x in result]
    
        with httpx.Client() as client:

            invalid_keys = []
            valid_key_data = []
            for key in keys:
                core_key_data, graphql_key_data = GithubApiKeyHandler.get_key_rate_limit(client, key)
                if core_key_data is None or graphql_key_data is None:
                    invalid_keys.append(key)
                else:
                    valid_key_data.append((key, core_key_data, graphql_key_data))

            valid_key_data = sorted(valid_key_data, key=lambda x: x[1]["requests_remaining"])

            core_request_header = "Core Requests Left"
            core_reset_header = "Core Reset Time"
            graphql_request_header = "Graphql Requests Left"
            graphql_reset_header = "Graphql Reset Time"
            print(f"{'Key'.center(40)}   {core_request_header}   {core_reset_header.center(24)}   {graphql_request_header}   {graphql_reset_header.center(24)}")  
            for key, core_key_data, graphql_key_data in valid_key_data:
                core_requests = str(core_key_data['requests_remaining']).center(len(core_request_header))
                core_reset_time = str(epoch_to_local_time_with_am_pm(core_key_data["reset_epoch"])).center(len(core_reset_header))

                graphql_requests = str(graphql_key_data['requests_remaining']).center(len(graphql_request_header))
                graphql_reset_time = str(epoch_to_local_time_with_am_pm(graphql_key_data["reset_epoch"])).center(len(graphql_reset_header))

                print(f"{key} | {core_requests} | {core_reset_time} | {graphql_requests} | {graphql_reset_time} |")

            valid_key_list = [x[0] for x in valid_key_data]
            duplicate_keys = find_duplicates(valid_key_list)
            if len(duplicate_keys) > 0:
                print("\n\nWARNING: There are duplicate keys this will slow down collection")
                print("Duplicate keys".center(40))
                for key in duplicate_keys:
                    print(key)


            if len(invalid_keys) > 0:
                invalid_key_header = "Invalid Keys".center(40)
                print("\n")
                print(invalid_key_header)
                for key in invalid_keys:
                    print(key)
                print("")


                                        
    engine.dispose()

def epoch_to_local_time_with_am_pm(epoch):
    # Convert epoch to local time with timezone awareness
    local_time = datetime.fromtimestamp(epoch).astimezone()
    formatted_time = local_time.strftime('%I:%M %p %Z (UTC%z)').center(24)
    return formatted_time

def find_duplicates(lst):
    counter = Counter(lst)
    return [item for item, count in counter.items() if count > 1]

