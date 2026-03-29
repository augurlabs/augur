import logging
import pytest
import uuid
import sqlalchemy as s

from augur.application.db.session import DatabaseSession
from augur.application.db.models import Contributor, Issue

logger = logging.getLogger(__name__)
not_provided_cntrb_id = '00000000-0000-0000-0000-000000000000'
nan_cntrb_id = '01000000-0000-0000-0000-000000000000'

# TODO: Add test that does not pass an engine to the Session

def test_execute_sql(test_db_engine):

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    data_2 = {"cntrb_login": "amazing", "gh_user_id": 1700, "gh_login": "hello", "cntrb_id": "01003f7a-8500-0000-0000-000123002000"}
    data_3 = {"cntrb_login": "cool_guy", "gh_user_id": 230, "gh_login": "lame_guy", "cntrb_id": "01003f7a-8511-0000-0000-000123875000"}
    data_4 = {"cntrb_login": "great", "gh_user_id": 230, "gh_login": "boring", "cntrb_id": "01003f7a-8511-0000-0000-000123000000"}
    all_data = [data_1, data_2, data_3, data_4]

    try:

        with test_db_engine.connect() as connection:

            for data in all_data:

                statement = s.sql.text("""INSERT INTO "augur_data"."contributors" ("cntrb_login", "cntrb_email", "cntrb_full_name", "cntrb_company", "cntrb_created_at", "cntrb_type", "cntrb_fake", "cntrb_deleted", "cntrb_long", "cntrb_lat", "cntrb_country_code", "cntrb_state", "cntrb_city", "cntrb_location", "cntrb_canonical", "cntrb_last_used", "gh_user_id", "gh_login", "gh_url", "gh_html_url", "gh_node_id", "gh_avatar_url", "gh_gravatar_id", "gh_followers_url", "gh_following_url", "gh_gists_url", "gh_starred_url", "gh_subscriptions_url", "gh_organizations_url", "gh_repos_url", "gh_events_url", "gh_received_events_url", "gh_type", "gh_site_admin", "gl_web_url", "gl_avatar_url", "gl_state", "gl_username", "gl_full_name", "gl_id", "tool_source", "tool_version", "data_source", "data_collection_date", "cntrb_id") VALUES (:cntrb_login, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, :gh_user_id, :gh_login, 'https://api.github.com/users/ivanayov', 'https://github.com/ivanayov', 'MDQ6VXNlcjQxNjAxMzM=', 'https://avatars.githubusercontent.com/u/4160133?v=4', '', 'https://api.github.com/users/ivanayov/followers', 'https://api.github.com/users/ivanayov/following{/other_user}', 'https://api.github.com/users/ivanayov/gists{/gist_id}', 'https://api.github.com/users/ivanayov/starred{/owner}{/repo}', 'https://api.github.com/users/ivanayov/subscriptions', 'https://api.github.com/users/ivanayov/orgs', 'https://api.github.com/users/ivanayov/repos', 'https://api.github.com/users/ivanayov/events{/privacy}', 'https://api.github.com/users/ivanayov/received_events', 'User', 'false', NULL, NULL, NULL, NULL, NULL, NULL, 'Pr Task', '2.0', 'Github API', '2022-08-05 09:06:39', :cntrb_id);""")

                connection.execute(statement, **data)

        for data in all_data:

            with DatabaseSession(logger, engine=test_db_engine) as session:

                cntrb_id = data['cntrb_id']
                result = session.execute_sql(f"SELECT * FROM augur_data.contributors WHERE cntrb_id='{cntrb_id}'").fetchall()

            assert result is not None
            assert isinstance(result[0], s.engine.result.RowProxy)

            result_dict = dict(result[0])

            for key in data.keys():

                if key == 'cntrb_id':
                    assert result_dict[key] == uuid.UUID(data[key])
                    continue

                assert result_dict[key] == data[key]

    finally:

        with test_db_engine.connect() as connection:

            for data in all_data:

                cntrb_id = data["cntrb_id"]
                connection.execute(f"DELETE FROM augur_data.contributors WHERE cntrb_id='{cntrb_id}';")


