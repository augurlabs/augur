#SPDX-License-Identifier: MIT

from tests.test_workers.worker_persistence.util_persistence import *



def test_enrich_data_primary_keys_standard_input(database_connection, sample_source_data_enriched, sample_source_data_unenriched):
    
    print(sample_source_data_enriched)
    print(sample_source_data_unenriched)
    
    data_tables = ['contributors', 'pull_requests', 'commits',
                            'pull_request_assignees', 'pull_request_events', 'pull_request_labels',
                            'pull_request_message_ref', 'pull_request_meta', 'pull_request_repo',
                            'pull_request_reviewers', 'pull_request_teams', 'message', 'pull_request_commits',
                            'pull_request_files', 'pull_request_reviews', 'pull_request_review_message_ref',
                            'contributors_aliases', 'unresolved_commit_emails']
    operations_tables = ['worker_history', 'worker_job']
    
    metadata = s.MetaData()
    # Reflect only the tables we will use for each schema's metadata object
    metadata.reflect(database_connection,only=data_tables)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    
    tableDict = {}
    
    for table in data_tables:
        print(f"Table: {table}")
        tableDict['{}_table'.format(table)] = Base.classes[table].__table__
        
    print(tableDict['contributors_table'])
    
    cntrb = [
        {
            "cntrb_login": test_data_not_enriched['login'],
            "gh_user_id": test_data_not_enriched['id'],
            "gh_login": test_data_not_enriched['login'],
            "gh_url": test_data_not_enriched['url'],
            "gh_html_url": test_data_not_enriched['html_url'],
            "gh_node_id": test_data_not_enriched['node_id'],
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
            "tool_version": "test_enrich_data_primary_keys",
            "data_source":"test_enrich_data_primary_keys"
    } for test_data_not_enriched in sample_source_data_unenriched
    ]
    
    
    database_connection.execute(tableDict['contributors_table'].insert().values(cntrb))
    
    #create class for enrichment
    dummyPersistent = DummyPersistence(database_connection)
    
    gh_merge_fields = ['avatar_url']
    augur_merge_fields = ['gh_avatar_url']
    
    dummyPersistent.enrich_data_primary_keys(sample_source_data_enriched, tableDict['contributors_table'], gh_merge_fields, augur_merge_fields)
    
    #now test each record to make sure that they have an avatar_url
    avatar_url_sql = s.sql.text("""
        SELECT gh_avatar_url
        FROM contributors
                                """)
    
    avatar_url_list = pd.read_sql(avatar_url_sql, database_connection, params={})
    
    for url in avatar_url_list:
        assert url != None
    return

def test_enrich_data_primary_keys_bad_data(database_connection):
    
    gh_merge_fields = ['avatar_url']
    augur_merge_fields = ['gh_avatar_url']
    
    #create class for enrichment
    dummyPersistent = DummyPersistence(database_connection)
    
    #Make sure that function rejects null data
    assert dummyPersistent.enrich_data_primary_keys({}, "contributors_table", gh_merge_fields, augur_merge_fields) == {}
    assert dummyPersistent.enrich_data_primary_keys(None, "contributors_table", gh_merge_fields, augur_merge_fields) == None


