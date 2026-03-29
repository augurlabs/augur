#SPDX-License-Identifier: MIT
from tests.test_workers.worker_persistence.util_persistence import *
import pandas as pd
#from augur.cli import add_repos
#from augur.cli import add_repo_groups


#Function to add repo_groups without starting an augur app instance
@pytest.fixture
def set_up_repo_groups(database_connection):

    df = pd.read_sql(s.sql.text("SELECT repo_group_id FROM augur_data.repo_groups"), database_connection)
    repo_group_IDs = df['repo_group_id'].values.tolist()

    insert_repo_group_sql = s.sql.text("""
    INSERT INTO "augur_data"."repo_groups"("repo_group_id", "rg_name", "rg_description", "rg_website", "rg_recache", "rg_last_modified", "rg_type", "tool_source", "tool_version", "data_source", "data_collection_date") VALUES (:repo_group_id, :repo_group_name, '', '', 0, CURRENT_TIMESTAMP, 'Unknown', 'Loaded by user', '1.0', 'Git', CURRENT_TIMESTAMP);
    """)

    with open("tests/test_workers/test_facade/test_facade_contributor_interface/test_repo_groups.csv") as create_repo_groups_file:
        data = csv.reader(create_repo_groups_file, delimiter=',')
        for row in data:
            print(f"Inserting repo group with name {row[1]} and ID {row[0]}...")
            if int(row[0]) not in repo_group_IDs:
                repo_group_IDs.append(int(row[0]))
                try:
                    database_connection.execute(insert_repo_group_sql, repo_group_id=int(row[0]), repo_group_name=row[1])
                except:
                    print("failed to execute repo_group")
            else:
                print(f"Repo group with ID {row[1]} for repo group {row[1]} already exists, skipping...")



    df = database_connection.execute(s.sql.text("SELECT repo_group_id FROM augur_data.repo_groups"))

    repo_group_IDs = [group[0] for group in df.fetchall()]

    insertSQL = s.sql.text("""
        INSERT INTO augur_data.repo(repo_group_id, repo_git,
        tool_source, tool_version, data_source, data_collection_date)
        VALUES (:repo_group_id, :repo_git, 'CLI', 1.0, 'Git', CURRENT_TIMESTAMP)
    """)

    with open("tests/test_workers/test_facade/test_facade_contributor_interface/test_repos.csv") as upload_repos_file:
        data = csv.reader(upload_repos_file, delimiter=',')
        for row in data:
            print(f"Inserting repo with Git URL `{row[1]}` into repo group {row[0]}")
            if int(row[0]) in repo_group_IDs:
                try:
                    result = database_connection.execute(insertSQL, repo_group_id=int(row[0]), repo_git=row[1])
                except:
                    print("Failed to execute")
            else:
                logger.warning(f"Invalid repo group id specified for {row[1]}, skipping.")




def test_create_sha_endpoint_default(database_connection, set_up_repo_groups):
    
    test_values_good = ['53b0cc122ac9ecc1588d76759dc2e8e437f45b48']
    
    #set_up_repo_groups(database_connection)

    #Dummy class for testing
    dummy = DummyFullWorker(database_connection)

    #Put a controlled repo path to test.
    debug_repo_values = s.sql.text("""
        UPDATE repo
        SET repo_path = \'github.com/chaoss/\', repo_name = \'augur\'
        WHERE repo_id = 1; 
    """)

    database_connection.execute(debug_repo_values)
    
    for value in test_values_good:
    
        url = dummy.create_endpoint_from_commit_sha(value, 1)

        try:
            response = requests.get(url=url, headers=dummy.headers)
        except:
            print(f"Good value wasn't accepted for value {value}")
            raise AssertionError
        
    test_values_wrong = ['notaHash',
                   ''
                   '\n'
                   '102e1a534c33e8ce1e4d01927d5df667596b3dc7']
    
    for value in test_values_wrong:
        
        try:
            url = dummy.create_endpoint_from_commit_sha(value, 1)
            response = requests.get(url=url, headers=dummy.headers)
        except:
            continue
        
        print(f"Bad value was accepted for value: {value}")
        raise AssertionError


def test_create_email_endpoint_default(database_connection, set_up_repo_groups):
    
    #set_up_repo_groups(database_connection)
    
    test_values_good = ['krabs@tilde.team', 
                   'jberkus@redhat.com',
                   'imilarsky@gmail.com']
    
    dummy = DummyFullWorker(database_connection)
    
    for value in test_values_good:
        url = dummy.create_endpoint_from_email(value)
    
        try:
            response = requests.get(url=url, headers=dummy.headers)
        except:
            print(f"Good value wasn't accepted for value {value}")
            raise AssertionError
    
    test_values_bad = ['fakefakefakefakefakefakefake',
                       ' ',
                       '\n\t\t\t']
    
    for value in test_values_bad:
        url = dummy.create_endpoint_from_email(value)
        
        try:
            response = requests.get(url=url, headers=dummy.headers)
        except:
            continue

        print(f"Bad value was accepted for value: {value}")
        raise AssertionError

def test_create_name_endpoint(database_connection, set_up_repo_groups):
    #set_up_repo_groups(database_connection)
    
    test_values_good = [{'name' : 'Santiago Dueñas'}, 
                   {'name' : 'Isaac Milarsky'},
                   {'name' : 'Sean P. Goggins'},
                   {'name' : 'Isaac William Kenyon Milarsky'},
                   {'name' : 'Isaac William Kenyon Milarsky III'}]
    
    dummy = DummyFullWorker(database_connection)
    
    for value in test_values_good:
        url = dummy.create_endpoint_from_name(value)
    
        try:
            response = requests.get(url=url, headers=dummy.headers)
        except:
            print(f"Good value wasn't accepted for value {value}")
            raise AssertionError
    
    test_values_bad = [{'name' : 'Ghost'},
                       {'name' : 'NULL'},
                       {'name' : None},
                       {'name' : '\n\t\t\t'}
                       ]
    
    for value in test_values_bad:
        try:
            url = dummy.create_endpoint_from_name(value)
            response = requests.get(url=url, headers=dummy.headers)
        except:
            continue
        
        print(f"Bad value was accepted for value: {value}")
        raise AssertionError


