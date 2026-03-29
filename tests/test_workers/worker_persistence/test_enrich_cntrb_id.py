#SPDX-License-Identifier: MIT
from tests.test_workers.worker_persistence.util_persistence import *


#WIP
def test_enrich_cntrb_id_standard_input(database_connection, sample_source_data_standard_github_comments, sample_source_data_enriched, sample_source_data_unenriched):
    
    #create class for testing
    dummy = DummyFullWorker(database_connection)
    
    
    cntrb = [
        {
            "cntrb_login": test_data_not_enriched['login'],
            "gh_user_id": test_data_not_enriched['id'],
            "gh_login": test_data_not_enriched['login'],
            "gh_url": test_data_not_enriched['url'],
            "gh_html_url": test_data_not_enriched['html_url'],
            #"gh_node_id": test_data_not_enriched['node_id'],
            #"gh_avatar_url": test_data_not_enriched['avatar_url'],
            "gh_gravatar_id": test_data_not_enriched['gravatar_id'],
            "gh_followers_url": test_data_not_enriched['followers_url'],
            "gh_following_url": test_data_not_enriched['following_url'],
            "gh_gists_url": test_data_not_enriched['gists_url'],
            "gh_starred_url": test_data_not_enriched['starred_url'],
            "gh_subscriptions_url": test_data_not_enriched['subscriptions_url'],
            "gh_organizations_url": test_data_not_enriched['organizations_url'],
            "gh_repos_url": test_data_not_enriched['repos_url'],
            "gh_events_url": test_data_not_enriched['events_url'],
            "gh_received_events_url": test_data_not_enriched['received_events_url'],
            "gh_type": test_data_not_enriched['type'],
            "gh_site_admin": test_data_not_enriched['site_admin'],
            "tool_source": "Test",
            "tool_version": "test_enrich_cntrb_id",
            "data_source":"test_enrich_cntrb_id"
    } for test_data_not_enriched in sample_source_data_unenriched
    ]
    
    
    database_connection.execute(dummy.contributors_table.values(cntrb))
    
    
    gh_merge_fields = ['avatar_url']
    augur_merge_fields = ['gh_avatar_url']
    
    dummy.enrich_cntrb_id(
                    sample_source_data_standard_github_comments, 'user.login', action_map_additions={
                        'insert': {
                            'source': ['user.node_id'],
                            'augur': ['gh_node_id']
                        }
                    }, prefix='user.'
    )
    
    #now test each record to make sure that they have an avatar_url and node id.
    avatar_url_sql = s.sql.text("""
        SELECT gh_avatar_url, gh_node_id
        FROM contributors
                                """)
    
    avatar_url_list = pd.read_sql(avatar_url_sql, database_connection, params={})
    
    for url in avatar_url_list:
        assert url != None
    return

