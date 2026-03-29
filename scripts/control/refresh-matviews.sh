#!/bin/sh
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.api_get_all_repos_issues with data;'
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.explorer_commits_and_committers_daily_count with data;'
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.api_get_all_repo_prs with data;'
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.api_get_all_repos_commits with data;'
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.augur_new_contributors with data;'
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.explorer_contributor_actions with data;'
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.explorer_new_contributors with data;'
psql -U augur -h localhost -p 5432 -d padres -c 'REFRESH MATERIALIZED VIEW augur_data.explorer_entry_list with data;'
