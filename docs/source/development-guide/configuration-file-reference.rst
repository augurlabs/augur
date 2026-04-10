Configuration file reference
===============================

Augur's configuration template file, which generates your locally deployed ``augur.config.json`` file, is found at ``augur/config.py``. You will notice a small collection of workers are turned on to start with, by examining the ``switch`` variable within the ``Workers`` block of the config file. You can also specify the number of processes to spawn for each worker using the ``workers`` command. The default is one, and we recommend you start here. If you are going to spawn multiple workers, be sure you have enough credentials cached in the ``augur_operations.worker_oath`` table for the platforms you use.

Task Scheduling Configuration
-----------------------------

The following keys in the ``[Tasks]`` section control the scheduling of periodic Celery tasks. You can adjust these intervals or disable tasks by setting the value to <= 0 (for interval-based tasks).

- ``collection_interval``: Interval in seconds for the main collection monitor. Default: 30.
- ``core_collection_interval_days``: Interval in days for core collection. Default: 15.
- ``secondary_collection_interval_days``: Interval in days for secondary collection. Default: 10.
- ``facade_collection_interval_days``: Interval in days for facade collection. Default: 10.
- ``ml_collection_interval_days``: Interval in days for ML collection. Default: 40.

**New Periodic Task Intervals:**

- ``non_repo_domain_tasks_interval_in_days``: 
  - Description: Schedule interval for non-repository domain tasks (e.g., data analysis).
  - Default: 30 days.
  - Unit: Days.
  - Disable: Set to <= 0.

- ``retry_errored_repos_cron_hour``: 
  - Description: Hour (0-23) to run the retry errored repos task.
  - Default: 0 (Midnight).
  - Unit: Hour of day.

- ``retry_errored_repos_cron_minute``: 
  - Description: Minute (0-59) to run the retry errored repos task.
  - Default: 0.
  - Unit: Minute of hour.

- ``process_contributors_interval_in_seconds``: 
  - Description: Interval to process contributors.
  - Default: 3600 (1 hour).
  - Unit: Seconds.
  - Disable: Set to <= 0.

- ``create_collection_status_records_interval_in_seconds``: 
  - Description: Interval to create collection status records.
  - Default: 86400 (1 day).
  - Unit: Seconds.
  - Disable: Set to <= 0.

If you have questions or would like to help please open an issue on GitHub_.

.. _GitHub: https://github.com/chaoss/augur/issues
