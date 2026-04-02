# SPDX-License-Identifier: MIT

import sqlalchemy as s
import pandas as pd
from flask import current_app

from augur.api.util import register_metric


@register_metric()
def bot_activity(repo_group_id, repo_id=None):
    """
    CHAOSS Bot Activity Metric (Initial Implementation)

    Measures the volume of automated bot activity by identifying
    bot-authored commits and comparing them with human commits.
    """

    if repo_id:
        bot_activity_sql = s.sql.text("""
            SELECT
                SUM(
                    CASE
                        WHEN LOWER(cn.cntrb_login) LIKE '%bot%' THEN 1
                        ELSE 0
                    END
                ) AS bot_commits,
                SUM(
                    CASE
                        WHEN LOWER(cn.cntrb_login) NOT LIKE '%bot%' THEN 1
                        ELSE 0
                    END
                ) AS human_commits
            FROM commits c
            JOIN contributors cn
                ON c.cmt_author_id = cn.cntrb_id
            WHERE c.repo_id = :repo_id
        """)
        params = {"repo_id": repo_id}

    else:
        bot_activity_sql = s.sql.text("""
            SELECT
                SUM(
                    CASE
                        WHEN LOWER(cn.cntrb_login) LIKE '%bot%' THEN 1
                        ELSE 0
                    END
                ) AS bot_commits,
                SUM(
                    CASE
                        WHEN LOWER(cn.cntrb_login) NOT LIKE '%bot%' THEN 1
                        ELSE 0
                    END
                ) AS human_commits
            FROM commits c
            JOIN contributors cn
                ON c.cmt_author_id = cn.cntrb_id
            JOIN repo r
                ON c.repo_id = r.repo_id
            WHERE r.repo_group_id = :repo_group_id
        """)
        params = {"repo_group_id": repo_group_id}

    with current_app.engine.connect() as conn:
        results = pd.read_sql(bot_activity_sql, conn, params=params)

    bot_commits = int(results.at[0, "bot_commits"] or 0)
    human_commits = int(results.at[0, "human_commits"] or 0)
    total_commits = bot_commits + human_commits

    bot_percentage = (
        round((bot_commits / total_commits) * 100, 2)
        if total_commits > 0 else 0
    )

    return pd.DataFrame([{
        "bot_commits": bot_commits,
        "human_commits": human_commits,
        "bot_commit_percentage": bot_percentage
    }])
