Collecting Data
===============

Now that you’ve installed Augur’s application server, it’s time to configure data collection if needed. If you just want to run Augur using the default repositories in the default database, and default celery collection settings, all you need to do is start the redis server in one terminal, make sure rabbitmq is running, and the augur application in the other terminal. (Don't forget that the AUGUR_DB environment variable needs to be set in the terminal, or set permanently)

.. code-block:: bash

    # Terminal Window 1

    # Starts the redis server
    redis-server


.. code-block:: bash

    # Terminal Window 3

    # To Start Augur:
    (uv run nohup augur backend start)

    # To Stop Augur:
    uv run augur backend stop
    uv run augur backend kill

Now, here's a ton of brain-splitting detail about celery collection. There are 2 pieces to data collection with Augur: the celery worker processes, and the job messages passed through rabbitmq. The jobs to collect are determined by a monitor process started through the cli that starts the rest of augur. The monitor process generates the jobs messages to send to rabbitmq through the collection_status table that informs the status of jobs that have yet to be run. The celery collection workers can then accept these jobs, after which they will use the information provided in the job to find the repositories in question and collect the requested data.

Since the default setup will work for most use cases, we'll first cover how to configure some specific data collection jobs and then briefly touch on the celery configuration options, after which we'll cover how to add repos and repo groups to the database.

Authentication and API Tokens
------------------------------

Augur collects data from hosted source control platforms such as GitHub and GitLab using their respective APIs. To avoid strict API rate limits and to enable access to private repositories, Augur requires Personal Access Tokens (PATs) with appropriate read-only permissions.

GitHub Authentication
~~~~~~~~~~~~~~~~~~~~~

Augur uses GitHub APIs to collect repository metadata, issues, pull requests, releases, and contributor information.

Augur requires a GitHub Personal Access Token (PAT). Two token types are supported:

- **Classic Personal Access Token (recommended)**

  A PAT with minimal permissions is sufficient for most public repository data collection.

  The following permissions are optional and only required for specific use cases:

  - ``repo`` — required only when collecting data from private repositories
  - ``read:org`` — required only when collecting organization-related metadata (e.g., organization members or org-owned repository data)
  - ``read:user`` — required only when collecting detailed user profile information (e.g., email, bio) beyond what is available in public API responses

- **Fine-grained Personal Access Token**

  Fine-grained tokens provide repository-specific access with more precise permission controls.

  For public repository data collection, fine-grained tokens include read-only public repository access by default and typically require no additional permission changes.

GitHub tokens should be treated as secrets and supplied to Augur using environment variables or the `installation process <../getting-started/installation.html>`_.

GitLab Authentication
~~~~~~~~~~~~~~~~~~~~~

Augur collects data from the GitLab API using a GitLab Personal Access Token.

The token must include the following scopes:

- ``read_api`` — required for accessing repository metadata, issues, and merge requests
- ``read_repository`` — required only for private repositories when running git-level analysis tasks (facade) that clone via Git over HTTP

These scopes apply to GitLab.com and most standard GitLab deployments.

As with GitHub tokens, GitLab tokens should be stored securely and provided to Augur through environment variables or the `installation process <../getting-started/installation.html>`_.

Configuring Collection
----------------------

There are many collection jobs that ship ready to collect out of the box:

- ``augur.tasks.git.facade_taks`` (collects raw commit and contributor data by parsing Git logs)
- ``augur.tasks.github`` (parent module of all github specific collection jobs)
- ``augur.tasks.github.contributors.tasks`` (collects contributor data from the GitHub API)
- ``augur.tasks.github.pull_requests.tasks`` (collects pull request data from the GitHub API)
- ``augur.tasks.github.repo_info.tasks`` (collects repository statistics from the GitHub API)
- ``augur.tasks.github.releases.tasks`` (collects release data from the GitHub API)
- ``augur.tasks.data_analysis.insight_worker.tasks`` (queries Augur's metrics API to find interesting anomalies in the collected data)

All worker configuration options are found in the config table generated when augur was installed. The config table is located in the augur_operations schema of your postgresql database. Each configurable data collection job set has its subsection with the same or similar title as the task's name. We recommend leaving the defaults and only changing them when explicitly necessary, as the default parameters will work for most use cases. Read on for more on how to make sure your workers are properly configured.

Worker-specific configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next up are the configuration options specific to some collection tasks (but some tasks require no additional configuration beyond the defaults). The most pertinent of these options is the ``Facade`` section ``repo_directory``, so make sure to pay attention to that one.

``Facade``
::::::::::::::::::

- ``repo_directory``, which is the local directory where the facade tasks will clone the repositories it needs to analyze. You should have been prompted for this during installation, but if you need to change it, make sure that it's an absolute path (environment variables like ``$HOME`` are not supported) and that the directory already exists. Defaults to ``repos/``, but it's highly recommended you change this.
- ``limited_run``, toggle between 0 and 1 to determine whether to run all facade tasks or not. Runs all tasks if set to 0
- ``pull_repos``, toggle whether to pull updates from repos after cloning them. If turned off updates to repos will not be collected.
- ``run_analysis``, toggle whether to process commit data at all. If turned off will only clone repos and run tertiary tasks such as resolving contributors from any existing commits or collecting dependency relationships. Mainly used for testing.
- ``run_facade_contributors``, toggle whether to run contributor resolution tasks. This will process and parse through commit data to link emails to contributors as well as aliases, etc.
- ``force_invalidate_caches``, set every repo to reset the status of commit email affillation, which is the organization that an email is associated with.
- ``rebuild_caches``, toggle whether to enable parsing through commit data to determine affillation and web cache

``Insight_Task``
::::::::::::::::::

We recommend leaving the defaults in place for the insight worker unless you are interested in other metrics, or anomalies for a different time period.

- ``training_days``, which specifies the date range that the ``insight_worker`` should use as its baseline for the statistical comparison. Defaults to ``365``, meaning that the worker will identify metrics that have had anomalies compared to their values over the course of the past year, starting at the current date.

- ``anomaly_days``, which specifies the date range in which the ``insight_worker`` should look for anomalies. Defaults to ``2``, meaning that the worker will detect anomalies that have only occured within the past two days, starting at the current date.

- ``contamination``, which is the "sensitivity" parameter for detecting anomalies. Acts as an estimated percentage of the training_days that are expected to be anomalous. The default is ``0.041`` for the default training days of 365: 4.1% of 365 days means that about 15 data points of the 365 days are expected to be anomalous.

- ``switch``, toggles whether to run insight tasks at all.

- ``workers``, number of worker processes to use for insight tasks.

``Task_Routine``
::::::::::::::::::

This section is for toggling sets of jobs on or off.

- ``prelim_phase``, toggles whether to run preliminary tasks that check to see whether repos are valid or not.
- ``primary_repo_collect_phase``, toggle the standard collection jobs, mainly pull requests and issues
- ``secondary_repo_collect_phase``, toggle the secondary collection jobs, mainly jobs that take a while
- ``facade_phase``, toggle all facade jobs
- ``machine_learning_phase``, toggle all ml related jobs

Celery Configuration
--------------------

**We strongly recommend leaving the default celery blocks generated by the installation process, but if you would like to know more, or fine-tune them to your needs, read on.**

The celery monitor is responsible for generating the tasks that will tell the other worker processes what data to collect, and how. The ``Celery`` block has several keys:

- ``core_worker_count``, the number of workers to spawn to run the core tasks.
- ``secondary_worker_count``, the number of workers to spawn to run the secondary tasks.
- ``facade_worker_count``, the number of workers to spawn to run the facade tasks.

- ``refresh_materialized_views_interval_in_days``, number of days to wait between refreshes of materialized views.

If you choose, you can also adjust the values in the ``Tasks`` block if you would like to control when tasks should be re-run on a given repository. 

- ``collection_interval``, the interval (in seconds) at which the collection monitor task runs to schedule new collection jobs. This is different from the other interval values which use days.

- ``core_collection_interval_days``, ``secondary_collection_interval_days``, ``facade_collection_interval_days``, and ``ml_collection_interval_days``, which specify the number of days since the last successful run before a task should be re-run on a given repository.

Adding repos for collection
-----------------------------

If you're using the Docker container, you can use the `provided UI <../docker/usage.html>`_ to load your repositories. Otherwise, you'll need to use the `Augur CLI <command-line-interface/db.html>`_  or the augur frontend to load your repositories. Please reference the respective sections of the documentation for detailed instructions on how to accomplish both of these steps.

Running collections
--------------------

Congratulations! At this point you (hopefully) have a fully functioning and configured Augur instance.

After you've loaded your repos, you're ready for your first collection run. We recommend running only the default jobs first to gather the initial data.

You can now run Augur and start the data collection by issuing the ``augur backend start`` command in the root ``augur`` directory. All your logs (including worker logs and error files) will be saved to a ``logs/`` subdirectory in that same folder, but this can be customized - more on that and other logging utilities `in the development guide <../development-guide/logging.html>`_.

Once you've finished the initial data collection, we suggest then running the ``value_worker`` (if you have it installed) and the ``insight_worker``. This is because the ``value_worker`` depends on the source files of the repositories cloned by the ``facade_worker``, and the ``insight_worker`` uses the data from all the other workers to identify anomalies in the data by by performing statistical analysis on the data returned from Augur's metrics API.

You're now ready to start exploring the data Augur can gather and metrics we can generate. If you're interested in contributing to Augur's codebase, you can check out the `development guide <../development-guide/toc.html>`_. For information about Augur's frontend, keep reading!

Happy collecting!
