#SPDX-License-Identifier: MIT
"""
Metrics that provide data about pull requests & their associated activity
"""

from datetime import datetime
import sqlalchemy as s
import pandas as pd
from flask import current_app

from augur.api.util import register_metric

@register_metric()
def pull_requests_new(repo_group_id, repo_id=None, period='day', begin_date=None, end_date=None):
    """
    Returns a time series of the number of new Pull Requests opened during a certain period.

    :param repo_id: The repository's id
    :param repo_group_id: The repository's group id
    :param period: To set the periodicity to 'day', 'week', 'month' or 'year', defaults to 'day'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:01'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of new Pull Requests/period
    """
    if not begin_date:
        begin_date = '1970-1-1 00:00:01'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if repo_id:
        new_pull_requests_query = s.sql.text("""
            SELECT DATE_TRUNC(:period, pr_created_at) AS created_date,
                   COUNT(*) AS new_pull_requests
            FROM pull_requests
            WHERE repo_id = :repo_id
            AND pr_created_at BETWEEN :begin_date AND :end_date
            GROUP BY created_date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(new_pull_requests_query, conn, params={'repo_id': repo_id, 'period': period,
                                                                       'begin_date': begin_date,
                                                                       'end_date': end_date})
    else:
        new_pull_requests_query = s.sql.text("""
            SELECT DATE_TRUNC(:period, pr_created_at) AS created_date,
                   COUNT(pr_id) AS new_pull_requests
            FROM pull_requests
            WHERE repo_id IN (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND pr_created_at BETWEEN :begin_date AND :end_date
            GROUP BY created_date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(new_pull_requests_query, conn,
                                params={'repo_group_id': repo_group_id, 'period': period,
                                      'begin_date': begin_date,
                                      'end_date': end_date})

    return results

@register_metric()
def pull_requests_merge_contributor_new(repo_group_id, repo_id=None, period='day', begin_date=None, end_date=None):
    """
    Returns a timeseries of the count of persons contributing with an accepted commit for the first time.

    :param repo_id: The repository's id
    :param repo_group_id: The repository's group id
    :param period: To set the periodicity to 'day', 'week', 'month' or 'year', defaults to 'day'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of persons/period
    """
    if not begin_date:
        begin_date = '1970-1-1 00:00:01'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if repo_id:
        commitNewContributor = s.sql.text("""
            SELECT date_trunc(:period, new_date::DATE) as commit_date,
            COUNT(cmt_author_email), repo_name
            FROM ( SELECT repo_name, cmt_author_email, MIN(TO_TIMESTAMP(cmt_author_date,'YYYY-MM-DD')) AS new_date
            FROM commits JOIN repo ON commits.repo_id = repo.repo_id
            WHERE commits.repo_id = :repo_id
            AND TO_TIMESTAMP(cmt_author_date,'YYYY-MM-DD') BETWEEN :begin_date AND :end_date AND cmt_author_email IS NOT NULL
            GROUP BY cmt_author_email, repo_name
            ) as abc GROUP BY commit_date, repo_name
        """)
        

        with current_app.engine.connect() as conn:
            results = pd.read_sql(commitNewContributor, conn, params={'repo_id': repo_id, 'period': period,
                                                                            'begin_date': begin_date,
                                                                            'end_date': end_date})
    else:
        commitNewContributor = s.sql.text("""
            SELECT abc.repo_id, repo_name ,date_trunc(:period, new_date::DATE) as commit_date,
                COUNT(cmt_author_email)
            FROM (SELECT cmt_author_email, MIN(TO_TIMESTAMP(cmt_author_date, 'YYYY-MM-DD')) AS new_date, repo_id
                FROM commits
                WHERE repo_id in (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
                    AND TO_TIMESTAMP(cmt_author_date, 'YYYY-MM-DD') BETWEEN :begin_date AND :end_date
                    AND cmt_author_email IS NOT NULL
                GROUP BY cmt_author_email, repo_id
                ) as abc, repo
            WHERE abc.repo_id = repo.repo_id
            GROUP BY abc.repo_id, repo_name, commit_date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(commitNewContributor, conn,
                                    params={'repo_group_id': repo_group_id, 'period': period,
                                            'begin_date': begin_date,
                                            'end_date': end_date})
    return results

@register_metric()
def pull_requests_closed_no_merge(repo_group_id, repo_id=None, period='day', begin_date=None, end_date=None):
    """
    Returns a timeseries of the which were closed but not merged

    :param repo_id: The repository's id
    :param repo_group_id: The repository's group id
    :param period: To set the periodicity to 'day', 'week', 'month' or 'year', defaults to 'day'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of persons/period
    """
    if not begin_date:
        begin_date = '1970-1-1 00:00:01'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if repo_id:
        closedNoMerge = s.sql.text("""
            SELECT DATE_TRUNC(:period, pull_requests.pr_closed_at) AS closed_date,
            COUNT(pull_request_id) as pr_count
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id = :repo_id
            AND pull_requests.pr_closed_at is NOT NULL AND
            pull_requests.pr_merged_at is NULL
            GROUP BY closed_date, pull_request_id
            ORDER BY closed_date
        """)

        

        with current_app.engine.connect() as conn:
            results = pd.read_sql(closedNoMerge, conn, params={'repo_id': repo_id, 'period': period,
                                                                            'begin_date': begin_date,
                                                                            'end_date': end_date})

    else:
        closedNoMerge = s.sql.text("""
            SELECT DATE_TRUNC(:period, pull_requests.pr_closed_at) AS closed_date,
            COUNT(pull_request_id) as pr_count
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id WHERE pull_requests.repo_id in (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            and pull_requests.pr_closed_at is NOT NULL and pull_requests.pr_merged_at is NULL
            GROUP BY closed_date, pull_request_id
            ORDER BY closed_date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(closedNoMerge, conn,
                                    params={'repo_group_id': repo_group_id, 'period': period,
                                            'begin_date': begin_date,
                                            'end_date': end_date})
    return results

@register_metric()
def reviews(repo_group_id, repo_id=None, period='day', begin_date=None, end_date=None):
    """ Returns a timeseris of new reviews or pull requests opened

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param period: To set the periodicity to 'day', 'week', 'month' or 'year', defaults to 'day'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of new reviews/period
    """
    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    if not repo_id:
        reviews_SQL = s.sql.text("""
            SELECT
                pull_requests.repo_id,
                repo_name,
                DATE_TRUNC(:period, pull_requests.pr_created_at) AS date,
                COUNT(pr_src_id) AS pull_requests
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id IN
                (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND pull_requests.pr_created_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD')
                AND to_timestamp(:end_date, 'YYYY-MM-DD')
            GROUP BY pull_requests.repo_id, repo_name, date
            ORDER BY pull_requests.repo_id, date
        """)

        
        with current_app.engine.connect() as conn:
            results = pd.read_sql(reviews_SQL, conn,
                                    params={'period': period, 'repo_group_id': repo_group_id,
                                            'begin_date': begin_date, 'end_date': end_date })
        return results

    else:
        reviews_SQL = s.sql.text("""
            SELECT
                repo_name,
                DATE_TRUNC(:period, pull_requests.pr_created_at) AS date,
                COUNT(pr_src_id) AS pull_requests
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id = :repo_id
            AND pull_requests.pr_created_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD HH24:MI:SS')
                AND to_timestamp(:end_date, 'YYYY-MM-DD HH24:MI:SS')
            GROUP BY date, repo_name
            ORDER BY date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(reviews_SQL, conn,
                                params={'period': period, 'repo_id': repo_id,
                                            'begin_date': begin_date, 'end_date': end_date})
        return results

@register_metric()
def reviews_accepted(repo_group_id, repo_id=None, period='day', begin_date=None, end_date=None):
    """Returns a timeseries of number of reviews or pull requests accepted.

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param period: To set the periodicity to 'day', 'week', 'month' or 'year', defaults to 'day'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of accepted reviews/period
    """
    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    if not repo_id:
        reviews_accepted_SQL = s.sql.text("""
            SELECT
                pull_requests.repo_id,
                repo.repo_name,
                DATE_TRUNC(:period, pull_requests.pr_merged_at) AS date,
                COUNT(pr_src_id) AS pull_requests
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id IN
                (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND pr_merged_at IS NOT NULL
            AND pr_merged_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD')
                AND to_timestamp(:end_date, 'YYYY-MM-DD')
            GROUP BY pull_requests.repo_id, repo_name, date
            ORDER BY pull_requests.repo_id, date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(reviews_accepted_SQL, conn,
                                    params={'period': period, 'repo_group_id': repo_group_id,
                                            'begin_date': begin_date, 'end_date': end_date})
        return results
    else:
        reviews_accepted_SQL = s.sql.text("""
            SELECT
                repo.repo_name,
                DATE_TRUNC(:period, pull_requests.pr_merged_at) AS date,
                COUNT(pr_src_id) AS pull_requests
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id = :repo_id
            AND pr_merged_at IS NOT NULL
            AND pr_merged_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD')
                AND to_timestamp(:end_date, 'YYYY-MM-DD')
            GROUP BY date, repo.repo_name
            ORDER BY date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(reviews_accepted_SQL, conn,
                                params={'period': period, 'repo_id': repo_id,
                                        'begin_date': begin_date, 'end_date': end_date})
        return results

@register_metric()
def reviews_declined(repo_group_id, repo_id=None, period='day', begin_date=None, end_date=None):
    """ Returns a time series of reivews declined

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param period: To set the periodicity to 'day', 'week', 'month' or 'year', defaults to 'day'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of declined reviews/period
    """
    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    if not repo_id:
        reviews_declined_SQL = s.sql.text("""
            SELECT
                pull_requests.repo_id,
                repo.repo_name,
                DATE_TRUNC(:period, pull_requests.pr_closed_at) AS date,
                COUNT(pr_src_id) AS pull_requests
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id IN
                (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND pr_src_state = 'closed' AND pr_merged_at IS NULL
            AND pr_closed_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD')
                AND to_timestamp(:end_date, 'YYYY-MM-DD')
            GROUP BY pull_requests.repo_id, repo_name, date
            ORDER BY pull_requests.repo_id, date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(reviews_declined_SQL, conn,
                                    params={'period': period, 'repo_group_id': repo_group_id,
                                            'begin_date': begin_date, 'end_date': end_date })
        return results
    else:
        reviews_declined_SQL = s.sql.text("""
            SELECT
                repo.repo_name,
                DATE_TRUNC(:period, pull_requests.pr_closed_at) AS date,
                COUNT(pr_src_id) AS pull_requests
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id = :repo_id
            AND pr_src_state = 'closed' AND pr_merged_at IS NULL
            AND pr_closed_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD')
                AND to_timestamp(:end_date, 'YYYY-MM-DD')
            GROUP BY date, repo.repo_name
            ORDER BY date
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(reviews_declined_SQL, conn,
                                params={'period': period, 'repo_id': repo_id,
                                        'begin_date': begin_date, 'end_date': end_date})
        return results

@register_metric()
def review_duration(repo_group_id, repo_id=None, begin_date=None, end_date=None):
    """ Returns the duration of each accepted review.

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of pull request id with the corresponding duration
    """
    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    if not repo_id:
        review_duration_SQL = s.sql.text("""
            SELECT
                pull_requests.repo_id,
                repo.repo_name,
                pull_requests.pull_request_id,
                pull_requests.pr_created_at AS created_at,
                pull_requests.pr_merged_at AS merged_at,
                (pr_merged_at - pr_created_at) AS duration
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id IN
                (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND pr_merged_at IS NOT NULL
            AND pr_created_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD')
                AND to_timestamp(:end_date, 'YYYY-MM-DD')
            ORDER BY pull_requests.repo_id, pull_requests.pull_request_id
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(review_duration_SQL, conn,
                                    params={'repo_group_id': repo_group_id,
                                            'begin_date': begin_date,
                                            'end_date': end_date})
        results['duration'] = results['duration'].astype(str)
        return results
    else:
        review_duration_SQL = s.sql.text("""
            SELECT
                repo_name,
                pull_request_id,
                pr_created_at AS created_at,
                pr_merged_at AS merged_at,
                (pr_merged_at - pr_created_at) AS duration
            FROM pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id = :repo_id
            AND pr_merged_at IS NOT NULL
            AND pr_created_at
                BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD')
                AND to_timestamp(:end_date, 'YYYY-MM-DD')
            ORDER BY pull_requests.repo_id, pull_request_id
        """)

        with current_app.engine.connect() as conn:
            results = pd.read_sql(review_duration_SQL, conn,
                                params={'repo_id': repo_id,
                                        'begin_date': begin_date,
                                        'end_date': end_date})
        results['duration'] = results['duration'].astype(str)
        return results

@register_metric()
def pull_request_acceptance_rate(repo_group_id, repo_id=None, begin_date=None, end_date=None, group_by='week'):
    """
    Timeseries of pull request acceptance rate (expressed as the ratio of pull requests merged on a date to the count of pull requests opened on a date)

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :return: DataFrame with ratio/day
    """
    if not begin_date:
        begin_date = '1970-1-1 00:00:01'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not repo_id:
        prAccRateSQL = s.sql.text("""
            SELECT DATE(date_created) AS "date", CAST(num_approved AS DECIMAL)/CAST(num_open AS DECIMAL) AS "rate"
            FROM
                (
                    SELECT count(issue_events.issue_id) AS num_approved,
                        date_trunc(:group_by,issue_events.created_at) AS accepted_on
                    FROM issue_events JOIN issues ON issues.issue_id = issue_events.issue_id
                        JOIN repo ON issues.repo_id = repo.repo_id
                    WHERE action = 'merged'
                    AND issues.pull_request IS NOT NULL 
                    AND repo_group_id = :repo_group_id
                    AND issue_events.created_at BETWEEN :begin_date AND :end_date
                    GROUP BY accepted_on
                    ORDER BY accepted_on
                ) accepted
            JOIN
                (
                    SELECT count(issue_events.issue_id) AS num_open,
                        date_trunc(:group_by,issue_events.created_at) AS date_created
                    FROM issue_events JOIN issues ON issues.issue_id = issue_events.issue_id
                        JOIN repo ON issues.repo_id = repo.repo_id
                    WHERE action = 'ready_for_review'
                    AND issues.pull_request IS NOT NULL 
                    AND repo_group_id = :repo_group_id
                    AND issue_events.created_at BETWEEN :begin_date AND :end_date
                    GROUP BY date_created
                    ORDER BY date_created
                ) opened
            ON opened.date_created = accepted.accepted_on
        """)
        
        with current_app.engine.connect() as conn:
            results = pd.read_sql(prAccRateSQL, conn, params={'repo_group_id': repo_group_id, 'group_by': group_by,
                                                            'begin_date': begin_date, 'end_date': end_date})
        return results
    else:
        prAccRateSQL = s.sql.text("""
            SELECT DATE(date_created) AS "date", CAST(num_approved AS DECIMAL)/CAST(num_open AS DECIMAL) AS "rate"
            FROM
                (
                    SELECT count(issue_events.issue_id) AS num_approved,
                        date_trunc(:group_by,issue_events.created_at) AS accepted_on
                    FROM issue_events JOIN issues ON issues.issue_id = issue_events.issue_id
                    WHERE action = 'merged'
                    AND issues.pull_request IS NOT NULL
                    AND issue_events.repo_id = :repo_id
                    AND issue_events.created_at BETWEEN :begin_date AND :end_date
                    GROUP BY accepted_on
                    ORDER BY accepted_on
                ) accepted
            JOIN
                (
                    SELECT count(issue_events.issue_id) AS num_open,
                        date_trunc(:group_by,issue_events.created_at) AS date_created
                    FROM issue_events JOIN issues ON issues.issue_id = issue_events.issue_id
                    WHERE action = 'ready_for_review'
                    AND issues.pull_request IS NOT NULL 
                    AND issue_events.repo_id = :repo_id
                    AND issue_events.created_at BETWEEN :begin_date AND :end_date
                    GROUP BY date_created
                    ORDER BY date_created
                ) opened
            ON opened.date_created = accepted.accepted_on
        """)
        
        with current_app.engine.connect() as conn:
            results = pd.read_sql(prAccRateSQL, conn, params={'repo_id': repo_id, 'group_by': group_by,
                                                                'begin_date': begin_date, 'end_date': end_date})
        return results

@register_metric()
def pull_request_average_time_to_close(repo_group_id, repo_id=None, group_by='month', time_unit='hours', begin_date=None, end_date=None):
    """ Avegage time to close pull requests with merged_status and the time frame

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param group_by: The time frame the data is grouped by, options are: 'day', 'week', 'month' or 'year', defaults to 'month'
    :param time_unit: Unit of time for data, options are: 'hours', or 'days', defaults to 'hours'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of average time to close pull request
    """

    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')


    unit_options = ['year', 'month', 'week', 'day']
    time_group_bys = []
    for unit in unit_options.copy():
        if group_by not in unit_options:
            continue
        time_group_bys.append('closed_{}'.format(unit))
        del unit_options[0]

    if not repo_id:
        pr_all_SQL = s.sql.text("""
        SELECT     
            repo_id,
            repo_name,
            repo_group_id,
            rg_name AS repo_group_name,
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part('week', pr_closed_at :: DATE) AS closed_week,
            date_part('day', pr_closed_at :: DATE) AS closed_day,
            EXTRACT (epoch FROM time_to_close)/ 86400 AS average_days_to_close,
            EXTRACT (epoch FROM time_to_close)/ 3600 AS average_hours_to_close,
        CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            count(*) AS num_pull_requests
        FROM (
        SELECT 
            pull_requests.pull_request_id,
            pull_requests.repo_id,
            repo_name,
            repo.repo_group_id,
            rg_name,
            pr_closed_at,
            pr_created_at,
            pr_closed_at - pr_created_at AS time_to_close,
            pr_merged_at
        FROM pull_request_message_ref, message, repo_groups,
        pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
        WHERE pull_requests.repo_id IN 
             (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
        AND repo.repo_id = pull_requests.repo_id
        AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
        AND pull_request_message_ref.msg_id = message.msg_id
        AND repo.repo_group_id = repo_groups.repo_group_id
        AND pr_created_at::DATE >= :begin_date ::DATE
        AND pr_closed_at::DATE <= :end_date ::DATE
        GROUP BY pull_requests.pull_request_id, repo.repo_name, repo.repo_group_id, repo_groups.rg_name
        ) time_between_responses
        GROUP BY merged_status, time_between_responses.pr_closed_at, time_between_responses.time_to_close, time_between_responses.repo_id, time_between_responses.repo_name, time_between_responses.repo_group_id, time_between_responses.rg_name
        ORDER BY merged_status
        """)

    else:
        pr_all_SQL = s.sql.text("""
        SELECT 
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part('week', pr_closed_at :: DATE) AS closed_week,
            date_part('day', pr_closed_at :: DATE) AS closed_day,
            EXTRACT (epoch FROM time_to_close)/ 86400 AS average_days_to_close,
            EXTRACT (epoch FROM time_to_close)/ 3600 AS average_hours_to_close,
        CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            count(*) AS num_pull_requests
        FROM (
        SELECT pull_requests.pull_request_id,
            pr_closed_at,
            pr_created_at,
            pr_closed_at - pr_created_at AS time_to_close,
            pr_merged_at
        FROM pull_requests, repo, pull_request_message_ref, message
        WHERE repo.repo_id = :repo_id
        AND repo.repo_id = pull_requests.repo_id
        AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
        AND pull_request_message_ref.msg_id = message.msg_id
        AND pr_created_at::DATE >= :begin_date ::DATE
        AND pr_closed_at::DATE <= :end_date ::DATE
        GROUP BY pull_requests.pull_request_id
        ) time_between_responses
        GROUP BY merged_status, time_between_responses.pr_closed_at, time_between_responses.time_to_close
        ORDER BY merged_status
        """)

    

        with current_app.engine.connect() as conn:
            pr_all = pd.read_sql(pr_all_SQL, conn,
                params={'repo_id': repo_id, 'repo_group_id':repo_group_id,
                        'begin_date': begin_date, 'end_date': end_date})
    

    if pr_all.empty:
        return []

    if not repo_id:
        pr_avg_time_to_close = pr_all.groupby(['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys).mean().reset_index()[['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys + ['average_{}_to_close'.format(time_unit)]]
    else:
        pr_avg_time_to_close = pr_all.groupby(['merged_status'] + time_group_bys).mean().reset_index()[time_group_bys + ['merged_status', 'average_{}_to_close'.format(time_unit)]]

    return pr_avg_time_to_close

@register_metric()
def pull_request_average_time_between_responses(repo_group_id, repo_id=None, group_by='month', time_unit='hours', begin_date=None, end_date=None):
    """ Avegage time between responeses with merged_status and the time frame

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param group_by: The time frame the data is grouped by, options are: 'day', 'week', 'month' or 'year', defaults to 'month'
    :param time_unit: Unit of time for data, options are: 'minutes', or 'hours', defaults to 'hours'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of average time beteen responses
=======
@register_metric()
def pull_request_merged_status_counts(repo_group_id, repo_id=None, begin_date='1970-1-1 00:00:01', end_date=None, group_by='week'):
>>>>>>> Stashed changes
    """

    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')


    unit_options = ['year', 'month', 'week', 'day']
    time_group_bys = []
    for unit in unit_options.copy():
        if group_by not in unit_options:
            continue
        time_group_bys.append('closed_{}'.format(unit))
        del unit_options[0]

    if not repo_id:
        pr_all_SQL = s.sql.text("""
            SELECT      
                repo_id,
                repo_name,
                repo_group_id,
                rg_name AS repo_group_name,
                date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
                date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
                date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
                date_part( 'day', pr_closed_at :: DATE ) AS closed_day,
                (EXTRACT(epoch FROM average_time_between_responses)/3600) AS average_hours_between_responses,
                (EXTRACT(epoch FROM average_time_between_responses)/60) AS average_minutes_between_responses,
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
                count(*) AS num_pull_requests
            FROM (
            SELECT 
                repo_name,
                repo_groups.repo_group_id,
                rg_name,
                pull_requests.repo_id,
                pull_requests.pull_request_id,
                pr_closed_at,
                pr_created_at,
                pr_merged_at,
                (MAX(message.msg_timestamp) - MIN(message.msg_timestamp)) / COUNT(DISTINCT message.msg_timestamp) AS average_time_between_responses
            FROM pull_request_message_ref, message, repo_groups,
            pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id IN 
                (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND repo.repo_id = pull_requests.repo_id
            AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
            AND pull_request_message_ref.msg_id = message.msg_id
            AND repo_groups.repo_group_id = repo.repo_group_id
            AND pr_created_at::DATE >= :begin_date ::DATE
            AND pr_closed_at::DATE <=  :end_date ::DATE
            GROUP BY pull_requests.pull_request_id, repo.repo_id, repo.repo_name, repo_groups.repo_group_id, repo_groups.rg_name
            ) time_between_responses
            GROUP BY closed_year, closed_month, merged_status, time_between_responses.pr_closed_at, time_between_responses.average_time_between_responses, time_between_responses.repo_id, time_between_responses.repo_name, time_between_responses.repo_group_id, time_between_responses.rg_name
            """)

    else:
        pr_all_SQL = s.sql.text("""
        SELECT 
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day,
            (EXTRACT(epoch FROM average_time_between_responses)/3600) AS average_hours_between_responses,
            (EXTRACT(epoch FROM average_time_between_responses)/60) AS average_minutes_between_responses,
        CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            count(*) AS num_pull_requests
        FROM (
        SELECT pull_requests.pull_request_id,
            pr_closed_at,
            pr_created_at,
            pr_merged_at,
            (MAX(message.msg_timestamp) - MIN(message.msg_timestamp)) / COUNT(DISTINCT message.msg_timestamp) AS average_time_between_responses
        FROM pull_requests, repo, pull_request_message_ref, message
        WHERE repo.repo_id = :repo_id
            AND repo.repo_id = pull_requests.repo_id
            AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
            AND pull_request_message_ref.msg_id = message.msg_id
            AND pr_created_at::DATE >= :begin_date ::DATE
            AND pr_closed_at::DATE <=  :end_date ::DATE
        GROUP BY pull_requests.pull_request_id
        ) time_between_responses
        GROUP BY closed_year, closed_month, merged_status, time_between_responses.pr_closed_at, time_between_responses.average_time_between_responses
        """)


        with current_app.engine.connect() as conn:
            pr_all = pd.read_sql(pr_all_SQL, conn,
                params={'repo_id': repo_id, 'repo_group_id':repo_group_id,
                        'begin_date': begin_date, 'end_date': end_date})
    
    if pr_all.empty:
        return []
    
    if not repo_id:
        pr_avg_time_between_responses = pr_all.groupby(['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys).mean().reset_index()[['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys + ['average_{}_between_responses'.format(time_unit)]]
    else:
        pr_avg_time_between_responses = pr_all.groupby(['merged_status'] + time_group_bys).mean().reset_index()[time_group_bys + ['merged_status', 'average_{}_between_responses'.format(time_unit)]]

    return pr_avg_time_between_responses

@register_metric()
def pull_request_average_commit_counts(repo_group_id, repo_id=None, group_by='month', begin_date=None, end_date=None):
    """ Average commits per pull request, with merged status and time frame

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param group_by: The time frame the data is grouped by, options are: 'day', 'week', 'month' or 'year', defaults to 'month'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of average commits per pull request
    """

    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')


    unit_options = ['year', 'month', 'week', 'day']
    time_group_bys = []
    for unit in unit_options.copy():
        if group_by not in unit_options:
            continue
        time_group_bys.append('closed_{}'.format(unit))
        del unit_options[0]

    if not repo_id:
        pr_all_SQL = s.sql.text("""
        SELECT 
            repo_id,
            repo_name,
            repo_group_id,
            repo_group_name,
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day,
            commit_count AS average_commits_per_pull_request,
            count(*) AS pr_count
            FROM (
            SELECT 
                pull_requests.repo_id,
                repo.repo_name,
                repo_groups.repo_group_id,
                rg_name AS repo_group_name,
                pull_request_commits.pull_request_id, 
                count(DISTINCT pr_cmt_sha) AS commit_count,
                pr_merged_at,
                pr_closed_at,
                pr_created_at
            FROM augur_data.pull_request_commits, augur_data.pull_request_meta,augur_data.repo_groups, 
            augur_data.pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id IN 
                (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
                AND pull_requests.pull_request_id = pull_request_commits.pull_request_id
                AND pull_requests.pull_request_id = pull_request_meta.pull_request_id
                AND pr_cmt_sha <> pull_requests.pr_merge_commit_sha
                AND pr_cmt_sha <> pull_request_meta.pr_sha
                AND repo_groups.repo_group_id = repo.repo_group_id
                AND pr_created_at::DATE >= :begin_date ::DATE
                AND pr_closed_at::DATE <=  :end_date ::DATE
            GROUP BY pull_request_commits.pull_request_id, pr_merged_at, pr_closed_at, pr_created_at, repo.repo_name, pull_requests.repo_id, repo_groups.rg_name, repo_groups.repo_group_id
            ORDER BY pr_created_at
            ) data
            GROUP BY closed_year, merged_status, data.pr_closed_at, data.commit_count, data.repo_id, data.repo_name, data.repo_group_id, data.repo_group_name
            """)

    else:
        pr_all_SQL = s.sql.text("""
        SELECT 
        CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
        date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
        date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
        date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
        date_part( 'day', pr_closed_at :: DATE ) AS closed_day,
        commit_count AS average_commits_per_pull_request,
        count(*) AS pr_count
        FROM (
        SELECT 
            pull_request_commits.pull_request_id, 
            count(DISTINCT pr_cmt_sha) AS commit_count,
            pr_merged_at,
            pr_closed_at,
            pr_created_at
        FROM augur_data.pull_request_commits, augur_data.pull_requests, augur_data.pull_request_meta
        WHERE pull_requests.pull_request_id = pull_request_commits.pull_request_id
            AND pull_requests.pull_request_id = pull_request_meta.pull_request_id
            AND pull_requests.repo_id = :repo_id
            AND pr_cmt_sha <> pull_requests.pr_merge_commit_sha
            AND pr_cmt_sha <> pull_request_meta.pr_sha
            AND pr_created_at::DATE >= :begin_date ::DATE
            AND pr_closed_at::DATE <=  :end_date ::DATE
        GROUP BY pull_request_commits.pull_request_id, pr_merged_at, pr_closed_at, pr_created_at
        ORDER BY pr_created_at
        ) data
        GROUP BY closed_year, merged_status, data.pr_closed_at, data.commit_count
        """)


        with current_app.engine.connect() as conn:
            pr_all = pd.read_sql(pr_all_SQL, conn,
                params={'repo_id': repo_id, 'repo_group_id':repo_group_id,
                        'begin_date': begin_date, 'end_date': end_date})

    if pr_all.empty:
        return []    
        
    if not repo_id:
        pr_avg_commit_counts = pr_all.groupby(['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys).mean().reset_index()[['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys + ['average_commits_per_pull_request']]
    else:        
        pr_avg_commit_counts = pr_all.groupby(['merged_status'] + time_group_bys).mean().reset_index()[time_group_bys + ['merged_status', 'average_commits_per_pull_request']]

    return pr_avg_commit_counts

@register_metric()
def pull_request_average_event_counts(repo_group_id, repo_id=None, group_by='month', begin_date=None, end_date=None):
    """ Average of event counts with merged status and time frame

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param group_by: The time frame the data is grouped by, options are: 'day', 'week', 'month' or 'year', defaults to 'month'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of event counts avergages
    """

    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')


    unit_options = ['year', 'month', 'week', 'day']
    time_group_bys = []
    for unit in unit_options.copy():
        if group_by not in unit_options:
            continue
        time_group_bys.append('closed_{}'.format(unit))
        del unit_options[0]

    if not repo_id:
        pr_all_SQL = s.sql.text("""
        SELECT 
            repo_id,
            repo_name,
            repo_group_id,
            repo_group_name,
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day, 
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            assigned_count AS average_assigned_count,
            review_requested_count AS average_review_requested_count,
            labeled_count AS average_labeled_count,
            unlabeled_count AS average_unlabeled_count,
            subscribed_count AS average_subscribed_count,
            mentioned_count AS average_mentioned_count,
            referenced_count AS average_referenced_count,
            closed_count AS average_closed_count,
            head_ref_force_pushed_count AS average_head_ref_force_pushed_count,
            head_ref_deleted_count AS average_head_ref_deleted_count,
            milestoned_count AS average_milestoned_count,
            merged_count AS average_merged_count,
            comment_count AS average_comment_count,
            count(*) AS num_pull_requests
        FROM (
            SELECT 
            pull_requests.repo_id,
            repo_name,
            repo_groups.repo_group_id,
            rg_name AS repo_group_name,
            pull_requests.pull_request_id,
            pr_merged_at,
            pr_created_at,
            pr_closed_at,
            count(*) FILTER (WHERE action = 'assigned') AS assigned_count,
            count(*) FILTER (WHERE action = 'review_requested') AS review_requested_count,
            count(*) FILTER (WHERE action = 'labeled') AS labeled_count,
            count(*) FILTER (WHERE action = 'unlabeled') AS unlabeled_count,
            count(*) FILTER (WHERE action = 'subscribed') AS subscribed_count,
            count(*) FILTER (WHERE action = 'mentioned') AS mentioned_count,
            count(*) FILTER (WHERE action = 'referenced') AS referenced_count,
            count(*) FILTER (WHERE action = 'closed') AS closed_count,
            count(*) FILTER (WHERE action = 'head_ref_force_pushed') AS head_ref_force_pushed_count,
            count(*) FILTER (WHERE action = 'head_ref_deleted') AS head_ref_deleted_count,
            count(*) FILTER (WHERE action = 'milestoned') AS milestoned_count,
            count(*) FILTER (WHERE action = 'merged') AS merged_count,
            COUNT(DISTINCT message.msg_timestamp) AS comment_count
            FROM pull_request_events, pull_request_message_ref, message, repo_groups,
            pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
            WHERE pull_requests.repo_id IN 
                (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
                AND repo.repo_id = pull_requests.repo_id
                AND repo_groups.repo_group_id = repo.repo_group_id
                AND pull_requests.pull_request_id = pull_request_events.pull_request_id
                AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
                AND pull_request_message_ref.msg_id = message.msg_id
                AND pr_created_at::DATE >= :begin_date ::DATE
                AND pr_closed_at::DATE <=  :end_date ::DATE
                GROUP BY pull_requests.pull_request_id, repo.repo_name, repo_groups.repo_group_id, repo_groups.rg_name
                ) data
           GROUP BY closed_year, closed_month, closed_week, closed_day, merged_status, data.assigned_count, data.review_requested_count, data.labeled_count, data.unlabeled_count, data.subscribed_count, data.mentioned_count, data.referenced_count, data.closed_count, 
        data.head_ref_force_pushed_count, data.head_ref_deleted_count, data.milestoned_count, data.merged_count, data.comment_count, data.repo_id, data.repo_name, data.repo_group_id, data.repo_group_name
        ORDER BY merged_status, closed_year, closed_week, closed_day
        """)

    else:
        pr_all_SQL = s.sql.text("""
        SELECT 
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day, 
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            assigned_count AS average_assigned_count,
            review_requested_count AS average_review_requested_count,
            labeled_count AS average_labeled_count,
            unlabeled_count AS average_unlabeled_count,
            subscribed_count AS average_subscribed_count,
            mentioned_count AS average_mentioned_count,
            referenced_count AS average_referenced_count,
            closed_count AS average_closed_count,
            head_ref_force_pushed_count AS average_head_ref_force_pushed_count,
            head_ref_deleted_count AS average_head_ref_deleted_count,
            milestoned_count AS average_milestoned_count,
            merged_count AS average_merged_count,
            comment_count AS average_comment_count,
            count(*) AS num_pull_requests
        FROM (
            SELECT pull_requests.pull_request_id,
            pr_merged_at,
            pr_created_at,
            pr_closed_at,
            count(*) FILTER (WHERE action = 'assigned') AS assigned_count,
            count(*) FILTER (WHERE action = 'review_requested') AS review_requested_count,
            count(*) FILTER (WHERE action = 'labeled') AS labeled_count,
            count(*) FILTER (WHERE action = 'unlabeled') AS unlabeled_count,
            count(*) FILTER (WHERE action = 'subscribed') AS subscribed_count,
            count(*) FILTER (WHERE action = 'mentioned') AS mentioned_count,
            count(*) FILTER (WHERE action = 'referenced') AS referenced_count,
            count(*) FILTER (WHERE action = 'closed') AS closed_count,
            count(*) FILTER (WHERE action = 'head_ref_force_pushed') AS head_ref_force_pushed_count,
            count(*) FILTER (WHERE action = 'head_ref_deleted') AS head_ref_deleted_count,
            count(*) FILTER (WHERE action = 'milestoned') AS milestoned_count,
            count(*) FILTER (WHERE action = 'merged') AS merged_count,
            COUNT(DISTINCT message.msg_timestamp) AS comment_count
            FROM pull_request_events, pull_requests, repo, pull_request_message_ref, message
            WHERE repo.repo_id = :repo_id
                AND repo.repo_id = pull_requests.repo_id
                AND pull_requests.pull_request_id = pull_request_events.pull_request_id
                AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
                AND pull_request_message_ref.msg_id = message.msg_id
                AND pr_created_at::DATE >= :begin_date ::DATE
                AND pr_closed_at::DATE <= :end_date ::DATE
            GROUP BY pull_requests.pull_request_id
            ) data
        GROUP BY closed_year, closed_month, closed_week, closed_day, merged_status, data.assigned_count, data.review_requested_count, data.labeled_count, data.unlabeled_count, data.subscribed_count, data.mentioned_count, data.referenced_count, data.closed_count, 
        data.head_ref_force_pushed_count, data.head_ref_deleted_count, data.milestoned_count, data.merged_count, data.comment_count
        ORDER BY merged_status, closed_year, closed_week, closed_day
        """)


        with current_app.engine.connect() as conn:
            pr_all = pd.read_sql(pr_all_SQL, conn,
                params={'repo_id': repo_id, 'repo_group_id':repo_group_id,
                        'begin_date': begin_date, 'end_date': end_date})

    count_names = ['assigned_count', 'review_requested_count', 'labeled_count', 'unlabeled_count', 'subscribed_count', 'mentioned_count', 'referenced_count', 'closed_count', 'head_ref_force_pushed_count', 'head_ref_deleted_count', 'milestoned_count', 'merged_count', 'comment_count']
    average_count_names = []
    for name in count_names.copy(): 
        average_count_names.append('average_' + name)


    if pr_all.empty:
        return []

    if not repo_id:
        pr_avg_event_counts = pr_all.groupby(['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys).mean().reset_index()[['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys + average_count_names]
    else:
        pr_avg_event_counts = pr_all.groupby(['merged_status'] + time_group_bys).mean().reset_index()[['merged_status'] + time_group_bys + average_count_names]

    return pr_avg_event_counts

@register_metric()
def pull_request_average_time_to_responses_and_close(repo_group_id, repo_id=None, group_by='month', time_unit ='days', begin_date=None, end_date=None):
    """ Average of time to first reponse, last response, and time to close with merged status and time frame

    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param group_by: The time frame the data is grouped by, options are: 'day', 'week', 'month' or 'year', defaults to 'month'
    :param time_unit: Unit of time of data is in, options are: 'hours', or 'days', defaults to 'days'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of averages of time to first response, last response, and close
    """

    if not begin_date:
        begin_date = '1970-1-1'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')


    unit_options = ['year', 'month', 'week', 'day']
    time_group_bys = []
    for unit in unit_options.copy():
        if group_by not in unit_options:
            continue
        time_group_bys.append('closed_{}'.format(unit))
        del unit_options[0]

    if not repo_id:
        pr_all_SQL = s.sql.text("""
        SELECT 
            repo_id,
            repo_name,
            repo_group_id,
            repo_group_name,
            EXTRACT(epoch FROM(first_response_time - pr_created_at)/86400) AS average_days_to_first_response,
            EXTRACT(epoch FROM(first_response_time - pr_created_at)/3600) AS average_hours_to_first_response,
            EXTRACT(epoch FROM(last_response_time - pr_created_at)/86400) AS average_days_to_last_response,
            EXTRACT(epoch FROM(last_response_time - pr_created_at)/3600) AS average_hours_to_last_response,
            EXTRACT(epoch FROM(pr_closed_at - pr_created_at)/86400) AS average_days_to_close,
            EXTRACT(epoch FROM(pr_closed_at - pr_created_at)/3600) AS average_hours_to_close,
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day,
            count(*) AS num_pull_requests
        FROM (
        SELECT
            pull_requests.repo_id, 
            repo.repo_name,
            repo_groups.repo_group_id,
            rg_name AS repo_group_name,
            pull_requests.pull_request_id,
            MIN(message.msg_timestamp) AS first_response_time,
            MAX(message.msg_timestamp) AS last_response_time,
            pull_requests.pr_closed_at,
            pr_created_at,
            pull_requests.pr_merged_at
        FROM pull_request_message_ref, message, repo_groups,
        pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
        WHERE pull_requests.repo_id IN 
            (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND repo.repo_id = pull_requests.repo_id
            AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
            AND pull_request_message_ref.msg_id = message.msg_id
            AND repo_groups.repo_group_id = repo.repo_group_id
            AND pr_created_at::DATE >= :begin_date ::DATE
            AND pr_closed_at::DATE <= :end_date ::DATE
        GROUP BY pull_requests.pull_request_id, repo.repo_name, repo_groups.repo_group_id, repo_groups.rg_name
        ) response_times
        GROUP BY closed_year, merged_status, response_times.first_response_time, response_times.last_response_time, response_times.pr_created_at, response_times.pr_closed_at, response_times.repo_id, response_times.repo_name, response_times.repo_group_id, response_times.repo_group_name
        """)

    else:
        pr_all_SQL = s.sql.text("""
        SELECT 
            EXTRACT(epoch FROM(first_response_time - pr_created_at)/86400) AS average_days_to_first_response,
            EXTRACT(epoch FROM(first_response_time - pr_created_at)/3600) AS average_hours_to_first_response,
            EXTRACT(epoch FROM(last_response_time - pr_created_at)/86400) AS average_days_to_last_response,
            EXTRACT(epoch FROM(last_response_time - pr_created_at)/3600) AS average_hours_to_last_response,
            EXTRACT(epoch FROM(pr_closed_at - pr_created_at)/86400) AS average_days_to_close,
            EXTRACT(epoch FROM(pr_closed_at - pr_created_at)/3600) AS average_hours_to_close,
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day,
            count(*) AS num_pull_requests
        FROM (
        SELECT pull_requests.pull_request_id,
            MIN(message.msg_timestamp) AS first_response_time,
            MAX(message.msg_timestamp) AS last_response_time,
            pull_requests.pr_closed_at,
            pr_created_at,
            pull_requests.pr_merged_at
        FROM pull_requests, repo, pull_request_message_ref, message
        WHERE repo.repo_id = :repo_id
            AND repo.repo_id = pull_requests.repo_id
            AND pull_requests.pull_request_id = pull_request_message_ref.pull_request_id
            AND pull_request_message_ref.msg_id = message.msg_id
            AND pr_created_at::DATE >= :begin_date ::DATE
            AND pr_closed_at::DATE <= :end_date ::DATE
        GROUP BY pull_requests.pull_request_id
        ) response_times
        GROUP BY closed_year, merged_status, response_times.first_response_time, response_times.last_response_time, response_times.pr_created_at, response_times.pr_closed_at
        """)

    with current_app.engine.connect() as conn:
        pr_all = pd.read_sql(pr_all_SQL, conn,
            params={'repo_id': repo_id, 'repo_group_id':repo_group_id,
                    'begin_date': begin_date, 'end_date': end_date})

    if pr_all.empty:
        return []

    if not repo_id:
         avg_pr_time_to_responses_and_close  = pr_all.groupby(['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys).mean().reset_index()[['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys + ['average_{}_to_first_response'.format(time_unit), 'average_{}_to_last_response'.format(time_unit), 'average_{}_to_close'.format(time_unit)]]
    else:
        avg_pr_time_to_responses_and_close  = pr_all.groupby(['merged_status'] + time_group_bys).mean().reset_index()[time_group_bys + ['merged_status', 'average_{}_to_first_response'.format(time_unit), 'average_{}_to_last_response'.format(time_unit), 'average_{}_to_close'.format(time_unit)]]

    return avg_pr_time_to_responses_and_close

@register_metric()
def pull_request_merged_status_counts(repo_group_id, repo_id=None, begin_date='1970-1-1 00:00:01', end_date=None, group_by='month'):
    """ Merged status counts with time frames
    
    :param repo_group_id: The repository's repo_group_id
    :param repo_id: The repository's repo_id, defaults to None
    :param group_by: The time frame the data is grouped by, options are: 'day', 'week', 'month' or 'year', defaults to 'month'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of merged status counts
    """

    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    unit_options = ['year', 'month', 'week', 'day']
    time_group_bys = []
    for time_unit in unit_options.copy():
        if group_by not in unit_options:
            continue
        time_group_bys.append('closed_{}'.format(time_unit))
        del unit_options[0]

    if not repo_id:
        pr_all_sql = s.sql.text("""
        SELECT 
            repo_id,
            repo_name,
            repo_group_id,
            repo_group_name,
            pull_request_id AS pull_request_count,
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' END AS merged_status,
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day
        FROM (
        SELECT
            pull_requests.pull_request_id,
            pull_requests.repo_id,
            repo.repo_name,
            repo_groups.repo_group_id,
            rg_name AS repo_group_name,
            pr_merged_at,
            pr_closed_at
        FROM repo_groups,
        pull_requests JOIN repo ON pull_requests.repo_id = repo.repo_id
        WHERE pull_requests.repo_id IN
            (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
            AND repo_groups.repo_group_id = repo.repo_group_id
            AND pr_created_at::DATE >= :begin_date ::DATE
            AND pr_closed_at::DATE <= :end_date ::DATE
        GROUP BY pull_requests.pull_request_id, pull_requests.repo_id, repo.repo_name, repo_groups.repo_group_id, repo_groups.rg_name
        ) data 
        GROUP BY repo_id, repo_name, repo_group_id, repo_group_name, pull_request_id, pr_merged_at, pr_closed_at  
    """)
    else:
        pr_all_sql = s.sql.text("""
        SELECT 
            pull_request_id as pull_request_count,
            CASE WHEN pr_merged_at IS NULL THEN 'Rejected' ELSE 'Merged' end as merged_status,
            date_part( 'year', pr_closed_at :: DATE ) AS closed_year,
            date_part( 'month', pr_closed_at :: DATE ) AS closed_month,
            date_part( 'week', pr_closed_at :: DATE ) AS closed_week,
            date_part( 'day', pr_closed_at :: DATE ) AS closed_day
        from pull_requests
        where repo_id = :repo_id
            AND pr_created_at::date >= :begin_date ::date
            AND pr_closed_at::date <= :end_date ::date
        """)


        with current_app.engine.connect() as conn:
            pr_all = pd.read_sql(pr_all_sql, conn, params={'repo_group_id': repo_group_id, 
                'repo_id': repo_id, 'begin_date': begin_date, 'end_date': end_date})

    if not repo_id:
         pr_merged_counts = pr_all.groupby(['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys).count().reset_index()[['merged_status', 'repo_id', 'repo_name', 'repo_group_id', 'repo_group_name'] + time_group_bys + ['pull_request_count']]
    else:
        pr_merged_counts = pr_all.groupby(['merged_status'] + time_group_bys).count().reset_index()[time_group_bys + ['merged_status', 'pull_request_count']]
    
    return pr_merged_counts

@register_metric()
def accepted_change_requests_count(repo_group_id, repo_id=None, begin_date=None, end_date=None, submitter_id=None, merger_id=None):
    """
    Returns the number of accepted (merged) change requests.
    Definition:
    - Accepted change requests are pull requests that have been merged.
    - Data source: GitHub (via Augur's ingested database).

    Supported Filters:
    - Time period (begin_date, end_date)
    - Repository or repository group
    - Submitter (PR author) using Augur internal contributor ID (cntrb_id)
    - Merger (user who merged the PR) using Augur internal contributor ID (cntrb_id)

    :param repo_group_id: Repository group ID
    :param repo_id: Repository ID (optional)
    :param begin_date: Start date (optional)
    :param end_date: End date (optional)
    :param submitter_id: Augur contributor ID (cntrb_id) of PR author (optional)
    :param merger_id: Augur contributor ID (cntrb_id) of PR merger (optional)
    :return: DataFrame with accepted change request count
    """
    if not repo_id and not repo_group_id:
        raise ValueError("Must provide either repo_id or repo_group_id")
    
    if not begin_date:
        begin_date = '1970-01-01 00:00:01'
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Base query
    sql = """
        SELECT COUNT(DISTINCT pr.pull_request_id) AS accepted_change_requests
        FROM pull_requests pr
        JOIN repo r ON pr.repo_id = r.repo_id
        WHERE pr.pr_merged_at IS NOT NULL
          AND pr.pr_merged_at BETWEEN :begin_date AND :end_date
    """
    params = {
        'begin_date': begin_date,
        'end_date': end_date
    }
    # Repo / repo-group filter
    if repo_id:
        sql += " AND pr.repo_id = :repo_id"
        params['repo_id'] = repo_id
    else:
        sql += " AND r.repo_group_id = :repo_group_id"
        params['repo_group_id'] = repo_group_id

    # Submitter filter (PR author)
    if submitter_id:
        sql += " AND pr.pr_augur_contributor_id = :submitter_id"
        params['submitter_id'] = submitter_id

    # Merger filter (who merged PR)
    if merger_id:
        sql += """
            AND pr.pull_request_id IN (
                SELECT pre.pull_request_id
                FROM pull_request_events pre
                WHERE pre.action = 'merged'
                  AND pre.cntrb_id = :merger_id
            )
        """
        params['merger_id'] = merger_id

    # Execute query
    with current_app.engine.connect() as conn:
        results = pd.read_sql(s.sql.text(sql), conn, params=params)
    return results

