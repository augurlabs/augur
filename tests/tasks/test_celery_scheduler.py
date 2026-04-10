
import pytest
from unittest.mock import MagicMock, patch, ANY
import datetime
import sys

# Mock modules that might cause side effects on import or are hard to set up
sys.modules['augur.tasks.init'] = MagicMock()
sys.modules['augur.tasks.init'].get_redis_conn_values = MagicMock(return_value=(0, 'redis://localhost:6379/'))
sys.modules['augur.tasks.init'].get_rabbitmq_conn_string = MagicMock(return_value='amqp://guest:guest@localhost:5672//')

# We need to ensure we can import the module now
# The module augur.tasks.init.celery_app imports get_redis_conn_values etc from augur.tasks.init
# which we just mocked.

from augur.tasks.init.celery_app import setup_periodic_tasks, split_tasks_into_groups

@pytest.fixture
def mock_sender():
    sender = MagicMock()
    return sender

@pytest.fixture
def mock_config_factory():
    def _create_config(settings):
        config_mock = MagicMock()
        
        def get_value(section, key):
            val = settings.get(section, {}).get(key)
            return val
            
        config_mock.get_value.side_effect = get_value
        return config_mock
    return _create_config

class TestCeleryScheduler:

    @patch('augur.tasks.init.celery_app.AugurConfig')
    @patch('augur.tasks.init.celery_app.DatabaseSession')
    @patch('augur.tasks.init.celery_app.temporary_database_engine')
    @patch('augur.tasks.init.celery_app.non_repo_domain_tasks')
    @patch('augur.tasks.init.celery_app.retry_errored_repos')
    @patch('augur.tasks.init.celery_app.process_contributors')
    @patch('augur.tasks.init.celery_app.create_collection_status_records')
    @patch('augur.tasks.init.celery_app.refresh_materialized_views')
    @patch('augur.tasks.init.celery_app.augur_collection_monitor')
    def test_setup_periodic_tasks_scheduling(
        self,
        mock_monitor,
        mock_refresh_views,
        mock_create_status,
        mock_process_contributors,
        mock_retry_repos,
        mock_non_repo_tasks,
        mock_temp_engine,
        mock_db_session,
        mock_AugurConfig,
        mock_sender,
        mock_config_factory
    ):
        # Setup config
        settings = {
            'Tasks': {
                'collection_interval': 30,
                'non_repo_domain_tasks_interval_in_days': 15,
                'retry_errored_repos_cron_hour': 2,
                'retry_errored_repos_cron_minute': 30,
                'process_contributors_interval_in_seconds': 1200,
                'create_collection_status_records_interval_in_seconds': 4000
            },
            'Celery': {
                'refresh_materialized_views_interval_in_days': 1
            }
        }
        mock_AugurConfig.return_value = mock_config_factory(settings)
        
        # Run setup
        setup_periodic_tasks(mock_sender)
        
        # Verify calls
        
        # 1. non_repo_domain_tasks: 15 days
        # The code usually converts days to seconds or timedelta
        # 15 days = 15 * 24 * 60 * 60 = 1296000 seconds
        
        # We need to inspect what arguments add_periodic_task was called with.
        # It's called multiple times.
        
        # Look for non_repo_domain_tasks
        # We can check if it was called with approximately the right value or check if the task signature was passed
        
        # Let's verify that the task was scheduled with the correct interval
        # Since we haven't implemented the change yet, we expect this to fail if we ran it, or pass if we check for the NEW behavior we want.
        # This test defines the expected behavior.
        
        # Expected:
        # non_repo_domain_tasks.s() passed as second arg
        # 15 * 86400 or timedelta(days=15) passed as first arg
        
        # Find call for non_repo_domain_tasks
        found_non_repo = False
        for call in mock_sender.add_periodic_task.call_args_list:
            args, _ = call
            interval = args[0]
            task_sig = args[1]
            
            if task_sig == mock_non_repo_tasks.s():
                found_non_repo = True
                # Check interval. 
                # Our implementation will likely use timedelta or seconds.
                # 15 days in seconds is 1296000
                if isinstance(interval, (int, float)):
                    assert interval == 1296000
                elif isinstance(interval, datetime.timedelta):
                    assert interval.days == 15
        
        assert found_non_repo, "non_repo_domain_tasks was not scheduled"

    @patch('augur.tasks.init.celery_app.AugurConfig')
    @patch('augur.tasks.init.celery_app.DatabaseSession')
    @patch('augur.tasks.init.celery_app.temporary_database_engine')
    @patch('augur.tasks.init.celery_app.process_contributors')
    def test_disabled_tasks(
        self,
        mock_process_contributors,
        mock_temp_engine,
        mock_db_session,
        mock_AugurConfig,
        mock_sender,
        mock_config_factory
    ):
        settings = {
            'Tasks': {
                'collection_interval': 30,
                'process_contributors_interval_in_seconds': 0, # Disabled
            },
            'Celery': {
                 'refresh_materialized_views_interval_in_days': 1
            }
        }
        mock_AugurConfig.return_value = mock_config_factory(settings)
        
        setup_periodic_tasks(mock_sender)
        
        # Verify process_contributors was NOT scheduled
        found_process = False
        for call in mock_sender.add_periodic_task.call_args_list:
            args, _ = call
            task_sig = args[1]
            if task_sig == mock_process_contributors.s():
                found_process = True
        
        assert not found_process, "process_contributors should be disabled"