def test_insert_data_with_duplicates(test_db_engine):

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    data_2 = {"cntrb_login": "amazing", "gh_user_id": 1700, "gh_login": "hello", "cntrb_id": "01003f7a-8500-0000-0000-000123002000"}
    data_3 = {"cntrb_login": "cool_guy", "gh_user_id": 230, "gh_login": "lame_guy", "cntrb_id": "01003f7a-8511-0000-0000-000123875000"}

    duplicate_data_list = [data_1, data_1, data_2, data_2, data_3]

    try:

        with DatabaseSession(logger, engine=test_db_engine) as session:

            for data in duplicate_data_list:

                session.insert_data(data, Contributor, ["cntrb_id"])


            
            cntrb_id = data_1['cntrb_id']
            result = session.execute_sql(f"SELECT * FROM augur_data.contributors WHERE cntrb_id!='{not_provided_cntrb_id}' AND cntrb_id!='{nan_cntrb_id}'").fetchall()

        assert result is not None
        assert len(result) == 3

        for row in result:
            assert isinstance(row, s.engine.result.RowProxy)
    
    finally:

        with test_db_engine.connect() as connection:

            for data in duplicate_data_list:

                cntrb_id = data["cntrb_id"]
                connection.execute(f"DELETE FROM augur_data.contributors WHERE cntrb_id='{cntrb_id}';")

def test_insert_data_with_updates(test_db_engine):

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    data_2 = data_1.copy()
    data_2["gh_user_id"] = 6
    
    try:

        with test_db_engine.connect() as connection:

            statement = s.sql.text("""INSERT INTO "augur_data"."contributors" ("cntrb_login", "cntrb_email", "cntrb_full_name", "cntrb_company", "cntrb_created_at", "cntrb_type", "cntrb_fake", "cntrb_deleted", "cntrb_long", "cntrb_lat", "cntrb_country_code", "cntrb_state", "cntrb_city", "cntrb_location", "cntrb_canonical", "cntrb_last_used", "gh_user_id", "gh_login", "gh_url", "gh_html_url", "gh_node_id", "gh_avatar_url", "gh_gravatar_id", "gh_followers_url", "gh_following_url", "gh_gists_url", "gh_starred_url", "gh_subscriptions_url", "gh_organizations_url", "gh_repos_url", "gh_events_url", "gh_received_events_url", "gh_type", "gh_site_admin", "gl_web_url", "gl_avatar_url", "gl_state", "gl_username", "gl_full_name", "gl_id", "tool_source", "tool_version", "data_source", "data_collection_date", "cntrb_id") VALUES (:cntrb_login, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, :gh_user_id, :gh_login, 'https://api.github.com/users/ivanayov', 'https://github.com/ivanayov', 'MDQ6VXNlcjQxNjAxMzM=', 'https://avatars.githubusercontent.com/u/4160133?v=4', '', 'https://api.github.com/users/ivanayov/followers', 'https://api.github.com/users/ivanayov/following{/other_user}', 'https://api.github.com/users/ivanayov/gists{/gist_id}', 'https://api.github.com/users/ivanayov/starred{/owner}{/repo}', 'https://api.github.com/users/ivanayov/subscriptions', 'https://api.github.com/users/ivanayov/orgs', 'https://api.github.com/users/ivanayov/repos', 'https://api.github.com/users/ivanayov/events{/privacy}', 'https://api.github.com/users/ivanayov/received_events', 'User', 'false', NULL, NULL, NULL, NULL, NULL, NULL, 'Pr Task', '2.0', 'Github API', '2022-08-05 09:06:39', :cntrb_id);""")

            connection.execute(statement, **data_1)

        with DatabaseSession(logger, engine=test_db_engine) as session:

            session.insert_data(data_2, Contributor, ["cntrb_id"])

        with test_db_engine.connect() as connection:

            cntrb_id = data_1['cntrb_id']
            result = connection.execute(f"SELECT * FROM augur_data.contributors WHERE cntrb_id='{cntrb_id}'").fetchall()

        assert result is not None
        assert dict(result[0])["gh_user_id"] == 6 
    
    finally:

        with test_db_engine.connect() as connection:

            cntrb_id = data_1["cntrb_id"]
            connection.execute(f"DELETE FROM augur_data.contributors WHERE cntrb_id='{cntrb_id}';")


