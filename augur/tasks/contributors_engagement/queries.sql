-- name: d0_engagement_query
SELECT DISTINCT ON (c.cntrb_login, cr.cntrb_category)
  c.cntrb_id,
  c.cntrb_login AS username,
  c.cntrb_full_name AS full_name,
  c.cntrb_country_code AS country,
  CASE 
    WHEN cr.repo_git ILIKE '%gitlab%' THEN 'GitLab'
    WHEN cr.repo_git ILIKE '%github%' THEN 'GitHub'
    ELSE 'Unknown'
  END AS platform,
  (cr.cntrb_category = 'ForkEvent') AS forked,
  (cr.cntrb_category = 'WatchEvent') AS starred_or_watched,
  cr.created_at AS engagement_timestamp
FROM 
  augur_data.contributors c
JOIN 
  augur_data.contributor_repo cr ON cr.cntrb_id = c.cntrb_id
WHERE 
  cr.cntrb_category IN ('ForkEvent', 'WatchEvent')
  AND cr.repo_git = (SELECT repo_git FROM augur_data.repo WHERE repo_id = :repo_id)
  {time_filter}
ORDER BY
  c.cntrb_login, cr.cntrb_category, cr.created_at;

-- name: create_d0_materialized_view
CREATE MATERIALIZED VIEW IF NOT EXISTS augur_data.d0_contributor_engagement AS
SELECT DISTINCT ON (c.cntrb_login, cr.cntrb_category)
  c.cntrb_login AS username,
  c.cntrb_full_name AS full_name,
  c.cntrb_country_code AS country,
  CASE 
    WHEN cr.repo_git ILIKE '%gitlab%' THEN 'GitLab'
    WHEN cr.repo_git ILIKE '%github%' THEN 'GitHub'
    ELSE 'Unknown'
  END AS platform,
  cr.cntrb_category = 'ForkEvent' AS forked,
  cr.cntrb_category = 'WatchEvent' AS starred_or_watched,
  cr.created_at AS engagement_timestamp
FROM 
  augur_data.contributors c
JOIN 
  augur_data.contributor_repo cr ON cr.cntrb_id = c.cntrb_id
WHERE 
  cr.cntrb_category IN ('ForkEvent', 'WatchEvent')
ORDER BY
  c.cntrb_login, cr.cntrb_category, cr.created_at;

-- name: refresh_d0_materialized_view
REFRESH MATERIALIZED VIEW augur_data.d0_contributor_engagement;


-- name: d1_engagement_query
SELECT
  c.cntrb_id,
  c.cntrb_login AS username,
  c.cntrb_full_name AS full_name,
  c.cntrb_country_code AS country,
  'GitHub' AS platform,
  MIN(i.created_at) AS first_issue_created_at,
  MIN(pr.pr_created_at) AS first_pr_opened_at,
  MIN(pm.msg_timestamp) AS first_pr_commented_at
FROM
  augur_data.contributors c

LEFT JOIN augur_data.issues i
  ON i.reporter_id = c.cntrb_id AND i.repo_id = :repo_id

LEFT JOIN augur_data.pull_requests pr
  ON pr.pr_augur_contributor_id = c.cntrb_id AND pr.repo_id = :repo_id

LEFT JOIN augur_data.pull_request_message_ref pmr
  ON pmr.pull_request_id = pr.pull_request_id
LEFT JOIN augur_data.message pm
  ON pm.msg_id = pmr.msg_id AND pm.cntrb_id = c.cntrb_id AND pm.repo_id = :repo_id

WHERE
  (i.created_at >= NOW() - INTERVAL '{time_filter}'
   OR pr.pr_created_at >= NOW() - INTERVAL '{time_filter}'
   OR pm.msg_timestamp >= NOW() - INTERVAL '{time_filter}')

GROUP BY
  c.cntrb_id, c.cntrb_login, c.cntrb_full_name, c.cntrb_country_code
HAVING
  MIN(i.created_at) IS NOT NULL 
  OR MIN(pr.pr_created_at) IS NOT NULL 
  OR MIN(pm.msg_timestamp) IS NOT NULL;

-- name: create_d1_materialized_view
CREATE MATERIALIZED VIEW IF NOT EXISTS augur_data.d1_contributor_engagement AS
SELECT
  c.cntrb_login AS username,
  MIN(i.created_at) AS first_issue_created_at,
  MIN(pr.pr_created_at) AS first_pr_opened_at,
  MIN(pm.msg_timestamp) AS first_pr_commented_at
FROM
  augur_data.contributors c
LEFT JOIN augur_data.issues i
  ON i.reporter_id = c.cntrb_id
LEFT JOIN augur_data.pull_requests pr
  ON pr.pr_augur_contributor_id = c.cntrb_id
LEFT JOIN augur_data.pull_request_message_ref pmr
  ON pmr.pull_request_id = pr.pull_request_id
