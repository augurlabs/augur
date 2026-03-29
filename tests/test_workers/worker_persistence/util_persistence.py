#SPDX-License-Identifier: MIT
#import pytest

#from tests.test_workers.test_data import *
from tests.test_workers.test_set_up_fixtures import *


#Sample source data generation that pulls json data that has contributions listed
@pytest.fixture
def sample_source_data_enriched():
    jsonFile = open("tests/test_workers/worker_persistence/contributors.json")

    source_data = json.load(jsonFile)

    jsonFile.close()
    return source_data

#Sample source data generation that opens json data that doesn't have contributions listed
@pytest.fixture
def sample_source_data_unenriched():
    jsonFile = open("tests/test_workers/worker_persistence/contributors_un_enriched.json")

    source_data = json.load(jsonFile)

    jsonFile.close()
    return source_data

#Bad data that an api might return
@pytest.fixture
def sample_source_data_bad_api_return():
    jsonFile = open("tests/test_workers/worker_persistence/bad_Data.json")

    source_data = json.load(jsonFile)

    jsonFile.close()
    return source_data


#Sample data for comments api return
@pytest.fixture
def sample_source_data_standard_github_comments():
    jsonFile = open("tests/test_workers/worker_persistence/standard_enrich_cntrb_id_data.json")
    
    source_data = json.load(jsonFile)
    
    jsonFile.close()
    
    return source_data