def test_enrich_data_primary_keys_redundant_enrich(database_connection,sample_source_data_enriched, sample_source_data_unenriched):
    print(sample_source_data_enriched)
    print(sample_source_data_unenriched)
    
    data_tables = ['contributors', 'pull_requests', 'commits',
                            'pull_request_assignees', 'pull_request_events', 'pull_request_labels',
                            'pull_request_message_ref', 'pull_request_meta', 'pull_request_repo',
                            'pull_request_reviewers', 'pull_request_teams', 'message', 'pull_request_commits',
                            'pull_request_files', 'pull_request_reviews', 'pull_request_review_message_ref',
                            'contributors_aliases', 'unresolved_commit_emails']
    operations_tables = ['worker_history', 'worker_job']
    
    metadata = s.MetaData()
    # Reflect only the tables we will use for each schema's metadata object
    metadata.reflect(database_connection,only=data_tables)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    
    tableDict = {}
    
    for table in data_tables:
        print(f"Table: {table}")
        tableDict['{}_table'.format(table)] = Base.classes[table].__table__
        
    print(tableDict['contributors_table'])
    
    cntrb = [
        {
            "cntrb_login": test_data_not_enriched['login'],
            "gh_user_id": test_data_not_enriched['id'],
            "gh_login": test_data_not_enriched['login'],
            "gh_url": test_data_not_enriched['url'],
            "gh_html_url": test_data_not_enriched['html_url'],
            "gh_node_id": test_data_not_enriched['node_id'],
            "gh_avatar_url": test_data_not_enriched['avatar_url'],
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
            "tool_version": "test_enrich_data_primary_keys",
            "data_source":"test_enrich_data_primary_keys"
    } for test_data_not_enriched in sample_source_data_unenriched
    ]
    
    
    database_connection.execute(tableDict['contributors_table'].insert().values(cntrb))
    
    #create class for enrichment
    dummyPersistent = DummyPersistence(database_connection)
    
    gh_merge_fields = ['avatar_url']
    augur_merge_fields = ['gh_avatar_url']
    
    dummyPersistent.enrich_data_primary_keys(sample_source_data_enriched, tableDict['contributors_table'], gh_merge_fields, augur_merge_fields)
    
    #now test each record to make sure that they have an avatar_url
    avatar_url_sql = s.sql.text("""
        SELECT gh_avatar_url
        FROM contributors
                                """)
    
    avatar_url_list = pd.read_sql(avatar_url_sql, database_connection, params={})
    
    for url in avatar_url_list:
        assert url != None
    return


def test_enrich_data_primary_keys_standard_input(database_connection, sample_source_data_bad_api_return, sample_source_data_unenriched):
    
    print(sample_source_data_enriched)
    print(sample_source_data_unenriched)
    
    data_tables = ['contributors', 'pull_requests', 'commits',
                            'pull_request_assignees', 'pull_request_events', 'pull_request_labels',
                            'pull_request_message_ref', 'pull_request_meta', 'pull_request_repo',
                            'pull_request_reviewers', 'pull_request_teams', 'message', 'pull_request_commits',
                            'pull_request_files', 'pull_request_reviews', 'pull_request_review_message_ref',
                            'contributors_aliases', 'unresolved_commit_emails']
    operations_tables = ['worker_history', 'worker_job']
    
    metadata = s.MetaData()
    # Reflect only the tables we will use for each schema's metadata object
    metadata.reflect(database_connection,only=data_tables)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    
    tableDict = {}
    
    for table in data_tables:
        print(f"Table: {table}")
        tableDict['{}_table'.format(table)] = Base.classes[table].__table__
        
    print(tableDict['contributors_table'])
    
    cntrb = [
        {
            "cntrb_login": test_data_not_enriched['login'],
            "gh_user_id": test_data_not_enriched['id'],
            "gh_login": test_data_not_enriched['login'],
            "gh_url": test_data_not_enriched['url'],
            "gh_html_url": test_data_not_enriched['html_url'],
            "gh_node_id": test_data_not_enriched['node_id'],
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
            "tool_version": "test_enrich_data_primary_keys",
            "data_source":"test_enrich_data_primary_keys"
    } for test_data_not_enriched in sample_source_data_unenriched
    ]
    
    
    database_connection.execute(tableDict['contributors_table'].insert().values(cntrb))
    
    #create class for enrichment
    dummyPersistent = DummyPersistence(database_connection)
    
    gh_merge_fields = ['avatar_url']
    augur_merge_fields = ['gh_avatar_url']
    
    dummyPersistent.enrich_data_primary_keys(sample_source_data_bad_api_return, tableDict['contributors_table'], gh_merge_fields, augur_merge_fields)
    
    return