def test_insert_data_with_bulk(test_db_engine):

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    data_2 = {"cntrb_login": "amazing", "gh_user_id": 1700, "gh_login": "hello", "cntrb_id": "01003f7a-8500-0000-0000-000123002000"}
    data_3 = {"cntrb_login": "cool_guy", "gh_user_id": 230, "gh_login": "lame_guy", "cntrb_id": "01003f7a-8511-0000-0000-000123875000"}
    data_4 = {"cntrb_login": "great", "gh_user_id": 230, "gh_login": "boring", "cntrb_id": "01003f7a-8511-0000-0000-000123000000"}
    all_data = [data_1, data_2, data_3, data_4]


    try:
        with DatabaseSession(logger, engine=test_db_engine) as session:
            session.insert_data(all_data, Contributor, ["cntrb_id"])

        with test_db_engine.connect() as connection:

            result = connection.execute(f"SELECT * FROM augur_data.contributors WHERE cntrb_id!='{not_provided_cntrb_id}' AND cntrb_id!='{nan_cntrb_id}'").fetchall()

            assert result is not None
            assert len(result) == 4

            for data in result:
                dict_data = dict(data)

                for key in dict_data.keys():
                    assert data[key] == dict_data[key]
    finally:

        with test_db_engine.connect() as connection:

            cntrb_id = data_1["cntrb_id"]
            connection.execute(f"DELETE FROM augur_data.contributors WHERE cntrb_id!='{not_provided_cntrb_id}' AND cntrb_id!='{nan_cntrb_id}';")