LEFT JOIN augur_data.message pm
  ON pm.msg_id = pmr.msg_id AND pm.cntrb_id = c.cntrb_id
WHERE
  (i.created_at >= NOW() - INTERVAL '1 year'
   OR pr.pr_created_at >= NOW() - INTERVAL '1 year'
   OR pm.msg_timestamp >= NOW() - INTERVAL '1 year')
GROUP BY
  c.cntrb_login;

-- name: refresh_d1_materialized_view
REFRESH MATERIALIZED VIEW augur_data.d1_contributor_engagement;


-- name: d2_engagement_query
WITH pr_merged AS (
  SELECT DISTINCT pr.pr_augur_contributor_id
  FROM augur_data.pull_requests pr
  WHERE pr.pr_merged_at IS NOT NULL AND pr.repo_id = :repo_id
),

issue_counts AS (
  SELECT reporter_id AS cntrb_id, COUNT(*) AS issue_count
  FROM augur_data.issues
  WHERE repo_id = :repo_id
  GROUP BY reporter_id
),

comment_counts AS (
  SELECT m.cntrb_id, COUNT(*) AS total_comments
  FROM augur_data.message m
  LEFT JOIN augur_data.issue_message_ref imr ON imr.msg_id = m.msg_id
  LEFT JOIN augur_data.pull_request_message_ref pmr ON pmr.msg_id = m.msg_id
  LEFT JOIN augur_data.issues i ON i.issue_id = imr.issue_id
  LEFT JOIN augur_data.pull_requests pr ON pr.pull_request_id = pmr.pull_request_id
  WHERE m.repo_id = :repo_id 
    AND (i.repo_id = :repo_id OR pr.repo_id = :repo_id)
    AND (imr.issue_id IS NOT NULL OR pmr.pull_request_id IS NOT NULL)
  GROUP BY m.cntrb_id
),

pr_commits_over_3 AS (
  SELECT pr.pr_augur_contributor_id AS cntrb_id
  FROM augur_data.pull_requests pr
  JOIN augur_data.pull_request_commits prc ON prc.pull_request_id = pr.pull_request_id
  WHERE pr.repo_id = :repo_id
  GROUP BY pr.pr_augur_contributor_id, pr.pull_request_id
  HAVING COUNT(prc.pr_cmt_sha) > 3
),

commented_on_multiple_prs AS (
  SELECT m.cntrb_id
  FROM augur_data.message m
  JOIN augur_data.pull_request_message_ref pmr ON pmr.msg_id = m.msg_id
  JOIN augur_data.pull_requests pr ON pr.pull_request_id = pmr.pull_request_id
  WHERE m.repo_id = :repo_id AND pr.repo_id = :repo_id
  GROUP BY m.cntrb_id
  HAVING COUNT(DISTINCT pmr.pull_request_id) > 2
)

SELECT 
  c.cntrb_id,
  c.cntrb_login AS username,
  c.cntrb_full_name AS full_name,
  c.cntrb_country_code AS country,
  'GitHub' AS platform,
  CASE WHEN pm.pr_augur_contributor_id IS NOT NULL THEN true ELSE false END AS has_merged_pr,
  CASE WHEN ic.issue_count > 5 THEN true ELSE false END AS created_many_issues,
  COALESCE(cc.total_comments, 0) AS total_comments,
  CASE WHEN pco3.cntrb_id IS NOT NULL THEN true ELSE false END AS has_pr_with_many_commits,
  CASE WHEN cmp.cntrb_id IS NOT NULL THEN true ELSE false END AS commented_on_multiple_prs
FROM augur_data.contributors c
LEFT JOIN pr_merged pm ON pm.pr_augur_contributor_id = c.cntrb_id
LEFT JOIN issue_counts ic ON ic.cntrb_id = c.cntrb_id
LEFT JOIN comment_counts cc ON cc.cntrb_id = c.cntrb_id
LEFT JOIN pr_commits_over_3 pco3 ON pco3.cntrb_id = c.cntrb_id
LEFT JOIN commented_on_multiple_prs cmp ON cmp.cntrb_id = c.cntrb_id
WHERE (pm.pr_augur_contributor_id IS NOT NULL 
       OR ic.cntrb_id IS NOT NULL 
       OR cc.cntrb_id IS NOT NULL 
       OR pco3.cntrb_id IS NOT NULL 
       OR cmp.cntrb_id IS NOT NULL);

-- name: create_d2_materialized_view
CREATE MATERIALIZED VIEW IF NOT EXISTS augur_data.d2_contributor_engagement AS
WITH pr_merged AS (
  SELECT DISTINCT pr.pr_augur_contributor_id
  FROM augur_data.pull_requests pr
  WHERE pr.pr_merged_at IS NOT NULL
),

