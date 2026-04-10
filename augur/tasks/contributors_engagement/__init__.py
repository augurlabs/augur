"""
Contributor Engagement Tasks

This module contains tasks for collecting and processing contributor engagement data
at different levels (D0, D1, D2) as defined in the CHAOSS metrics.

D0: Basic engagement (forks, stars/watches)
D1: Issue/review engagement (first issue, first PR, first comment)
D2: Significant contributions (merged PRs, many issues, multiple comments)
"""

from augur.tasks.contributors_engagement.worker import (
    collect_contributor_engagement,
    collect_d0_engagement,
    collect_d1_engagement,
    collect_d2_engagement
)

__all__ = [
    'collect_contributor_engagement',
    'collect_d0_engagement', 
    'collect_d1_engagement',
    'collect_d2_engagement'
]