def test_insert_data_partial_update(test_db_engine):

    data_1 = {"cntrb_login": "Bob", "gh_user_id": 4, "gh_login": "bob", "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    data_2 = {"cntrb_login": "Bob", "gh_user_id": 6, "cntrb_id": "01003f7a-8500-0000-0000-000000000000"}
    
    try:
        with test_db_engine.connect() as connection:

            statement = s.sql.text("""INSERT INTO "augur_data"."contributors" ("cntrb_login", "cntrb_email", "cntrb_full_name", "cntrb_company", "cntrb_created_at", "cntrb_type", "cntrb_fake", "cntrb_deleted", "cntrb_long", "cntrb_lat", "cntrb_country_code", "cntrb_state", "cntrb_city", "cntrb_location", "cntrb_canonical", "cntrb_last_used", "gh_user_id", "gh_login", "gh_url", "gh_html_url", "gh_node_id", "gh_avatar_url", "gh_gravatar_id", "gh_followers_url", "gh_following_url", "gh_gists_url", "gh_starred_url", "gh_subscriptions_url", "gh_organizations_url", "gh_repos_url", "gh_events_url", "gh_received_events_url", "gh_type", "gh_site_admin", "gl_web_url", "gl_avatar_url", "gl_state", "gl_username", "gl_full_name", "gl_id", "tool_source", "tool_version", "data_source", "data_collection_date", "cntrb_id") VALUES (:cntrb_login, NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, :gh_user_id, :gh_login, 'https://api.github.com/users/ivanayov', 'https://github.com/ivanayov', 'MDQ6VXNlcjQxNjAxMzM=', 'https://avatars.githubusercontent.com/u/4160133?v=4', '', 'https://api.github.com/users/ivanayov/followers', 'https://api.github.com/users/ivanayov/following{/other_user}', 'https://api.github.com/users/ivanayov/gists{/gist_id}', 'https://api.github.com/users/ivanayov/starred{/owner}{/repo}', 'https://api.github.com/users/ivanayov/subscriptions', 'https://api.github.com/users/ivanayov/orgs', 'https://api.github.com/users/ivanayov/repos', 'https://api.github.com/users/ivanayov/events{/privacy}', 'https://api.github.com/users/ivanayov/received_events', 'User', 'false', NULL, NULL, NULL, NULL, NULL, NULL, 'Pr Task', '2.0', 'Github API', '2022-08-05 09:06:39', :cntrb_id);""")

            connection.execute(statement, **data_1)

        with DatabaseSession(logger, engine=test_db_engine) as session:

            session.insert_data(data_2, Contributor, ["cntrb_id"])

        with test_db_engine.connect() as connection:

            cntrb_id = data_1['cntrb_id']
            result = connection.execute(f"SELECT * FROM augur_data.contributors WHERE cntrb_id='{cntrb_id}'").fetchall()

        assert result is not None
        assert dict(result[0])["gh_user_id"] == 6 
    
    finally:

        with test_db_engine.connect() as connection:

            cntrb_id = data_1["cntrb_id"]
            connection.execute(f"DELETE FROM augur_data.contributors WHERE cntrb_id='{cntrb_id}';")


issue_data_with_null_strings = []
issue_data_with_null_strings.append({'cntrb_id': None, 'repo_id': 1, 'reporter_id': None, 'pull_request': None, 'pull_request_id': None, 'created_at': '2016-04-06T08:08:16Z', 'issue_title': '(Bundler: :GemRequireError)', 'issue_body': """I get this one in the clean jekyll project.\n\nResolving dependencies...\nUsing colorator 0.1\nUsing ffi 1.9.10\nUsing htmlentities 4.3.4\nUsing sass 3.4.22\nUsing rb-fsevent 0.9.7\nUsing kramdown 1.10.0\nUsing liquid 3.0.6\nUsing mercenary 0.3.5\nUsing rouge 1.10.1\nUsing safe_yaml 1.0.4\nUsing bundler 1.11.2\nUsing rb-inotify 0.9.7\nUsing jekyll-sass-converter 1.4.0\nUsing listen 3.0.6\nUsing jekyll-watch 1.3.1\nUsing jekyll 3.1.2\nUsing jekyll_pages_api 0.1.5\nUsing jekyll_pages_api_search 0.4.4\nBundle complete! 1 Gemfile dependency
                                     18 gems now installed.\nUse `bundle show [gemname]` to see where a bundled gem is installed.\nAndreass-MacBook-Pro: maukasta-blogi andreaskoutsoukos$ \nAndreass-MacBook-Pro: maukasta-blogi andreaskoutsoukos$ jekyll serve\x00\x00\nWARN: Unresolved specs during Gem: : Specification.reset: \n      jekyll-watch (~ > 1.1)\nWARN: Clearing out unresolved specs.\nPlease report a bug if this causes problems.\n/Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb: 80: in `rescue in block (2 levels) in require': There was an error while trying to load the gem 'jekyll_pages_api_search'. (Bundler::GemRequireError)\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:76:in`block (2 levels) in require'\n        from / Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb: 72: in `each'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:72:in`block in require'\n        from / Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb: 61: in `each'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:61:in`require'\n        from / Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler.rb: 99: in `require'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/jekyll-3.1.2/lib/jekyll/plugin_manager.rb:34:in`require_from_bundler'\n        from / Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/jekyll-3.1.2/bin/jekyll: 9: in `<top (required) > '\n        from /Users/andreaskoutsoukos/.rbenv/versions/2.2.1/bin/jekyll:23:in`load'\n        from / Users/andreaskoutsoukos/.rbenv/versions/2.2.1/bin/jekyll: 23: in `<main > '\n" 'comment_count': 0""",
                                    'comment_count': 0, 'updated_at': '2016-04-06T08:08:16Z', 'closed_at': None, 'repository_url': 'https: //api.github.com/repos/18F/jekyll_pages_api_search', 'issue_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/31', 'labels_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/30/labels{/name}', 'comments_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/30/comments', 'events_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/30/events', 'html_url': 'https://github.com/18F/jekyll_pages_api_search/issues/30', 'issue_state': 'open', 'issue_node_id': 'MDU6SXNzdWUxNDYyMjcwNTU=', 'gh_issue_id': 146227055, 'gh_issue_number': 30, 'gh_user_id': 196690, 'tool_source': 'Issue Task', 'tool_version': '2.0', 'data_source': 'Github API'})
issue_data_with_null_strings.append({'cntrb_id': None, 'repo_id': 1, 'reporter_id': None, 'pull_request': None, 'pull_request_id': None, 'created_at': '2016-04-06T08:08:16Z', 'issue_title': '(Bundler: :GemRequireError)', 'issue_body': "I get this one in the clean jekyll project.\n\nResolving dependencies...\nUsing colorator 0.1\nUsing ffi 1.9.10\nUsing htmlentities 4.3.4\nUsing sass 3.4.22\nUsing rb-fsevent 0.9.7\nUsing kramdown 1.10.0\nUsing liquid 3.0.6\nUsing mercenary 0.3.5\nUsing rouge 1.10.1\nUsing safe_yaml 1.0.4\nUsing bundler 1.11.2\nUsing rb-inotify 0.9.7\nUsing jekyll-sass-converter 1.4.0\nUsing listen 3.0.6\nUsing jekyll-watch 1.3.1\nUsing jekyll 3.1.2\nUsing jekyll_pages_api 0.1.5\nUsing jekyll_pages_api_search 0.4.4\nBundle complete! 1 Gemfile dependency, 18 gems now installed.\nUse `bundle show [gemname]` to see where a bundled gem is installed.\nAndreass-MacBook-Pro:maukasta-blogi andreaskoutsoukos$ \nAndreass-MacBook-Pro:maukasta-blogi andreaskoutsoukos$ jekyll serve\x00\x00\nWARN: Unresolved specs during Gem::Specification.reset:\n      jekyll-watch (~> 1.1)\nWARN: Clearing out unresolved specs.\nPlease report a bug if this causes problems.\n/Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:80:in `rescue in block (2 levels) in require': There was an error while trying to load the gem 'jekyll_pages_api_search'. (Bundler::GemRequireError)\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:76:in`block (2 levels) in require'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:72:in `each'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:72:in`block in require'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:61:in `each'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler/runtime.rb:61:in`require'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/bundler-1.11.2/lib/bundler.rb:99:in `require'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/jekyll-3.1.2/lib/jekyll/plugin_manager.rb:34:in`require_from_bundler'\n        from /Users/andreaskoutsoukos/.rvm/gems/ruby-2.2.1/gems/jekyll-3.1.2/bin/jekyll:9:in `<top (required)>'\n        from /Users/andreaskoutsoukos/.rbenv/versions/2.2.1/bin/jekyll:23:in`load'\n        from /Users/andreaskoutsoukos/.rbenv/versions/2.2.1/bin/jekyll:23:in `<main>'\n",
                                    'comment_count': 0, 'updated_at': '2016-04-06T08:08:16Z', 'closed_at': None, 'repository_url': 'https: //api.github.com/repos/18F/jekyll_pages_api_search', 'issue_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/34', 'labels_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/30/labels{/name}', 'comments_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/30/comments', 'events_url': 'https://api.github.com/repos/18F/jekyll_pages_api_search/issues/30/events', 'html_url': 'https://github.com/18F/jekyll_pages_api_search/issues/30', 'issue_state': 'open', 'issue_node_id': 'MDU6SXNzdWUxNDYyMjcwNTU=', 'gh_issue_id': 146227056, 'gh_issue_number': 30, 'gh_user_id': 196690, 'tool_source': 'Issue Task', 'tool_version': '2.0', 'data_source': 'Github API'})

def test_insert_issue_data_with_invalid_strings(test_db_engine):

    with test_db_engine.connect() as connection:

        # insert the cntrb_id and cntrb_login into the contributors table so the contributor is present. 
        # This is so we don't get a foreign key error on the cntrb_id when we insert the prs
        query = s.sql.text("""
        DELETE FROM "augur_data"."repo";
        DELETE FROM "augur_data"."repo_groups";
        INSERT INTO "augur_data"."repo_groups" ("repo_group_id", "rg_name", "rg_description", "rg_website", "rg_recache", "rg_last_modified", "rg_type", "tool_source", "tool_version", "data_source", "data_collection_date") VALUES (1, 'Default Repo Group', 'The default repo group created by the schema generation script', '', 0, '2019-06-03 15:55:20', 'GitHub Organization', 'load', 'one', 'git', '2019-06-05 13:36:25');
        
        INSERT INTO "augur_data"."repo" ("repo_id", "repo_group_id", "repo_git", "repo_path", "repo_name", "repo_added", "repo_type", "url", "owner_id", "description", "primary_language", "created_at", "forked_from", "updated_at", "repo_archived_date_collected", "repo_archived", "tool_source", "tool_version", "data_source", "data_collection_date") VALUES (1, 1, 'https://github.com/chaoss/augur', NULL, NULL, '2022-08-15 21:08:07', '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'CLI', '1.0', 'Git', '2022-08-15 21:08:07');
        """)

        connection.execute(query)

    try:
        issue_natural_keys = ["issue_url"]
        issue_return_columns = ["issue_url", "issue_id"]
        issue_string_columns = ["issue_title", "issue_body"]

        with test_db_engine.connect() as connection:

            with DatabaseSession(logger, engine=test_db_engine) as session:

                issue_return_data = session.insert_data(issue_data_with_null_strings, Issue, issue_natural_keys,
                                                    return_columns=issue_return_columns, string_fields=issue_string_columns)
                
                data_inserted_count = len(issue_data_with_null_strings)
                result = connection.execute(f"Select * FROM augur_data.issues;").fetchall()

                assert issue_return_data is not None
                assert len(issue_return_data) == data_inserted_count
                assert len(result) == data_inserted_count

    finally:
        with test_db_engine.connect() as connection:

            connection.execute("""
                                DELETE FROM augur_data.issues;
                                DELETE FROM "augur_data"."repo";
                                DELETE FROM "augur_data"."repo_groups";
                                """)


def test_session_without_passing_engine():

    # with DatabaseSession(logger) as session:

    session = DatabaseSession(logger)

    assert session is not None
    assert session.engine is not None

    with session.engine.connect() as connection:

        # insert the cntrb_id and cntrb_login into the contributors table so the contributor is present. 
        # This is so we don't get a foreign key error on the cntrb_id when we insert the prs
        query = s.sql.text("""SELECT * FROM repo""")

        result = connection.execute(query)
        data = result.fetchall()

        assert result is not None
        assert data is not None
        assert isinstance(data, list)