issue_counts AS (
  SELECT reporter_id AS cntrb_id, COUNT(*) AS issue_count
  FROM augur_data.issues
  GROUP BY reporter_id
),

comment_counts AS (
  SELECT m.cntrb_id, COUNT(*) AS total_comments
  FROM augur_data.message m
  LEFT JOIN augur_data.issue_message_ref imr ON imr.msg_id = m.msg_id
  LEFT JOIN augur_data.pull_request_message_ref pmr ON pmr.msg_id = m.msg_id
  WHERE imr.issue_id IS NOT NULL OR pmr.pull_request_id IS NOT NULL
  GROUP BY m.cntrb_id
),

pr_commits_over_3 AS (
  SELECT pr.pr_augur_contributor_id AS cntrb_id
  FROM augur_data.pull_requests pr
  JOIN augur_data.pull_request_commits prc ON prc.pull_request_id = pr.pull_request_id
  GROUP BY pr.pr_augur_contributor_id, pr.pull_request_id
  HAVING COUNT(prc.pr_cmt_sha) > 3
),

commented_on_multiple_prs AS (
  SELECT m.cntrb_id
  FROM augur_data.message m
  JOIN augur_data.pull_request_message_ref pmr ON pmr.msg_id = m.msg_id
  GROUP BY m.cntrb_id
  HAVING COUNT(DISTINCT pmr.pull_request_id) > 2
)

SELECT 
  c.cntrb_login AS username,
  CASE WHEN pm.pr_augur_contributor_id IS NOT NULL THEN true ELSE false END AS has_merged_pr,
  CASE WHEN ic.issue_count > 5 THEN true ELSE false END AS created_many_issues,
  COALESCE(cc.total_comments, 0) AS total_comments,
  CASE WHEN pco3.cntrb_id IS NOT NULL THEN true ELSE false END AS has_pr_with_many_commits,
  CASE WHEN cmp.cntrb_id IS NOT NULL THEN true ELSE false END AS commented_on_multiple_prs
FROM augur_data.contributors c
LEFT JOIN pr_merged pm ON pm.pr_augur_contributor_id = c.cntrb_id
LEFT JOIN issue_counts ic ON ic.cntrb_id = c.cntrb_id
LEFT JOIN comment_counts cc ON cc.cntrb_id = c.cntrb_id
LEFT JOIN pr_commits_over_3 pco3 ON pco3.cntrb_id = c.cntrb_id
LEFT JOIN commented_on_multiple_prs cmp ON cmp.cntrb_id = c.cntrb_id;

-- name: refresh_d2_materialized_view
REFRESH MATERIALIZED VIEW augur_data.d2_contributor_engagement;

-- name: create_contributor_engagement_table
CREATE TABLE IF NOT EXISTS augur_data.contributor_engagement (
    engagement_id BIGSERIAL PRIMARY KEY,
    repo_id BIGINT NOT NULL REFERENCES augur_data.repo(repo_id),
    cntrb_id UUID NOT NULL REFERENCES augur_data.contributors(cntrb_id),
    username VARCHAR NOT NULL,
    full_name VARCHAR,
    country VARCHAR,
    platform VARCHAR,
    d0_forked BOOLEAN DEFAULT FALSE,
    d0_starred_or_watched BOOLEAN DEFAULT FALSE,
    d0_engagement_timestamp TIMESTAMP(6),
    d1_first_issue_created_at TIMESTAMP(6),
    d1_first_pr_opened_at TIMESTAMP(6),
    d1_first_pr_commented_at TIMESTAMP(6),
    d2_has_merged_pr BOOLEAN DEFAULT FALSE,
    d2_created_many_issues BOOLEAN DEFAULT FALSE,
    d2_total_comments BIGINT DEFAULT 0,
    d2_has_pr_with_many_commits BOOLEAN DEFAULT FALSE,
    d2_commented_on_multiple_prs BOOLEAN DEFAULT FALSE,
    tool_source VARCHAR,
    tool_version VARCHAR,
    data_source VARCHAR,
    data_collection_date TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repo_id, cntrb_id)
);

-- name: create_contributor_engagement_indexes
CREATE INDEX IF NOT EXISTS idx_contributor_engagement_repo_id ON augur_data.contributor_engagement(repo_id);
CREATE INDEX IF NOT EXISTS idx_contributor_engagement_cntrb_id ON augur_data.contributor_engagement(cntrb_id);
CREATE INDEX IF NOT EXISTS idx_contributor_engagement_username ON augur_data.contributor_engagement(username);
CREATE INDEX IF NOT EXISTS idx_contributor_engagement_platform ON augur_data.contributor_engagement(platform);


-- name: create_contributor_engagement_sequence
CREATE SEQUENCE IF NOT EXISTS augur_data.contributor_engagement_engagement_id_seq
    OWNED BY augur_data.contributor_engagement.engagement_id;
