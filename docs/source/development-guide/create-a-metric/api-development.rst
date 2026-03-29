Parts of an Augur API Endpoint
=====================================

1. Develop the query that will produce data needed to deliver the endpoint, usually parameterized by a `repo_id`.
2. Determine if the endpoint will be a "standard endpoint", or a custom endpoint.

Where Are the Endpoints?
---------------------------

JSON Metrics are here:

.. code-block:: bash

   $ AUGUR_HOME/augur/metrics

Visualization Metrics are here:

.. code-block:: bash

   $ AUGUR_HOME/augur/routes


Existing metrics files (JSON Metric) "Standard Metrics":
---------------------------------------------------------

1. commit.py
2. contributor.py
3. experimental.py
4. insight.py
5. issue.py
6. message.py
7. platform.py
8. release.py
9. repo_meta.py

All "Standard Metrics" files generally share a set of imports

.. code-block:: python

   import datetime
   import sqlalchemy as s
   import pandas as pd
   from augur.util import register_metric

You can see that one of the imports is our standard metric import from the util file, which is located in:

.. code-block:: python

   AUGUR_HOME/augur/routes/util.py


All "Standard Metrics" share declaration and a method signature

Declaration:

.. code-block:: python

   @register_metric()

Method Signature:

.. code-block:: python

   def contributors(self, repo_group_id, repo_id=None, period='day', begin_date=None, end_date=None):

Standard metrics also, generally, include default setting blocks for date range, in the event parameters are not passed.

.. code-block:: python

    if not begin_date:
        begin_date = '1970-1-1 00:00:01'
    if not end_date:
        end_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

There is also, generally, a block in a standard metric for pulling data by a repo_id or a repo_group_id. The default is a repo_group_id. Here is an abrdiged example from the contributors endpoint in `contributor.py`

.. code-block:: python

    if repo_id:
        contributorsSQL = s.sql.text("""
           SELECT id                           AS user_id,
                SUM(commits)                 AS commits,
                SUM(issues)                  AS issues,
                SUM(commit_comments)         AS commit_comments,
                SUM(issue_comments)          AS issue_comments,
                SUM(pull_requests)           AS pull_requests,
                SUM(pull_request_comments)   AS pull_request_comments,
                SUM(a.commits + a.issues + a.commit_comments + a.issue_comments + a.pull_requests +
                    a.pull_request_comments) AS total,
                a.repo_id, repo.repo_name
            FROM (
                    (SELECT gh_user_id AS id,
                        ommitted_lines as ommitted_from_example
                        AND created_at BETWEEN :begin_date AND :end_date
                        GROUP BY id, repo_id
                    )
                ) a, repo
            WHERE a.repo_id = repo.repo_id
            GROUP BY a.id, a.repo_id, repo_name
            ORDER BY total DESC
        """)

        results = pd.read_sql(contributorsSQL, self.database, params={'repo_id': repo_id, 'period': period,
                                                                'begin_date': begin_date, 'end_date': end_date})
    else: ## This is if the repo_id is not specified
        contributorsSQL = s.sql.text("""
           SELECT id                           AS user_id,
                SUM(commits)                 AS commits,
                SUM(issues)                  AS issues,
                SUM(commit_comments)         AS commit_comments,
                SUM(issue_comments)          AS issue_comments,
                SUM(pull_requests)           AS pull_requests,
                SUM(pull_request_comments)   AS pull_request_comments,
                SUM(a.commits + a.issues + a.commit_comments + a.issue_comments + a.pull_requests +
                    a.pull_request_comments) AS total, a.repo_id, repo_name
            FROM (
                    (SELECT gh_user_id AS id,
                            repo_id,
                            0          AS commits,
                            COUNT(*)   AS issues,
                            0          AS commit_comments,
                        AND created_at BETWEEN :begin_date AND :end_date
                        GROUP BY id, repo_id
                        ommitted_lines as ommitted_from_example
                    )
                ) a, repo
            WHERE a.repo_id = repo.repo_id
            GROUP BY a.id, a.repo_id, repo_name
            ORDER BY total DESC
        """)

        results = pd.read_sql(contributorsSQL, self.database, params={'repo_group_id': repo_group_id, 'period': period,
                                                                'begin_date': begin_date, 'end_date': end_date})
    return results


Existing Metrics Files:
--------------------------------------------

1. augur/metrics/commit.py
2. augur/metrics/contributor.py
3. augur/metrics/deps.py
4. augur/metrics/experimental.py
5. augur/metrics/insight.py
6. augur/metrics/issue.py
7. augur/metrics/message.py
8. augur/metrics/platform.py
9. augur/metrics/pull_request.py
10. augur/metrics/release.py
11. augur/metrics/repo_meta.py


These files are not intended to be all inclusive. Rather, they are what we have developed, or imagined, based on existing CHAOSS metrics to date. New CHAOSS metrics are likely to result in the inclusion of new files under metrics, or routes, depending if they are standard metrics or not.
