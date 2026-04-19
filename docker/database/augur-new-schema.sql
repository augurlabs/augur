--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3 (Homebrew)
-- Dumped by pg_dump version 16.3 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: augur_data; Type: SCHEMA; Schema: -; Owner: augur
--

CREATE SCHEMA augur_data;


ALTER SCHEMA augur_data OWNER TO augur;

--
-- Name: augur_operations; Type: SCHEMA; Schema: -; Owner: augur
--

CREATE SCHEMA augur_operations;


ALTER SCHEMA augur_operations OWNER TO augur;

--
-- Name: spdx; Type: SCHEMA; Schema: -; Owner: augur
--

CREATE SCHEMA spdx;


ALTER SCHEMA spdx OWNER TO augur;

--
-- Name: toss_specific; Type: SCHEMA; Schema: -; Owner: augur
--

CREATE SCHEMA toss_specific;


ALTER SCHEMA toss_specific OWNER TO augur;

--
-- Name: refresh_aggregates(); Type: PROCEDURE; Schema: augur_data; Owner: augur
--

CREATE PROCEDURE augur_data.refresh_aggregates()
    LANGUAGE plpgsql
    AS $$
    begin
        perform pg_advisory_lock(124);
        execute 'REFRESH MATERIALIZED VIEW "augur_data"."issue_reporter_created_at"';
        perform pg_advisory_unlock(124);
    end;
$$;


ALTER PROCEDURE augur_data.refresh_aggregates() OWNER TO augur;

--
-- Name: create_constraint_if_not_exists(text, text, text); Type: FUNCTION; Schema: public; Owner: augur
--

CREATE FUNCTION public.create_constraint_if_not_exists(t_name text, c_name text, constraint_sql text) RETURNS void
    LANGUAGE plpgsql
    AS $$
  BEGIN
    -- Look for our constraint
    IF NOT EXISTS (SELECT constraint_name
                   FROM information_schema.constraint_column_usage
                   WHERE constraint_name = c_name) THEN
        EXECUTE 'ALTER TABLE ' || t_name || ' ADD CONSTRAINT ' || c_name || ' ' || constraint_sql;
    END IF;
  END;
$$;


ALTER FUNCTION public.create_constraint_if_not_exists(t_name text, c_name text, constraint_sql text) OWNER TO augur;

--
-- Name: pc_chartoint(character varying); Type: FUNCTION; Schema: public; Owner: augur
--

CREATE FUNCTION public.pc_chartoint(chartoconvert character varying) RETURNS integer
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$
SELECT CASE WHEN trim($1) SIMILAR TO '[0-9]+' 
        THEN CAST(trim($1) AS integer) 
    ELSE NULL END;

$_$;


ALTER FUNCTION public.pc_chartoint(chartoconvert character varying) OWNER TO augur;

--
-- Name: refresh_aggregates(); Type: PROCEDURE; Schema: public; Owner: augur
--

CREATE PROCEDURE public.refresh_aggregates()
    LANGUAGE plpgsql
    AS $$
    begin
        perform pg_advisory_lock(124);
        execute 'REFRESH MATERIALIZED VIEW "augur_data"."issue_reporter_created_at"';
        perform pg_advisory_unlock(124);
    end;
$$;


ALTER PROCEDURE public.refresh_aggregates() OWNER TO augur;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: analysis_log; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.analysis_log (
    repos_id integer NOT NULL,
    status character varying NOT NULL,
    date_attempted timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE augur_data.analysis_log OWNER TO augur;

--
-- Name: pull_requests_pull_request_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_requests_pull_request_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_requests_pull_request_id_seq OWNER TO augur;

--
-- Name: pull_requests; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_requests (
    pull_request_id bigint DEFAULT nextval('augur_data.pull_requests_pull_request_id_seq'::regclass) NOT NULL,
    repo_id bigint DEFAULT 0,
    pr_url character varying,
    pr_src_id bigint,
    pr_src_node_id character varying,
    pr_html_url character varying,
    pr_diff_url character varying,
    pr_patch_url character varying,
    pr_issue_url character varying,
    pr_augur_issue_id bigint,
    pr_src_number bigint,
    pr_src_state character varying,
    pr_src_locked boolean,
    pr_src_title character varying,
    pr_body text,
    pr_created_at timestamp(0) without time zone,
    pr_updated_at timestamp(0) without time zone,
    pr_closed_at timestamp(0) without time zone,
    pr_merged_at timestamp(0) without time zone,
    pr_merge_commit_sha character varying,
    pr_teams bigint,
    pr_milestone character varying,
    pr_commits_url character varying,
    pr_review_comments_url character varying,
    pr_review_comment_url character varying,
    pr_comments_url character varying,
    pr_statuses_url character varying,
    pr_meta_head_id character varying,
    pr_meta_base_id character varying,
    pr_src_issue_url character varying,
    pr_src_comments_url character varying,
    pr_src_review_comments_url character varying,
    pr_src_commits_url character varying,
    pr_src_statuses_url character varying,
    pr_src_author_association character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    pr_augur_contributor_id uuid
);


ALTER TABLE augur_data.pull_requests OWNER TO augur;

--
-- Name: COLUMN pull_requests.pr_src_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_src_id IS 'The pr_src_id is unique across all of github.';


--
-- Name: COLUMN pull_requests.pr_augur_issue_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_augur_issue_id IS 'This is to link to the augur stored related issue';


--
-- Name: COLUMN pull_requests.pr_src_number; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_src_number IS 'The pr_src_number is unique within a repository.';


--
-- Name: COLUMN pull_requests.pr_teams; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_teams IS 'One to many with pull request teams. ';


--
-- Name: COLUMN pull_requests.pr_review_comment_url; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_review_comment_url IS 'This is a field with limited utility. It does expose how to access a specific comment if needed with parameters. If the source changes URL structure, it may be useful';


--
-- Name: COLUMN pull_requests.pr_meta_head_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_meta_head_id IS 'The metadata for the head repo that links to the pull_request_meta table. ';


--
-- Name: COLUMN pull_requests.pr_meta_base_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_meta_base_id IS 'The metadata for the base repo that links to the pull_request_meta table. ';


--
-- Name: COLUMN pull_requests.pr_augur_contributor_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_requests.pr_augur_contributor_id IS 'This is to link to the augur contributor record. ';


--
-- Name: api_get_all_repo_prs; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.api_get_all_repo_prs AS
 SELECT repo_id,
    count(*) AS pull_requests_all_time
   FROM augur_data.pull_requests
  GROUP BY repo_id
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.api_get_all_repo_prs OWNER TO augur;

--
-- Name: commits_cmt_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.commits_cmt_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.commits_cmt_id_seq OWNER TO augur;

--
-- Name: commits; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.commits (
    cmt_id bigint DEFAULT nextval('augur_data.commits_cmt_id_seq'::regclass) NOT NULL,
    repo_id bigint NOT NULL,
    cmt_commit_hash character varying(80) NOT NULL,
    cmt_author_name character varying NOT NULL,
    cmt_author_raw_email character varying NOT NULL,
    cmt_author_email character varying NOT NULL,
    cmt_author_date character varying(10) NOT NULL,
    cmt_author_affiliation character varying,
    cmt_committer_name character varying NOT NULL,
    cmt_committer_raw_email character varying NOT NULL,
    cmt_committer_email character varying NOT NULL,
    cmt_committer_date character varying NOT NULL,
    cmt_committer_affiliation character varying,
    cmt_added integer NOT NULL,
    cmt_removed integer NOT NULL,
    cmt_whitespace integer NOT NULL,
    cmt_filename character varying NOT NULL,
    cmt_date_attempted timestamp(0) without time zone NOT NULL,
    cmt_ght_committer_id integer,
    cmt_ght_committed_at timestamp(0) without time zone,
    cmt_committer_timestamp timestamp(0) with time zone,
    cmt_author_timestamp timestamp(0) with time zone,
    cmt_author_platform_username character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cmt_ght_author_id uuid
)
WITH (autovacuum_vacuum_scale_factor='0', autovacuum_vacuum_threshold='1000');


ALTER TABLE augur_data.commits OWNER TO augur;

--
-- Name: TABLE commits; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.commits IS 'Commits.
Each row represents changes to one FILE within a single commit. So you will encounter multiple rows per commit hash in many cases. ';


--
-- Name: api_get_all_repos_commits; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.api_get_all_repos_commits AS
 SELECT repo_id,
    count(DISTINCT cmt_commit_hash) AS commits_all_time
   FROM augur_data.commits
  GROUP BY repo_id
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.api_get_all_repos_commits OWNER TO augur;

--
-- Name: issue_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.issue_seq
    START WITH 31000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.issue_seq OWNER TO augur;

--
-- Name: issues; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.issues (
    issue_id bigint DEFAULT nextval('augur_data.issue_seq'::regclass) NOT NULL,
    repo_id bigint,
    pull_request bigint,
    pull_request_id bigint,
    created_at timestamp(0) without time zone,
    issue_title character varying,
    issue_body character varying,
    comment_count bigint,
    updated_at timestamp(0) without time zone,
    closed_at timestamp(0) without time zone,
    due_on timestamp(0) without time zone,
    repository_url character varying,
    issue_url character varying,
    labels_url character varying,
    comments_url character varying,
    events_url character varying,
    html_url character varying,
    issue_state character varying,
    issue_node_id character varying,
    gh_issue_number bigint,
    gh_issue_id bigint,
    gh_user_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    reporter_id uuid,
    cntrb_id uuid
);


ALTER TABLE augur_data.issues OWNER TO augur;

--
-- Name: COLUMN issues.reporter_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issues.reporter_id IS 'The ID of the person who opened the issue. ';


--
-- Name: COLUMN issues.cntrb_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issues.cntrb_id IS 'The ID of the person who closed the issue. ';


--
-- Name: api_get_all_repos_issues; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.api_get_all_repos_issues AS
 SELECT repo_id,
    count(*) AS issues_all_time
   FROM augur_data.issues
  WHERE (pull_request IS NULL)
  GROUP BY repo_id
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.api_get_all_repos_issues OWNER TO augur;

--
-- Name: augur_data.repo_insights_ri_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data."augur_data.repo_insights_ri_id_seq"
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data."augur_data.repo_insights_ri_id_seq" OWNER TO augur;

--
-- Name: contributors; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.contributors (
    cntrb_login character varying,
    cntrb_email character varying,
    cntrb_full_name character varying,
    cntrb_company character varying,
    cntrb_created_at timestamp(0) without time zone,
    cntrb_type character varying,
    cntrb_fake smallint DEFAULT 0,
    cntrb_deleted smallint DEFAULT 0,
    cntrb_long numeric(11,8) DEFAULT NULL::numeric,
    cntrb_lat numeric(10,8) DEFAULT NULL::numeric,
    cntrb_country_code character(3) DEFAULT NULL::bpchar,
    cntrb_state character varying,
    cntrb_city character varying,
    cntrb_location character varying,
    cntrb_canonical character varying,
    cntrb_last_used timestamp(0) with time zone DEFAULT NULL::timestamp with time zone,
    gh_user_id bigint,
    gh_login character varying,
    gh_url character varying,
    gh_html_url character varying,
    gh_node_id character varying,
    gh_avatar_url character varying,
    gh_gravatar_id character varying,
    gh_followers_url character varying,
    gh_following_url character varying,
    gh_gists_url character varying,
    gh_starred_url character varying,
    gh_subscriptions_url character varying,
    gh_organizations_url character varying,
    gh_repos_url character varying,
    gh_events_url character varying,
    gh_received_events_url character varying,
    gh_type character varying,
    gh_site_admin character varying,
    gl_web_url character varying,
    gl_avatar_url character varying,
    gl_state character varying,
    gl_username character varying,
    gl_full_name character varying,
    gl_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid NOT NULL
);


ALTER TABLE augur_data.contributors OWNER TO augur;

--
-- Name: TABLE contributors; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.contributors IS 'For GitHub, this should be repeated from gh_login. for other systems, it should be that systems login. 
Github now allows a user to change their login name, but their user id remains the same in this case. So, the natural key is the combination of id and login, but there should never be repeated logins. ';


--
-- Name: COLUMN contributors.cntrb_login; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.cntrb_login IS 'Will be a double population with the same value as gh_login for github, but the local value for other systems. ';


--
-- Name: COLUMN contributors.cntrb_email; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.cntrb_email IS 'This needs to be here for matching contributor ids, which are augur, to the commit information. ';


--
-- Name: COLUMN contributors.cntrb_type; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.cntrb_type IS 'Present in another models. It is not currently used in Augur. ';


--
-- Name: COLUMN contributors.gh_login; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.gh_login IS 'populated with the github user name for github originated data. ';


--
-- Name: COLUMN contributors.gl_web_url; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.gl_web_url IS '“web_url” value from these API calls to GitLab, all for the same user

https://gitlab.com/api/v4/users?username=computationalmystic
https://gitlab.com/api/v4/users?search=s@goggins.com
https://gitlab.com/api/v4/users?search=outdoors@acm.org

[
  {
    "id": 5481034,
    "name": "sean goggins",
    "username": "computationalmystic",
    "state": "active",
    "avatar_url": "https://secure.gravatar.com/avatar/fb1fb43953a6059df2fe8d94b21d575c?s=80&d=identicon",
    "web_url": "https://gitlab.com/computationalmystic"
  }
]';


--
-- Name: COLUMN contributors.gl_avatar_url; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.gl_avatar_url IS '“avatar_url” value from these API calls to GitLab, all for the same user

https://gitlab.com/api/v4/users?username=computationalmystic
https://gitlab.com/api/v4/users?search=s@goggins.com
https://gitlab.com/api/v4/users?search=outdoors@acm.org

[
  {
    "id": 5481034,
    "name": "sean goggins",
    "username": "computationalmystic",
    "state": "active",
    "avatar_url": "https://secure.gravatar.com/avatar/fb1fb43953a6059df2fe8d94b21d575c?s=80&d=identicon",
    "web_url": "https://gitlab.com/computationalmystic"
  }
]';


--
-- Name: COLUMN contributors.gl_state; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.gl_state IS '“state” value from these API calls to GitLab, all for the same user

https://gitlab.com/api/v4/users?username=computationalmystic
https://gitlab.com/api/v4/users?search=s@goggins.com
https://gitlab.com/api/v4/users?search=outdoors@acm.org

[
  {
    "id": 5481034,
    "name": "sean goggins",
    "username": "computationalmystic",
    "state": "active",
    "avatar_url": "https://secure.gravatar.com/avatar/fb1fb43953a6059df2fe8d94b21d575c?s=80&d=identicon",
    "web_url": "https://gitlab.com/computationalmystic"
  }
]';


--
-- Name: COLUMN contributors.gl_username; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.gl_username IS '“username” value from these API calls to GitLab, all for the same user

https://gitlab.com/api/v4/users?username=computationalmystic
https://gitlab.com/api/v4/users?search=s@goggins.com
https://gitlab.com/api/v4/users?search=outdoors@acm.org

[
  {
    "id": 5481034,
    "name": "sean goggins",
    "username": "computationalmystic",
    "state": "active",
    "avatar_url": "https://secure.gravatar.com/avatar/fb1fb43953a6059df2fe8d94b21d575c?s=80&d=identicon",
    "web_url": "https://gitlab.com/computationalmystic"
  }
]';


--
-- Name: COLUMN contributors.gl_full_name; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.gl_full_name IS '“name” value from these API calls to GitLab, all for the same user

https://gitlab.com/api/v4/users?username=computationalmystic
https://gitlab.com/api/v4/users?search=s@goggins.com
https://gitlab.com/api/v4/users?search=outdoors@acm.org

[
  {
    "id": 5481034,
    "name": "sean goggins",
    "username": "computationalmystic",
    "state": "active",
    "avatar_url": "https://secure.gravatar.com/avatar/fb1fb43953a6059df2fe8d94b21d575c?s=80&d=identicon",
    "web_url": "https://gitlab.com/computationalmystic"
  }
]';


--
-- Name: COLUMN contributors.gl_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributors.gl_id IS '"id" value from these API calls to GitLab, all for the same user

https://gitlab.com/api/v4/users?username=computationalmystic
https://gitlab.com/api/v4/users?search=s@goggins.com
https://gitlab.com/api/v4/users?search=outdoors@acm.org

[
  {
    "id": 5481034,
    "name": "sean goggins",
    "username": "computationalmystic",
    "state": "active",
    "avatar_url": "https://secure.gravatar.com/avatar/fb1fb43953a6059df2fe8d94b21d575c?s=80&d=identicon",
    "web_url": "https://gitlab.com/computationalmystic"
  }
]';


--
-- Name: issue_events_event_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.issue_events_event_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.issue_events_event_id_seq OWNER TO augur;

--
-- Name: issue_events; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.issue_events (
    event_id bigint DEFAULT nextval('augur_data.issue_events_event_id_seq'::regclass) NOT NULL,
    issue_id bigint NOT NULL,
    repo_id bigint,
    action character varying NOT NULL,
    action_commit_hash character varying,
    created_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    node_id character varying,
    node_url character varying,
    platform_id bigint NOT NULL,
    issue_event_src_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid
);


ALTER TABLE augur_data.issue_events OWNER TO augur;

--
-- Name: COLUMN issue_events.node_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issue_events.node_id IS 'This should be renamed to issue_event_src_node_id, as its the varchar identifier in GitHub and likely common in other sources as well. However, since it was created before we came to this naming standard and workers are built around it, we have it simply named as node_id. Anywhere you see node_id in the schema, it comes from GitHubs terminology.';


--
-- Name: COLUMN issue_events.issue_event_src_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issue_events.issue_event_src_id IS 'This ID comes from the source. In the case of GitHub, it is the id that is the first field returned from the issue events API';


--
-- Name: issue_message_ref_issue_msg_ref_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.issue_message_ref_issue_msg_ref_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.issue_message_ref_issue_msg_ref_id_seq OWNER TO augur;

--
-- Name: issue_message_ref; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.issue_message_ref (
    issue_msg_ref_id bigint DEFAULT nextval('augur_data.issue_message_ref_issue_msg_ref_id_seq'::regclass) NOT NULL,
    issue_id bigint,
    repo_id bigint,
    msg_id bigint,
    issue_msg_ref_src_node_id character varying,
    issue_msg_ref_src_comment_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.issue_message_ref OWNER TO augur;

--
-- Name: COLUMN issue_message_ref.issue_msg_ref_src_node_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issue_message_ref.issue_msg_ref_src_node_id IS 'This character based identifier comes from the source. In the case of GitHub, it is the id that is the first field returned from the issue comments API';


--
-- Name: COLUMN issue_message_ref.issue_msg_ref_src_comment_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issue_message_ref.issue_msg_ref_src_comment_id IS 'This ID comes from the source. In the case of GitHub, it is the id that is the first field returned from the issue comments API';


--
-- Name: message_msg_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.message_msg_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.message_msg_id_seq OWNER TO augur;

--
-- Name: message; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.message (
    msg_id bigint DEFAULT nextval('augur_data.message_msg_id_seq'::regclass) NOT NULL,
    rgls_id bigint,
    platform_msg_id bigint,
    platform_node_id character varying,
    repo_id bigint,
    msg_text character varying,
    msg_timestamp timestamp(0) without time zone,
    msg_sender_email character varying,
    msg_header character varying,
    pltfrm_id bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid
);


ALTER TABLE augur_data.message OWNER TO augur;

--
-- Name: COLUMN message.cntrb_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message.cntrb_id IS 'Not populated for mailing lists. Populated for GitHub issues. ';


--
-- Name: pull_request_events_pr_event_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_events_pr_event_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_events_pr_event_id_seq OWNER TO augur;

--
-- Name: pull_request_events; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_events (
    pr_event_id bigint DEFAULT nextval('augur_data.pull_request_events_pr_event_id_seq'::regclass) NOT NULL,
    pull_request_id bigint NOT NULL,
    repo_id bigint,
    action character varying NOT NULL,
    action_commit_hash character varying,
    created_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    issue_event_src_id bigint,
    node_id character varying,
    node_url character varying,
    platform_id bigint DEFAULT 25150 NOT NULL,
    pr_platform_event_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid
);


ALTER TABLE augur_data.pull_request_events OWNER TO augur;

--
-- Name: COLUMN pull_request_events.issue_event_src_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_events.issue_event_src_id IS 'This ID comes from the source. In the case of GitHub, it is the id that is the first field returned from the issue events API';


--
-- Name: COLUMN pull_request_events.node_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_events.node_id IS 'This should be renamed to issue_event_src_node_id, as its the varchar identifier in GitHub and likely common in other sources as well. However, since it was created before we came to this naming standard and workers are built around it, we have it simply named as node_id. Anywhere you see node_id in the schema, it comes from GitHubs terminology.';


--
-- Name: pull_request_message_ref_pr_msg_ref_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_message_ref_pr_msg_ref_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_message_ref_pr_msg_ref_id_seq OWNER TO augur;

--
-- Name: pull_request_message_ref; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_message_ref (
    pr_msg_ref_id bigint DEFAULT nextval('augur_data.pull_request_message_ref_pr_msg_ref_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    repo_id bigint,
    msg_id bigint,
    pr_message_ref_src_comment_id bigint,
    pr_message_ref_src_node_id character varying,
    pr_issue_url character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.pull_request_message_ref OWNER TO augur;

--
-- Name: pull_request_reviews_pr_review_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_reviews_pr_review_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_reviews_pr_review_id_seq OWNER TO augur;

--
-- Name: pull_request_reviews; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_reviews (
    pr_review_id bigint DEFAULT nextval('augur_data.pull_request_reviews_pr_review_id_seq'::regclass) NOT NULL,
    pull_request_id bigint NOT NULL,
    repo_id bigint,
    pr_review_author_association character varying,
    pr_review_state character varying,
    pr_review_body character varying,
    pr_review_submitted_at timestamp(6) without time zone,
    pr_review_src_id bigint,
    pr_review_node_id character varying,
    pr_review_html_url character varying,
    pr_review_pull_request_url character varying,
    pr_review_commit_id character varying,
    platform_id bigint DEFAULT 25150,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid NOT NULL
);


ALTER TABLE augur_data.pull_request_reviews OWNER TO augur;

--
-- Name: repo_repo_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_repo_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_repo_id_seq OWNER TO augur;

--
-- Name: repo; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo (
    repo_id bigint DEFAULT nextval('augur_data.repo_repo_id_seq'::regclass) NOT NULL,
    repo_group_id bigint NOT NULL,
    repo_git character varying NOT NULL,
    repo_path character varying DEFAULT 'NULL'::character varying,
    repo_name character varying DEFAULT 'NULL'::character varying,
    repo_added timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    repo_type character varying DEFAULT ''::character varying,
    url character varying,
    owner_id integer,
    description character varying,
    primary_language character varying,
    created_at character varying,
    forked_from character varying,
    updated_at timestamp(0) without time zone,
    repo_archived_date_collected timestamp(0) with time zone,
    repo_archived integer,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo OWNER TO augur;

--
-- Name: TABLE repo; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo IS 'This table is a combination of the columns in Facade’s repo table and GHTorrent’s projects table. ';


--
-- Name: COLUMN repo.repo_type; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo.repo_type IS 'This field is intended to indicate if the repository is the "main instance" of a repository in cases where implementations choose to add the same repository to more than one repository group. In cases where the repository group is of rg_type Github Organization then this repo_type should be "primary". In other cases the repo_type should probably be "user created". We made this a varchar in order to hold open the possibility that there are additional repo_types we have not thought about. ';


--
-- Name: augur_new_contributors; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.augur_new_contributors AS
 SELECT a.id AS cntrb_id,
    a.created_at,
    a.repo_id,
    a.action,
    repo.repo_name,
    a.login,
    row_number() OVER (PARTITION BY a.id, a.repo_id ORDER BY a.created_at DESC) AS rank
   FROM ( SELECT commits.cmt_ght_author_id AS id,
            commits.cmt_author_timestamp AS created_at,
            commits.repo_id,
            'commit'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.commits
             LEFT JOIN augur_data.contributors ON (((contributors.cntrb_id)::text = (commits.cmt_ght_author_id)::text)))
          GROUP BY commits.cmt_commit_hash, commits.cmt_ght_author_id, commits.repo_id, commits.cmt_author_timestamp, 'commit'::text, contributors.cntrb_login
        UNION ALL
         SELECT issues.reporter_id AS id,
            issues.created_at,
            issues.repo_id,
            'issue_opened'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.issues
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issues.reporter_id)))
          WHERE (issues.pull_request IS NULL)
        UNION ALL
         SELECT pull_request_events.cntrb_id AS id,
            pull_request_events.created_at,
            pull_requests.repo_id,
            'pull_request_closed'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_events.cntrb_id)))
          WHERE ((pull_requests.pull_request_id = pull_request_events.pull_request_id) AND (pull_requests.pr_merged_at IS NULL) AND ((pull_request_events.action)::text = 'closed'::text))
        UNION ALL
         SELECT pull_request_events.cntrb_id AS id,
            pull_request_events.created_at,
            pull_requests.repo_id,
            'pull_request_merged'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_events.cntrb_id)))
          WHERE ((pull_requests.pull_request_id = pull_request_events.pull_request_id) AND ((pull_request_events.action)::text = 'merged'::text))
        UNION ALL
         SELECT issue_events.cntrb_id AS id,
            issue_events.created_at,
            issues.repo_id,
            'issue_closed'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.issues,
            (augur_data.issue_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issue_events.cntrb_id)))
          WHERE ((issues.issue_id = issue_events.issue_id) AND (issues.pull_request IS NULL) AND ((issue_events.action)::text = 'closed'::text))
        UNION ALL
         SELECT pull_request_reviews.cntrb_id AS id,
            pull_request_reviews.pr_review_submitted_at AS created_at,
            pull_requests.repo_id,
            ('pull_request_review_'::text || (pull_request_reviews.pr_review_state)::text) AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_reviews
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_reviews.cntrb_id)))
          WHERE (pull_requests.pull_request_id = pull_request_reviews.pull_request_id)
        UNION ALL
         SELECT pull_requests.pr_augur_contributor_id AS id,
            pull_requests.pr_created_at AS created_at,
            pull_requests.repo_id,
            'pull_request_open'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.pull_requests
             LEFT JOIN augur_data.contributors ON ((pull_requests.pr_augur_contributor_id = contributors.cntrb_id)))
        UNION ALL
         SELECT message.cntrb_id AS id,
            message.msg_timestamp AS created_at,
            pull_requests.repo_id,
            'pull_request_comment'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            augur_data.pull_request_message_ref,
            (augur_data.message
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
          WHERE ((pull_request_message_ref.pull_request_id = pull_requests.pull_request_id) AND (pull_request_message_ref.msg_id = message.msg_id))
        UNION ALL
         SELECT issues.reporter_id AS id,
            message.msg_timestamp AS created_at,
            issues.repo_id,
            'issue_comment'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.issues,
            augur_data.issue_message_ref,
            (augur_data.message
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
          WHERE ((issue_message_ref.msg_id = message.msg_id) AND (issues.issue_id = issue_message_ref.issue_id) AND (issues.closed_at <> message.msg_timestamp))) a,
    augur_data.repo
  WHERE (a.repo_id = repo.repo_id)
  ORDER BY a.created_at DESC
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.augur_new_contributors OWNER TO augur;

--
-- Name: chaoss_metric_status_cms_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.chaoss_metric_status_cms_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.chaoss_metric_status_cms_id_seq OWNER TO augur;

--
-- Name: chaoss_metric_status; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.chaoss_metric_status (
    cms_id bigint DEFAULT nextval('augur_data.chaoss_metric_status_cms_id_seq'::regclass) NOT NULL,
    cm_group character varying,
    cm_source character varying,
    cm_type character varying,
    cm_backend_status character varying,
    cm_frontend_status character varying,
    cm_defined boolean,
    cm_api_endpoint_repo character varying,
    cm_api_endpoint_rg character varying,
    cm_name character varying,
    cm_working_group character varying,
    cm_info json,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cm_working_group_focus_area character varying
);


ALTER TABLE augur_data.chaoss_metric_status OWNER TO augur;

--
-- Name: TABLE chaoss_metric_status; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.chaoss_metric_status IS 'This table used to track CHAOSS Metric implementations in Augur, but due to the constantly changing location of that information, it is for the moment not actively populated. ';


--
-- Name: chaoss_user; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.chaoss_user (
    chaoss_id bigint NOT NULL,
    chaoss_login_name character varying,
    chaoss_login_hashword character varying,
    chaoss_email character varying,
    chaoss_text_phone character varying,
    chaoss_first_name character varying,
    chaoss_last_name character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(6) with time zone DEFAULT now()
);


ALTER TABLE augur_data.chaoss_user OWNER TO augur;

--
-- Name: chaoss_user_chaoss_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.chaoss_user_chaoss_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.chaoss_user_chaoss_id_seq OWNER TO augur;

--
-- Name: chaoss_user_chaoss_id_seq; Type: SEQUENCE OWNED BY; Schema: augur_data; Owner: augur
--

ALTER SEQUENCE augur_data.chaoss_user_chaoss_id_seq OWNED BY augur_data.chaoss_user.chaoss_id;


--
-- Name: commit_comment_ref_cmt_comment_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.commit_comment_ref_cmt_comment_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.commit_comment_ref_cmt_comment_id_seq OWNER TO augur;

--
-- Name: commit_comment_ref; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.commit_comment_ref (
    cmt_comment_id bigint DEFAULT nextval('augur_data.commit_comment_ref_cmt_comment_id_seq'::regclass) NOT NULL,
    cmt_id bigint NOT NULL,
    repo_id bigint,
    msg_id bigint NOT NULL,
    user_id bigint NOT NULL,
    body text,
    line bigint,
    "position" bigint,
    commit_comment_src_node_id character varying,
    cmt_comment_src_id bigint NOT NULL,
    created_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.commit_comment_ref OWNER TO augur;

--
-- Name: COLUMN commit_comment_ref.commit_comment_src_node_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.commit_comment_ref.commit_comment_src_node_id IS 'For data provenance, we store the source node ID if it exists. ';


--
-- Name: COLUMN commit_comment_ref.cmt_comment_src_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.commit_comment_ref.cmt_comment_src_id IS 'For data provenance, we store the source ID if it exists. ';


--
-- Name: commit_parents_parent_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.commit_parents_parent_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.commit_parents_parent_id_seq OWNER TO augur;

--
-- Name: commit_parents; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.commit_parents (
    cmt_id bigint NOT NULL,
    parent_id bigint DEFAULT nextval('augur_data.commit_parents_parent_id_seq'::regclass) NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.commit_parents OWNER TO augur;

--
-- Name: contributor_affiliations_ca_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.contributor_affiliations_ca_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.contributor_affiliations_ca_id_seq OWNER TO augur;

--
-- Name: contributor_affiliations; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.contributor_affiliations (
    ca_id bigint DEFAULT nextval('augur_data.contributor_affiliations_ca_id_seq'::regclass) NOT NULL,
    ca_domain character varying(64) NOT NULL,
    ca_start_date date DEFAULT '1970-01-01'::date,
    ca_last_used timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ca_affiliation character varying,
    ca_active smallint DEFAULT 1,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.contributor_affiliations OWNER TO augur;

--
-- Name: TABLE contributor_affiliations; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.contributor_affiliations IS 'This table exists outside of relations with other tables. The purpose is to provide a dynamic, owner maintained (and augur augmented) list of affiliations. This table is processed in affiliation information in the DM_ tables generated when Augur is finished counting commits using the Facade Worker. ';


--
-- Name: contributor_repo_cntrb_repo_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.contributor_repo_cntrb_repo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.contributor_repo_cntrb_repo_id_seq OWNER TO augur;

--
-- Name: contributor_repo; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.contributor_repo (
    cntrb_repo_id bigint DEFAULT nextval('augur_data.contributor_repo_cntrb_repo_id_seq'::regclass) NOT NULL,
    repo_git character varying NOT NULL,
    repo_name character varying NOT NULL,
    gh_repo_id bigint NOT NULL,
    cntrb_category character varying,
    event_id bigint,
    created_at timestamp(0) without time zone,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid NOT NULL
);


ALTER TABLE augur_data.contributor_repo OWNER TO augur;

--
-- Name: TABLE contributor_repo; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.contributor_repo IS 'Developed in Partnership with Andrew Brain. 
From: [
  {
    "login": "octocat",
    "id": 1,
    "node_id": "MDQ6VXNlcjE=",
    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
    "gravatar_id": "",
    "url": "https://api.github.com/users/octocat",
    "html_url": "https://github.com/octocat",
    "followers_url": "https://api.github.com/users/octocat/followers",
    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
    "organizations_url": "https://api.github.com/users/octocat/orgs",
    "repos_url": "https://api.github.com/users/octocat/repos",
    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
    "received_events_url": "https://api.github.com/users/octocat/received_events",
    "type": "User",
    "site_admin": false
  }
]
';


--
-- Name: COLUMN contributor_repo.repo_git; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributor_repo.repo_git IS 'Similar to cntrb_id, we need this data for the table to have meaningful data. ';


--
-- Name: COLUMN contributor_repo.cntrb_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.contributor_repo.cntrb_id IS 'This is not null because what is the point without the contributor in this table? ';


--
-- Name: contributors_aliases_cntrb_alias_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.contributors_aliases_cntrb_alias_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.contributors_aliases_cntrb_alias_id_seq OWNER TO augur;

--
-- Name: contributors_aliases; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.contributors_aliases (
    cntrb_alias_id bigint DEFAULT nextval('augur_data.contributors_aliases_cntrb_alias_id_seq'::regclass) NOT NULL,
    canonical_email character varying NOT NULL,
    alias_email character varying NOT NULL,
    cntrb_active smallint DEFAULT 1 NOT NULL,
    cntrb_last_modified timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid NOT NULL
);


ALTER TABLE augur_data.contributors_aliases OWNER TO augur;

--
-- Name: TABLE contributors_aliases; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.contributors_aliases IS 'Every open source user may have more than one email used to make contributions over time. Augur selects the first email it encounters for a user as its “canonical_email”. 

The canonical_email is also added to the contributors_aliases table, with the canonical_email and alias_email being identical.  Using this strategy, an email search will only need to join the alias table for basic email information, and can then more easily map the canonical email from each alias row to the same, more detailed information in the contributors table for a user. ';


--
-- Name: contributors_aliases_cntrb_a_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.contributors_aliases_cntrb_a_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.contributors_aliases_cntrb_a_id_seq OWNER TO augur;

--
-- Name: contributors_cntrb_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.contributors_cntrb_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.contributors_cntrb_id_seq OWNER TO augur;

--
-- Name: contributors_history_cntrb_history_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.contributors_history_cntrb_history_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.contributors_history_cntrb_history_id_seq OWNER TO augur;


--
-- Name: discourse_insights_msg_discourse_id_seq1; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.discourse_insights_msg_discourse_id_seq1
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.discourse_insights_msg_discourse_id_seq1 OWNER TO augur;

--
-- Name: discourse_insights; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.discourse_insights (
    msg_discourse_id bigint DEFAULT nextval('augur_data.discourse_insights_msg_discourse_id_seq1'::regclass) NOT NULL,
    msg_id bigint,
    discourse_act character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(6) with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.discourse_insights OWNER TO augur;

--
-- Name: TABLE discourse_insights; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.discourse_insights IS 'This table is populated by the “Discourse_Analysis_Worker”. It examines sequential discourse, using computational linguistic methods, to draw statistical inferences regarding the discourse in a particular comment thread. ';


--
-- Name: discourse_insights_msg_discourse_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.discourse_insights_msg_discourse_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.discourse_insights_msg_discourse_id_seq OWNER TO augur;

--
-- Name: dm_repo_annual; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.dm_repo_annual (
    repo_id bigint NOT NULL,
    email character varying NOT NULL,
    affiliation character varying DEFAULT 'NULL'::character varying,
    year smallint NOT NULL,
    added bigint NOT NULL,
    removed bigint NOT NULL,
    whitespace bigint NOT NULL,
    files bigint NOT NULL,
    patches bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.dm_repo_annual OWNER TO augur;

--
-- Name: dm_repo_group_annual; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.dm_repo_group_annual (
    repo_group_id bigint NOT NULL,
    email character varying NOT NULL,
    affiliation character varying DEFAULT 'NULL'::character varying,
    year smallint NOT NULL,
    added bigint NOT NULL,
    removed bigint NOT NULL,
    whitespace bigint NOT NULL,
    files bigint NOT NULL,
    patches bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.dm_repo_group_annual OWNER TO augur;

--
-- Name: dm_repo_group_monthly; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.dm_repo_group_monthly (
    repo_group_id bigint NOT NULL,
    email character varying NOT NULL,
    affiliation character varying DEFAULT 'NULL'::character varying,
    month smallint NOT NULL,
    year smallint NOT NULL,
    added bigint NOT NULL,
    removed bigint NOT NULL,
    whitespace bigint NOT NULL,
    files bigint NOT NULL,
    patches bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.dm_repo_group_monthly OWNER TO augur;

--
-- Name: dm_repo_group_weekly; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.dm_repo_group_weekly (
    repo_group_id bigint NOT NULL,
    email character varying NOT NULL,
    affiliation character varying DEFAULT 'NULL'::character varying,
    week smallint NOT NULL,
    year smallint NOT NULL,
    added bigint NOT NULL,
    removed bigint NOT NULL,
    whitespace bigint NOT NULL,
    files bigint NOT NULL,
    patches bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.dm_repo_group_weekly OWNER TO augur;

--
-- Name: dm_repo_monthly; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.dm_repo_monthly (
    repo_id bigint NOT NULL,
    email character varying NOT NULL,
    affiliation character varying DEFAULT 'NULL'::character varying,
    month smallint NOT NULL,
    year smallint NOT NULL,
    added bigint NOT NULL,
    removed bigint NOT NULL,
    whitespace bigint NOT NULL,
    files bigint NOT NULL,
    patches bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.dm_repo_monthly OWNER TO augur;

--
-- Name: dm_repo_weekly; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.dm_repo_weekly (
    repo_id bigint NOT NULL,
    email character varying NOT NULL,
    affiliation character varying DEFAULT 'NULL'::character varying,
    week smallint NOT NULL,
    year smallint NOT NULL,
    added bigint NOT NULL,
    removed bigint NOT NULL,
    whitespace bigint NOT NULL,
    files bigint NOT NULL,
    patches bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.dm_repo_weekly OWNER TO augur;

--
-- Name: exclude; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.exclude (
    id integer NOT NULL,
    projects_id integer NOT NULL,
    email character varying DEFAULT 'NULL'::character varying,
    domain character varying DEFAULT 'NULL'::character varying
);


ALTER TABLE augur_data.exclude OWNER TO augur;

--
-- Name: explorer_commits_and_committers_daily_count; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_commits_and_committers_daily_count AS
 SELECT repo.repo_id,
    repo.repo_name,
    commits.cmt_committer_date,
    count(commits.cmt_id) AS num_of_commits,
    count(DISTINCT commits.cmt_committer_raw_email) AS num_of_unique_committers
   FROM (augur_data.commits
     LEFT JOIN augur_data.repo ON ((repo.repo_id = commits.repo_id)))
  GROUP BY repo.repo_id, repo.repo_name, commits.cmt_committer_date
  ORDER BY repo.repo_id, commits.cmt_committer_date
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_commits_and_committers_daily_count OWNER TO augur;

--
-- Name: explorer_contributor_actions; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_contributor_actions AS
 SELECT a.id AS cntrb_id,
    a.created_at,
    a.repo_id,
    a.action,
    repo.repo_name,
    a.login,
    row_number() OVER (PARTITION BY a.id, a.repo_id ORDER BY a.created_at DESC) AS rank
   FROM ( SELECT commits.cmt_ght_author_id AS id,
            commits.cmt_author_timestamp AS created_at,
            commits.repo_id,
            'commit'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.commits
             LEFT JOIN augur_data.contributors ON (((contributors.cntrb_id)::text = (commits.cmt_ght_author_id)::text)))
          GROUP BY commits.cmt_commit_hash, commits.cmt_ght_author_id, commits.repo_id, commits.cmt_author_timestamp, 'commit'::text, contributors.cntrb_login
        UNION ALL
         SELECT issues.reporter_id AS id,
            issues.created_at,
            issues.repo_id,
            'issue_opened'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.issues
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issues.reporter_id)))
          WHERE (issues.pull_request IS NULL)
        UNION ALL
         SELECT pull_request_events.cntrb_id AS id,
            pull_request_events.created_at,
            pull_requests.repo_id,
            'pull_request_closed'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_events.cntrb_id)))
          WHERE ((pull_requests.pull_request_id = pull_request_events.pull_request_id) AND (pull_requests.pr_merged_at IS NULL) AND ((pull_request_events.action)::text = 'closed'::text))
        UNION ALL
         SELECT pull_request_events.cntrb_id AS id,
            pull_request_events.created_at,
            pull_requests.repo_id,
            'pull_request_merged'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_events.cntrb_id)))
          WHERE ((pull_requests.pull_request_id = pull_request_events.pull_request_id) AND ((pull_request_events.action)::text = 'merged'::text))
        UNION ALL
         SELECT issue_events.cntrb_id AS id,
            issue_events.created_at,
            issues.repo_id,
            'issue_closed'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.issues,
            (augur_data.issue_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issue_events.cntrb_id)))
          WHERE ((issues.issue_id = issue_events.issue_id) AND (issues.pull_request IS NULL) AND ((issue_events.action)::text = 'closed'::text))
        UNION ALL
         SELECT pull_request_reviews.cntrb_id AS id,
            pull_request_reviews.pr_review_submitted_at AS created_at,
            pull_requests.repo_id,
            ('pull_request_review_'::text || (pull_request_reviews.pr_review_state)::text) AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_reviews
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_reviews.cntrb_id)))
          WHERE (pull_requests.pull_request_id = pull_request_reviews.pull_request_id)
        UNION ALL
         SELECT pull_requests.pr_augur_contributor_id AS id,
            pull_requests.pr_created_at AS created_at,
            pull_requests.repo_id,
            'pull_request_open'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.pull_requests
             LEFT JOIN augur_data.contributors ON ((pull_requests.pr_augur_contributor_id = contributors.cntrb_id)))
        UNION ALL
         SELECT message.cntrb_id AS id,
            message.msg_timestamp AS created_at,
            pull_requests.repo_id,
            'pull_request_comment'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            augur_data.pull_request_message_ref,
            (augur_data.message
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
          WHERE ((pull_request_message_ref.pull_request_id = pull_requests.pull_request_id) AND (pull_request_message_ref.msg_id = message.msg_id))
        UNION ALL
         SELECT issues.reporter_id AS id,
            message.msg_timestamp AS created_at,
            issues.repo_id,
            'issue_comment'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.issues,
            augur_data.issue_message_ref,
            (augur_data.message
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
          WHERE ((issue_message_ref.msg_id = message.msg_id) AND (issues.issue_id = issue_message_ref.issue_id) AND (issues.closed_at <> message.msg_timestamp))) a,
    augur_data.repo
  WHERE (a.repo_id = repo.repo_id)
  ORDER BY a.created_at DESC
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_contributor_actions OWNER TO augur;

--
-- Name: repo_groups_repo_group_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_groups_repo_group_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_groups_repo_group_id_seq OWNER TO augur;

--
-- Name: repo_groups; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_groups (
    repo_group_id bigint DEFAULT nextval('augur_data.repo_groups_repo_group_id_seq'::regclass) NOT NULL,
    rg_name character varying NOT NULL,
    rg_description character varying DEFAULT 'NULL'::character varying,
    rg_website character varying(128) DEFAULT 'NULL'::character varying,
    rg_recache smallint DEFAULT 1,
    rg_last_modified timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    rg_type character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.repo_groups OWNER TO augur;

--
-- Name: TABLE repo_groups; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_groups IS 'rg_type is intended to be either a GitHub Organization or a User Created Repo Group. ';


--
-- Name: explorer_entry_list; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_entry_list AS
 SELECT DISTINCT r.repo_git,
    r.repo_id,
    r.repo_name,
    rg.rg_name
   FROM (augur_data.repo r
     JOIN augur_data.repo_groups rg ON ((rg.repo_group_id = r.repo_group_id)))
  ORDER BY rg.rg_name
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_entry_list OWNER TO augur;

--
-- Name: explorer_issue_assignments; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_issue_assignments AS
 SELECT i.issue_id,
    i.repo_id AS id,
    i.created_at AS created,
    i.closed_at AS closed,
    ie.created_at AS assign_date,
    ie.action AS assignment_action,
    ie.cntrb_id AS assignee,
    ie.node_id
   FROM (augur_data.issues i
     LEFT JOIN augur_data.issue_events ie ON (((i.issue_id = ie.issue_id) AND ((ie.action)::text = ANY (ARRAY[('unassigned'::character varying)::text, ('assigned'::character varying)::text])))))
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_issue_assignments OWNER TO augur;

--
-- Name: explorer_new_contributors; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_new_contributors AS
 SELECT cntrb_id,
    created_at,
    month,
    year,
    repo_id,
    repo_name,
    full_name,
    login,
    rank
   FROM ( SELECT b.cntrb_id,
            b.created_at,
            b.month,
            b.year,
            b.repo_id,
            b.repo_name,
            b.full_name,
            b.login,
            b.action,
            b.rank
           FROM ( SELECT a.id AS cntrb_id,
                    a.created_at,
                    date_part('month'::text, (a.created_at)::date) AS month,
                    date_part('year'::text, (a.created_at)::date) AS year,
                    a.repo_id,
                    repo.repo_name,
                    a.full_name,
                    a.login,
                    a.action,
                    row_number() OVER (PARTITION BY a.id, a.repo_id ORDER BY a.created_at DESC) AS rank
                   FROM ( SELECT canonical_full_names.canonical_id AS id,
                            issues.created_at,
                            issues.repo_id,
                            'issue_opened'::text AS action,
                            contributors.cntrb_full_name AS full_name,
                            contributors.cntrb_login AS login
                           FROM ((augur_data.issues
                             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issues.reporter_id)))
                             LEFT JOIN ( SELECT DISTINCT ON (contributors_1.cntrb_canonical) contributors_1.cntrb_full_name,
                                    contributors_1.cntrb_canonical AS canonical_email,
                                    contributors_1.data_collection_date,
                                    contributors_1.cntrb_id AS canonical_id
                                   FROM augur_data.contributors contributors_1
                                  WHERE ((contributors_1.cntrb_canonical)::text = (contributors_1.cntrb_email)::text)
                                  ORDER BY contributors_1.cntrb_canonical) canonical_full_names ON (((canonical_full_names.canonical_email)::text = (contributors.cntrb_canonical)::text)))
                          WHERE (issues.pull_request IS NULL)
                          GROUP BY canonical_full_names.canonical_id, issues.repo_id, issues.created_at, contributors.cntrb_full_name, contributors.cntrb_login
                        UNION ALL
                         SELECT canonical_full_names.canonical_id AS id,
                            to_timestamp((commits.cmt_author_date)::text, 'YYYY-MM-DD'::text) AS created_at,
                            commits.repo_id,
                            'commit'::text AS action,
                            contributors.cntrb_full_name AS full_name,
                            contributors.cntrb_login AS login
                           FROM ((augur_data.commits
                             LEFT JOIN augur_data.contributors ON (((contributors.cntrb_canonical)::text = (commits.cmt_author_email)::text)))
                             LEFT JOIN ( SELECT DISTINCT ON (contributors_1.cntrb_canonical) contributors_1.cntrb_full_name,
                                    contributors_1.cntrb_canonical AS canonical_email,
                                    contributors_1.data_collection_date,
                                    contributors_1.cntrb_id AS canonical_id
                                   FROM augur_data.contributors contributors_1
                                  WHERE ((contributors_1.cntrb_canonical)::text = (contributors_1.cntrb_email)::text)
                                  ORDER BY contributors_1.cntrb_canonical) canonical_full_names ON (((canonical_full_names.canonical_email)::text = (contributors.cntrb_canonical)::text)))
                          GROUP BY commits.repo_id, canonical_full_names.canonical_email, canonical_full_names.canonical_id, commits.cmt_author_date, contributors.cntrb_full_name, contributors.cntrb_login
                        UNION ALL
                         SELECT message.cntrb_id AS id,
                            commit_comment_ref.created_at,
                            commits.repo_id,
                            'commit_comment'::text AS action,
                            contributors.cntrb_full_name AS full_name,
                            contributors.cntrb_login AS login
                           FROM augur_data.commit_comment_ref,
                            augur_data.commits,
                            ((augur_data.message
                             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
                             LEFT JOIN ( SELECT DISTINCT ON (contributors_1.cntrb_canonical) contributors_1.cntrb_full_name,
                                    contributors_1.cntrb_canonical AS canonical_email,
                                    contributors_1.data_collection_date,
                                    contributors_1.cntrb_id AS canonical_id
                                   FROM augur_data.contributors contributors_1
                                  WHERE ((contributors_1.cntrb_canonical)::text = (contributors_1.cntrb_email)::text)
                                  ORDER BY contributors_1.cntrb_canonical) canonical_full_names ON (((canonical_full_names.canonical_email)::text = (contributors.cntrb_canonical)::text)))
                          WHERE ((commits.cmt_id = commit_comment_ref.cmt_id) AND (commit_comment_ref.msg_id = message.msg_id))
                          GROUP BY message.cntrb_id, commits.repo_id, commit_comment_ref.created_at, contributors.cntrb_full_name, contributors.cntrb_login
                        UNION ALL
                         SELECT issue_events.cntrb_id AS id,
                            issue_events.created_at,
                            issues.repo_id,
                            'issue_closed'::text AS action,
                            contributors.cntrb_full_name AS full_name,
                            contributors.cntrb_login AS login
                           FROM augur_data.issues,
                            ((augur_data.issue_events
                             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issue_events.cntrb_id)))
                             LEFT JOIN ( SELECT DISTINCT ON (contributors_1.cntrb_canonical) contributors_1.cntrb_full_name,
                                    contributors_1.cntrb_canonical AS canonical_email,
                                    contributors_1.data_collection_date,
                                    contributors_1.cntrb_id AS canonical_id
                                   FROM augur_data.contributors contributors_1
                                  WHERE ((contributors_1.cntrb_canonical)::text = (contributors_1.cntrb_email)::text)
                                  ORDER BY contributors_1.cntrb_canonical) canonical_full_names ON (((canonical_full_names.canonical_email)::text = (contributors.cntrb_canonical)::text)))
                          WHERE ((issues.issue_id = issue_events.issue_id) AND (issues.pull_request IS NULL) AND (issue_events.cntrb_id IS NOT NULL) AND ((issue_events.action)::text = 'closed'::text))
                          GROUP BY issue_events.cntrb_id, issues.repo_id, issue_events.created_at, contributors.cntrb_full_name, contributors.cntrb_login
                        UNION ALL
                         SELECT pull_requests.pr_augur_contributor_id AS id,
                            pull_requests.pr_created_at AS created_at,
                            pull_requests.repo_id,
                            'open_pull_request'::text AS action,
                            contributors.cntrb_full_name AS full_name,
                            contributors.cntrb_login AS login
                           FROM ((augur_data.pull_requests
                             LEFT JOIN augur_data.contributors ON ((pull_requests.pr_augur_contributor_id = contributors.cntrb_id)))
                             LEFT JOIN ( SELECT DISTINCT ON (contributors_1.cntrb_canonical) contributors_1.cntrb_full_name,
                                    contributors_1.cntrb_canonical AS canonical_email,
                                    contributors_1.data_collection_date,
                                    contributors_1.cntrb_id AS canonical_id
                                   FROM augur_data.contributors contributors_1
                                  WHERE ((contributors_1.cntrb_canonical)::text = (contributors_1.cntrb_email)::text)
                                  ORDER BY contributors_1.cntrb_canonical) canonical_full_names ON (((canonical_full_names.canonical_email)::text = (contributors.cntrb_canonical)::text)))
                          GROUP BY pull_requests.pr_augur_contributor_id, pull_requests.repo_id, pull_requests.pr_created_at, contributors.cntrb_full_name, contributors.cntrb_login
                        UNION ALL
                         SELECT message.cntrb_id AS id,
                            message.msg_timestamp AS created_at,
                            pull_requests.repo_id,
                            'pull_request_comment'::text AS action,
                            contributors.cntrb_full_name AS full_name,
                            contributors.cntrb_login AS login
                           FROM augur_data.pull_requests,
                            augur_data.pull_request_message_ref,
                            ((augur_data.message
                             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
                             LEFT JOIN ( SELECT DISTINCT ON (contributors_1.cntrb_canonical) contributors_1.cntrb_full_name,
                                    contributors_1.cntrb_canonical AS canonical_email,
                                    contributors_1.data_collection_date,
                                    contributors_1.cntrb_id AS canonical_id
                                   FROM augur_data.contributors contributors_1
                                  WHERE ((contributors_1.cntrb_canonical)::text = (contributors_1.cntrb_email)::text)
                                  ORDER BY contributors_1.cntrb_canonical) canonical_full_names ON (((canonical_full_names.canonical_email)::text = (contributors.cntrb_canonical)::text)))
                          WHERE ((pull_request_message_ref.pull_request_id = pull_requests.pull_request_id) AND (pull_request_message_ref.msg_id = message.msg_id))
                          GROUP BY message.cntrb_id, pull_requests.repo_id, message.msg_timestamp, contributors.cntrb_full_name, contributors.cntrb_login
                        UNION ALL
                         SELECT issues.reporter_id AS id,
                            message.msg_timestamp AS created_at,
                            issues.repo_id,
                            'issue_comment'::text AS action,
                            contributors.cntrb_full_name AS full_name,
                            contributors.cntrb_login AS login
                           FROM augur_data.issues,
                            augur_data.issue_message_ref,
                            ((augur_data.message
                             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
                             LEFT JOIN ( SELECT DISTINCT ON (contributors_1.cntrb_canonical) contributors_1.cntrb_full_name,
                                    contributors_1.cntrb_canonical AS canonical_email,
                                    contributors_1.data_collection_date,
                                    contributors_1.cntrb_id AS canonical_id
                                   FROM augur_data.contributors contributors_1
                                  WHERE ((contributors_1.cntrb_canonical)::text = (contributors_1.cntrb_email)::text)
                                  ORDER BY contributors_1.cntrb_canonical) canonical_full_names ON (((canonical_full_names.canonical_email)::text = (contributors.cntrb_canonical)::text)))
                          WHERE ((issue_message_ref.msg_id = message.msg_id) AND (issues.issue_id = issue_message_ref.issue_id) AND (issues.pull_request_id = NULL::bigint))
                          GROUP BY issues.reporter_id, issues.repo_id, message.msg_timestamp, contributors.cntrb_full_name, contributors.cntrb_login) a,
                    augur_data.repo
                  WHERE ((a.id IS NOT NULL) AND (a.repo_id = repo.repo_id))
                  GROUP BY a.id, a.repo_id, a.action, a.created_at, repo.repo_name, a.full_name, a.login
                  ORDER BY a.id) b
          WHERE (b.rank = ANY (ARRAY[(1)::bigint, (2)::bigint, (3)::bigint, (4)::bigint, (5)::bigint, (6)::bigint, (7)::bigint]))) x
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_new_contributors OWNER TO augur;

--
-- Name: explorer_pr_assignments; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_pr_assignments AS
 SELECT pr.pull_request_id,
    pr.repo_id AS id,
    pr.pr_created_at AS created,
    pr.pr_closed_at AS closed,
    pre.created_at AS assign_date,
    pre.action AS assignment_action,
    pre.cntrb_id AS assignee,
    pre.node_id
   FROM (augur_data.pull_requests pr
     LEFT JOIN augur_data.pull_request_events pre ON (((pr.pull_request_id = pre.pull_request_id) AND ((pre.action)::text = ANY (ARRAY[('unassigned'::character varying)::text, ('assigned'::character varying)::text])))))
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_pr_assignments OWNER TO augur;

--
-- Name: pull_request_review_message_ref_pr_review_msg_ref_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_review_message_ref_pr_review_msg_ref_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_review_message_ref_pr_review_msg_ref_id_seq OWNER TO augur;

--
-- Name: pull_request_review_message_ref; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_review_message_ref (
    pr_review_msg_ref_id bigint DEFAULT nextval('augur_data.pull_request_review_message_ref_pr_review_msg_ref_id_seq'::regclass) NOT NULL,
    pr_review_id bigint NOT NULL,
    repo_id bigint,
    msg_id bigint NOT NULL,
    pr_review_msg_url character varying,
    pr_review_src_id bigint,
    pr_review_msg_src_id bigint,
    pr_review_msg_node_id character varying,
    pr_review_msg_diff_hunk character varying,
    pr_review_msg_path character varying,
    pr_review_msg_position bigint,
    pr_review_msg_original_position bigint,
    pr_review_msg_commit_id character varying,
    pr_review_msg_original_commit_id character varying,
    pr_review_msg_updated_at timestamp(6) without time zone,
    pr_review_msg_html_url character varying,
    pr_url character varying,
    pr_review_msg_author_association character varying,
    pr_review_msg_start_line bigint,
    pr_review_msg_original_start_line bigint,
    pr_review_msg_start_side character varying,
    pr_review_msg_line bigint,
    pr_review_msg_original_line bigint,
    pr_review_msg_side character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.pull_request_review_message_ref OWNER TO augur;

--
-- Name: explorer_pr_response; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_pr_response AS
 SELECT pr.pull_request_id,
    pr.repo_id AS id,
    pr.pr_augur_contributor_id AS cntrb_id,
    m.msg_timestamp,
    m.msg_cntrb_id,
    pr.pr_created_at,
    pr.pr_closed_at
   FROM (augur_data.pull_requests pr
     LEFT JOIN ( SELECT prr.pull_request_id,
            m_1.msg_timestamp,
            m_1.cntrb_id AS msg_cntrb_id
           FROM augur_data.pull_request_review_message_ref prrmr,
            augur_data.pull_requests pr_1,
            augur_data.message m_1,
            augur_data.pull_request_reviews prr
          WHERE ((prrmr.pr_review_id = prr.pr_review_id) AND (prrmr.msg_id = m_1.msg_id) AND (prr.pull_request_id = pr_1.pull_request_id))
        UNION
         SELECT prmr.pull_request_id,
            m_1.msg_timestamp,
            m_1.cntrb_id AS msg_cntrb_id
           FROM augur_data.pull_request_message_ref prmr,
            augur_data.pull_requests pr_1,
            augur_data.message m_1
          WHERE ((prmr.pull_request_id = pr_1.pull_request_id) AND (prmr.msg_id = m_1.msg_id))) m ON ((m.pull_request_id = pr.pull_request_id)))
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_pr_response OWNER TO augur;

--
-- Name: pull_request_commits_pr_cmt_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_commits_pr_cmt_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_commits_pr_cmt_id_seq OWNER TO augur;

--
-- Name: pull_request_commits; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_commits (
    pr_cmt_id bigint DEFAULT nextval('augur_data.pull_request_commits_pr_cmt_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    repo_id bigint,
    pr_cmt_sha character varying,
    pr_cmt_node_id character varying,
    pr_cmt_message character varying,
    pr_cmt_comments_url character varying,
    pr_cmt_timestamp timestamp(0) without time zone,
    pr_cmt_author_email character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    pr_cmt_author_cntrb_id uuid
);


ALTER TABLE augur_data.pull_request_commits OWNER TO augur;

--
-- Name: TABLE pull_request_commits; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.pull_request_commits IS 'Pull request commits are an enumeration of each commit associated with a pull request. 
Not all pull requests are from a branch or fork into master. 
The commits table intends to count only commits that end up in the master branch (i.e., part of the deployed code base for a project).
Therefore, there will be commit “SHA”’s in this table that are no associated with a commit SHA in the commits table. 
In cases where the PR is to the master branch of a project, you will find a match. In cases where the PR does not involve the master branch, you will not find a corresponding commit SHA in the commits table. This is expected. ';


--
-- Name: COLUMN pull_request_commits.pr_cmt_sha; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_commits.pr_cmt_sha IS 'This is the commit SHA for a pull request commit. If the PR is not to the master branch of the main repository (or, in rare cases, from it), then you will NOT find a corresponding commit SHA in the commit table. (see table comment for further explanation). ';


--
-- Name: pull_request_meta_pr_repo_meta_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_meta_pr_repo_meta_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_meta_pr_repo_meta_id_seq OWNER TO augur;

--
-- Name: pull_request_meta; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_meta (
    pr_repo_meta_id bigint DEFAULT nextval('augur_data.pull_request_meta_pr_repo_meta_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    repo_id bigint,
    pr_head_or_base character varying,
    pr_src_meta_label character varying,
    pr_src_meta_ref character varying,
    pr_sha character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid
);


ALTER TABLE augur_data.pull_request_meta OWNER TO augur;

--
-- Name: TABLE pull_request_meta; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.pull_request_meta IS 'Pull requests contain referencing metadata.  There are a few columns that are discrete. There are also head and base designations for the repo on each side of the pull request. Similar functions exist in GitLab, though the language here is based on GitHub. The JSON Being adapted to as of the development of this schema is here:      "base": {       "label": "chaoss:dev",       "ref": "dev",       "sha": "dc6c6f3947f7dc84ecba3d8bda641ef786e7027d",       "user": {         "login": "chaoss",         "id": 29740296,         "node_id": "MDEyOk9yZ2FuaXphdGlvbjI5NzQwMjk2",         "avatar_url": "https://avatars2.githubusercontent.com/u/29740296?v=4",         "gravatar_id": "",         "url": "https://api.github.com/users/chaoss",         "html_url": "https://github.com/chaoss",         "followers_url": "https://api.github.com/users/chaoss/followers",         "following_url": "https://api.github.com/users/chaoss/following{/other_user}",         "gists_url": "https://api.github.com/users/chaoss/gists{/gist_id}",         "starred_url": "https://api.github.com/users/chaoss/starred{/owner}{/repo}",         "subscriptions_url": "https://api.github.com/users/chaoss/subscriptions",         "organizations_url": "https://api.github.com/users/chaoss/orgs",         "repos_url": "https://api.github.com/users/chaoss/repos",         "events_url": "https://api.github.com/users/chaoss/events{/privacy}",         "received_events_url": "https://api.github.com/users/chaoss/received_events",         "type": "Organization",         "site_admin": false       },       "repo": {         "id": 78134122,         "node_id": "MDEwOlJlcG9zaXRvcnk3ODEzNDEyMg==",         "name": "augur",         "full_name": "chaoss/augur",         "private": false,         "owner": {           "login": "chaoss",           "id": 29740296,           "node_id": "MDEyOk9yZ2FuaXphdGlvbjI5NzQwMjk2",           "avatar_url": "https://avatars2.githubusercontent.com/u/29740296?v=4",           "gravatar_id": "",           "url": "https://api.github.com/users/chaoss",           "html_url": "https://github.com/chaoss",           "followers_url": "https://api.github.com/users/chaoss/followers",           "following_url": "https://api.github.com/users/chaoss/following{/other_user}",           "gists_url": "https://api.github.com/users/chaoss/gists{/gist_id}",           "starred_url": "https://api.github.com/users/chaoss/starred{/owner}{/repo}",           "subscriptions_url": "https://api.github.com/users/chaoss/subscriptions",           "organizations_url": "https://api.github.com/users/chaoss/orgs",           "repos_url": "https://api.github.com/users/chaoss/repos",           "events_url": "https://api.github.com/users/chaoss/events{/privacy}",           "received_events_url": "https://api.github.com/users/chaoss/received_events",           "type": "Organization",           "site_admin": false         }, ';


--
-- Name: COLUMN pull_request_meta.pr_head_or_base; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_meta.pr_head_or_base IS 'Each pull request should have one and only one head record; and one and only one base record. ';


--
-- Name: COLUMN pull_request_meta.pr_src_meta_label; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_meta.pr_src_meta_label IS 'This is a representation of the repo:branch information in the pull request. Head is issueing the pull request and base is taking the pull request. For example:  (We do not store all of this)

 "head": {
      "label": "chaoss:pull-request-worker",
      "ref": "pull-request-worker",
      "sha": "6b380c3d6d625616f79d702612ebab6d204614f2",
      "user": {
        "login": "chaoss",
        "id": 29740296,
        "node_id": "MDEyOk9yZ2FuaXphdGlvbjI5NzQwMjk2",
        "avatar_url": "https://avatars2.githubusercontent.com/u/29740296?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/chaoss",
        "html_url": "https://github.com/chaoss",
        "followers_url": "https://api.github.com/users/chaoss/followers",
        "following_url": "https://api.github.com/users/chaoss/following{/other_user}",
        "gists_url": "https://api.github.com/users/chaoss/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/chaoss/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/chaoss/subscriptions",
        "organizations_url": "https://api.github.com/users/chaoss/orgs",
        "repos_url": "https://api.github.com/users/chaoss/repos",
        "events_url": "https://api.github.com/users/chaoss/events{/privacy}",
        "received_events_url": "https://api.github.com/users/chaoss/received_events",
        "type": "Organization",
        "site_admin": false
      },
      "repo": {
        "id": 78134122,
        "node_id": "MDEwOlJlcG9zaXRvcnk3ODEzNDEyMg==",
        "name": "augur",
        "full_name": "chaoss/augur",
        "private": false,
        "owner": {
          "login": "chaoss",
          "id": 29740296,
          "node_id": "MDEyOk9yZ2FuaXphdGlvbjI5NzQwMjk2",
          "avatar_url": "https://avatars2.githubusercontent.com/u/29740296?v=4",
          "gravatar_id": "",
          "url": "https://api.github.com/users/chaoss",
          "html_url": "https://github.com/chaoss",
          "followers_url": "https://api.github.com/users/chaoss/followers",
          "following_url": "https://api.github.com/users/chaoss/following{/other_user}",
          "gists_url": "https://api.github.com/users/chaoss/gists{/gist_id}",
          "starred_url": "https://api.github.com/users/chaoss/starred{/owner}{/repo}",
          "subscriptions_url": "https://api.github.com/users/chaoss/subscriptions",
          "organizations_url": "https://api.github.com/users/chaoss/orgs",
          "repos_url": "https://api.github.com/users/chaoss/repos",
          "events_url": "https://api.github.com/users/chaoss/events{/privacy}",
          "received_events_url": "https://api.github.com/users/chaoss/received_events",
          "type": "Organization",
          "site_admin": false
        },
        "html_url": "https://github.com/chaoss/augur",
        "description": "Python library and web service for Open Source Software Health and Sustainability metrics & data collection.",
        "fork": false,
        "url": "https://api.github.com/repos/chaoss/augur",
        "forks_url": "https://api.github.com/repos/chaoss/augur/forks",
        "keys_url": "https://api.github.com/repos/chaoss/augur/keys{/key_id}",
        "collaborators_url": "https://api.github.com/repos/chaoss/augur/collaborators{/collaborator}",
        "teams_url": "https://api.github.com/repos/chaoss/augur/teams",
        "hooks_url": "https://api.github.com/repos/chaoss/augur/hooks",
        "issue_events_url": "https://api.github.com/repos/chaoss/augur/issues/events{/number}",
        "events_url": "https://api.github.com/repos/chaoss/augur/events",
        "assignees_url": "https://api.github.com/repos/chaoss/augur/assignees{/user}",
        "branches_url": "https://api.github.com/repos/chaoss/augur/branches{/branch}",
        "tags_url": "https://api.github.com/repos/chaoss/augur/tags",
        "blobs_url": "https://api.github.com/repos/chaoss/augur/git/blobs{/sha}",
        "git_tags_url": "https://api.github.com/repos/chaoss/augur/git/tags{/sha}",
        "git_refs_url": "https://api.github.com/repos/chaoss/augur/git/refs{/sha}",
        "trees_url": "https://api.github.com/repos/chaoss/augur/git/trees{/sha}",
        "statuses_url": "https://api.github.com/repos/chaoss/augur/statuses/{sha}",
        "languages_url": "https://api.github.com/repos/chaoss/augur/languages",
        "stargazers_url": "https://api.github.com/repos/chaoss/augur/stargazers",
        "contributors_url": "https://api.github.com/repos/chaoss/augur/contributors",
        "subscribers_url": "https://api.github.com/repos/chaoss/augur/subscribers",
        "subscription_url": "https://api.github.com/repos/chaoss/augur/subscription",
        "commits_url": "https://api.github.com/repos/chaoss/augur/commits{/sha}",
        "git_commits_url": "https://api.github.com/repos/chaoss/augur/git/commits{/sha}",
        "comments_url": "https://api.github.com/repos/chaoss/augur/comments{/number}",
        "issue_comment_url": "https://api.github.com/repos/chaoss/augur/issues/comments{/number}",
        "contents_url": "https://api.github.com/repos/chaoss/augur/contents/{+path}",
        "compare_url": "https://api.github.com/repos/chaoss/augur/compare/{base}...{head}",
        "merges_url": "https://api.github.com/repos/chaoss/augur/merges",
        "archive_url": "https://api.github.com/repos/chaoss/augur/{archive_format}{/ref}",
        "downloads_url": "https://api.github.com/repos/chaoss/augur/downloads",
        "issues_url": "https://api.github.com/repos/chaoss/augur/issues{/number}",
        "pulls_url": "https://api.github.com/repos/chaoss/augur/pulls{/number}",
        "milestones_url": "https://api.github.com/repos/chaoss/augur/milestones{/number}",
        "notifications_url": "https://api.github.com/repos/chaoss/augur/notifications{?since,all,participating}",
        "labels_url": "https://api.github.com/repos/chaoss/augur/labels{/name}",
        "releases_url": "https://api.github.com/repos/chaoss/augur/releases{/id}",
        "deployments_url": "https://api.github.com/repos/chaoss/augur/deployments",
        "created_at": "2017-01-05T17:34:54Z",
        "updated_at": "2019-11-15T00:56:12Z",
        "pushed_at": "2019-12-02T06:27:26Z",
        "git_url": "git://github.com/chaoss/augur.git",
        "ssh_url": "git@github.com:chaoss/augur.git",
        "clone_url": "https://github.com/chaoss/augur.git",
        "svn_url": "https://github.com/chaoss/augur",
        "homepage": "http://augur.osshealth.io/",
        "size": 82004,
        "stargazers_count": 153,
        "watchers_count": 153,
        "language": "Python",
        "has_issues": true,
        "has_projects": false,
        "has_downloads": true,
        "has_wiki": false,
        "has_pages": true,
        "forks_count": 205,
        "mirror_url": null,
        "archived": false,
        "disabled": false,
        "open_issues_count": 14,
        "license": {
          "key": "mit",
          "name": "MIT License",
          "spdx_id": "MIT",
          "url": "https://api.github.com/licenses/mit",
          "node_id": "MDc6TGljZW5zZTEz"
        },
        "forks": 205,
        "open_issues": 14,
        "watchers": 153,
        "default_branch": "master"
      }
    },
    "base": {
      "label": "chaoss:dev",
      "ref": "dev",
      "sha": "bfd2d34b51659613dd842cf83c3873f7699c2a0e",
      "user": {
        "login": "chaoss",
        "id": 29740296,
        "node_id": "MDEyOk9yZ2FuaXphdGlvbjI5NzQwMjk2",
        "avatar_url": "https://avatars2.githubusercontent.com/u/29740296?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/chaoss",
        "html_url": "https://github.com/chaoss",
        "followers_url": "https://api.github.com/users/chaoss/followers",
        "following_url": "https://api.github.com/users/chaoss/following{/other_user}",
        "gists_url": "https://api.github.com/users/chaoss/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/chaoss/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/chaoss/subscriptions",
        "organizations_url": "https://api.github.com/users/chaoss/orgs",
        "repos_url": "https://api.github.com/users/chaoss/repos",
        "events_url": "https://api.github.com/users/chaoss/events{/privacy}",
        "received_events_url": "https://api.github.com/users/chaoss/received_events",
        "type": "Organization",
        "site_admin": false
      },
      "repo": {
        "id": 78134122,
        "node_id": "MDEwOlJlcG9zaXRvcnk3ODEzNDEyMg==",
        "name": "augur",
        "full_name": "chaoss/augur",
        "private": false,
        "owner": {
          "login": "chaoss",
          "id": 29740296,
          "node_id": "MDEyOk9yZ2FuaXphdGlvbjI5NzQwMjk2",
          "avatar_url": "https://avatars2.githubusercontent.com/u/29740296?v=4",
          "gravatar_id": "",
          "url": "https://api.github.com/users/chaoss",
          "html_url": "https://github.com/chaoss",
          "followers_url": "https://api.github.com/users/chaoss/followers",
          "following_url": "https://api.github.com/users/chaoss/following{/other_user}",
          "gists_url": "https://api.github.com/users/chaoss/gists{/gist_id}",
          "starred_url": "https://api.github.com/users/chaoss/starred{/owner}{/repo}",
          "subscriptions_url": "https://api.github.com/users/chaoss/subscriptions",
          "organizations_url": "https://api.github.com/users/chaoss/orgs",
          "repos_url": "https://api.github.com/users/chaoss/repos",
          "events_url": "https://api.github.com/users/chaoss/events{/privacy}",
          "received_events_url": "https://api.github.com/users/chaoss/received_events",
          "type": "Organization",
          "site_admin": false
        },
';


--
-- Name: explorer_pr_response_times; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_pr_response_times AS
 SELECT repo.repo_id,
    pull_requests.pr_src_id,
    repo.repo_name,
    pull_requests.pr_src_author_association,
    repo_groups.rg_name AS repo_group,
    pull_requests.pr_src_state,
    pull_requests.pr_merged_at,
    pull_requests.pr_created_at,
    pull_requests.pr_closed_at,
    date_part('year'::text, (pull_requests.pr_created_at)::date) AS created_year,
    date_part('month'::text, (pull_requests.pr_created_at)::date) AS created_month,
    date_part('year'::text, (pull_requests.pr_closed_at)::date) AS closed_year,
    date_part('month'::text, (pull_requests.pr_closed_at)::date) AS closed_month,
    base_labels.pr_src_meta_label,
    base_labels.pr_head_or_base,
    ((EXTRACT(epoch FROM pull_requests.pr_closed_at) - EXTRACT(epoch FROM pull_requests.pr_created_at)) / (3600)::numeric) AS hours_to_close,
    ((EXTRACT(epoch FROM pull_requests.pr_closed_at) - EXTRACT(epoch FROM pull_requests.pr_created_at)) / (86400)::numeric) AS days_to_close,
    ((EXTRACT(epoch FROM response_times.first_response_time) - EXTRACT(epoch FROM pull_requests.pr_created_at)) / (3600)::numeric) AS hours_to_first_response,
    ((EXTRACT(epoch FROM response_times.first_response_time) - EXTRACT(epoch FROM pull_requests.pr_created_at)) / (86400)::numeric) AS days_to_first_response,
    ((EXTRACT(epoch FROM response_times.last_response_time) - EXTRACT(epoch FROM pull_requests.pr_created_at)) / (3600)::numeric) AS hours_to_last_response,
    ((EXTRACT(epoch FROM response_times.last_response_time) - EXTRACT(epoch FROM pull_requests.pr_created_at)) / (86400)::numeric) AS days_to_last_response,
    response_times.first_response_time,
    response_times.last_response_time,
    response_times.average_time_between_responses,
    response_times.assigned_count,
    response_times.review_requested_count,
    response_times.labeled_count,
    response_times.subscribed_count,
    response_times.mentioned_count,
    response_times.referenced_count,
    response_times.closed_count,
    response_times.head_ref_force_pushed_count,
    response_times.merged_count,
    response_times.milestoned_count,
    response_times.unlabeled_count,
    response_times.head_ref_deleted_count,
    response_times.comment_count,
    master_merged_counts.lines_added,
    master_merged_counts.lines_removed,
    all_commit_counts.commit_count,
    master_merged_counts.file_count
   FROM augur_data.repo,
    augur_data.repo_groups,
    ((((augur_data.pull_requests
     LEFT JOIN ( SELECT pull_requests_1.pull_request_id,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'assigned'::text)) AS assigned_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'review_requested'::text)) AS review_requested_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'labeled'::text)) AS labeled_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'unlabeled'::text)) AS unlabeled_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'subscribed'::text)) AS subscribed_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'mentioned'::text)) AS mentioned_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'referenced'::text)) AS referenced_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'closed'::text)) AS closed_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'head_ref_force_pushed'::text)) AS head_ref_force_pushed_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'head_ref_deleted'::text)) AS head_ref_deleted_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'milestoned'::text)) AS milestoned_count,
            count(*) FILTER (WHERE ((pull_request_events.action)::text = 'merged'::text)) AS merged_count,
            min(message.msg_timestamp) AS first_response_time,
            count(DISTINCT message.msg_timestamp) AS comment_count,
            max(message.msg_timestamp) AS last_response_time,
            ((max(message.msg_timestamp) - min(message.msg_timestamp)) / (count(DISTINCT message.msg_timestamp))::double precision) AS average_time_between_responses
           FROM augur_data.pull_request_events,
            augur_data.pull_requests pull_requests_1,
            augur_data.repo repo_1,
            augur_data.pull_request_message_ref,
            augur_data.message
          WHERE ((repo_1.repo_id = pull_requests_1.repo_id) AND (pull_requests_1.pull_request_id = pull_request_events.pull_request_id) AND (pull_requests_1.pull_request_id = pull_request_message_ref.pull_request_id) AND (pull_request_message_ref.msg_id = message.msg_id))
          GROUP BY pull_requests_1.pull_request_id) response_times ON ((pull_requests.pull_request_id = response_times.pull_request_id)))
     LEFT JOIN ( SELECT pull_request_commits.pull_request_id,
            count(DISTINCT pull_request_commits.pr_cmt_sha) AS commit_count
           FROM augur_data.pull_request_commits,
            augur_data.pull_requests pull_requests_1,
            augur_data.pull_request_meta
          WHERE ((pull_requests_1.pull_request_id = pull_request_commits.pull_request_id) AND (pull_requests_1.pull_request_id = pull_request_meta.pull_request_id) AND ((pull_request_commits.pr_cmt_sha)::text <> (pull_requests_1.pr_merge_commit_sha)::text) AND ((pull_request_commits.pr_cmt_sha)::text <> (pull_request_meta.pr_sha)::text))
          GROUP BY pull_request_commits.pull_request_id) all_commit_counts ON ((pull_requests.pull_request_id = all_commit_counts.pull_request_id)))
     LEFT JOIN ( SELECT max(pull_request_meta.pr_repo_meta_id) AS max,
            pull_request_meta.pull_request_id,
            pull_request_meta.pr_head_or_base,
            pull_request_meta.pr_src_meta_label
           FROM augur_data.pull_requests pull_requests_1,
            augur_data.pull_request_meta
          WHERE ((pull_requests_1.pull_request_id = pull_request_meta.pull_request_id) AND ((pull_request_meta.pr_head_or_base)::text = 'base'::text))
          GROUP BY pull_request_meta.pull_request_id, pull_request_meta.pr_head_or_base, pull_request_meta.pr_src_meta_label) base_labels ON ((base_labels.pull_request_id = all_commit_counts.pull_request_id)))
     LEFT JOIN ( SELECT sum(commits.cmt_added) AS lines_added,
            sum(commits.cmt_removed) AS lines_removed,
            pull_request_commits.pull_request_id,
            count(DISTINCT commits.cmt_filename) AS file_count
           FROM augur_data.pull_request_commits,
            augur_data.commits,
            augur_data.pull_requests pull_requests_1,
            augur_data.pull_request_meta
          WHERE (((commits.cmt_commit_hash)::text = (pull_request_commits.pr_cmt_sha)::text) AND (pull_requests_1.pull_request_id = pull_request_commits.pull_request_id) AND (pull_requests_1.pull_request_id = pull_request_meta.pull_request_id) AND (commits.repo_id = pull_requests_1.repo_id) AND ((commits.cmt_commit_hash)::text <> (pull_requests_1.pr_merge_commit_sha)::text) AND ((commits.cmt_commit_hash)::text <> (pull_request_meta.pr_sha)::text))
          GROUP BY pull_request_commits.pull_request_id) master_merged_counts ON ((base_labels.pull_request_id = master_merged_counts.pull_request_id)))
  WHERE ((repo.repo_group_id = repo_groups.repo_group_id) AND (repo.repo_id = pull_requests.repo_id))
  ORDER BY response_times.merged_count DESC
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_pr_response_times OWNER TO augur;

--
-- Name: repo_labor_repo_labor_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_labor_repo_labor_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_labor_repo_labor_id_seq OWNER TO augur;

--
-- Name: repo_labor; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_labor (
    repo_labor_id bigint DEFAULT nextval('augur_data.repo_labor_repo_labor_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    repo_clone_date timestamp(0) without time zone,
    rl_analysis_date timestamp(0) without time zone,
    programming_language character varying,
    file_path character varying,
    file_name character varying,
    total_lines integer,
    code_lines integer,
    comment_lines integer,
    blank_lines integer,
    code_complexity integer,
    repo_url character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.repo_labor OWNER TO augur;

--
-- Name: TABLE repo_labor; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_labor IS 'repo_labor is a derivative of tables used to store scc code and complexity counting statistics that are inputs to labor analysis, which are components of CHAOSS value metric calculations. ';


--
-- Name: COLUMN repo_labor.repo_url; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_labor.repo_url IS 'This is a convenience column to simplify analysis against external datasets';


--
-- Name: explorer_repo_languages; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_repo_languages AS
 SELECT e.repo_id,
    repo.repo_git,
    repo.repo_name,
    e.programming_language,
    e.code_lines,
    e.files
   FROM augur_data.repo,
    ( SELECT d.repo_id,
            d.programming_language,
            sum(d.code_lines) AS code_lines,
            (count(*))::integer AS files
           FROM ( SELECT repo_labor.repo_id,
                    repo_labor.programming_language,
                    repo_labor.code_lines
                   FROM augur_data.repo_labor,
                    ( SELECT repo_labor_1.repo_id,
                            max(repo_labor_1.data_collection_date) AS last_collected
                           FROM augur_data.repo_labor repo_labor_1
                          GROUP BY repo_labor_1.repo_id) recent
                  WHERE ((repo_labor.repo_id = recent.repo_id) AND (repo_labor.data_collection_date > (recent.last_collected - ((5)::double precision * '00:01:00'::interval))))) d
          GROUP BY d.repo_id, d.programming_language) e
  WHERE (repo.repo_id = e.repo_id)
  ORDER BY e.repo_id
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_repo_languages OWNER TO augur;

--
-- Name: user_groups; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.user_groups (
    group_id bigint NOT NULL,
    user_id integer NOT NULL,
    name character varying NOT NULL,
    favorited boolean DEFAULT false NOT NULL
);


ALTER TABLE augur_operations.user_groups OWNER TO augur;

--
-- Name: user_repos; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.user_repos (
    repo_id bigint NOT NULL,
    group_id bigint NOT NULL
);


ALTER TABLE augur_operations.user_repos OWNER TO augur;

--
-- Name: users; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.users (
    user_id integer NOT NULL,
    login_name character varying NOT NULL,
    login_hashword character varying NOT NULL,
    email character varying NOT NULL,
    text_phone character varying,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    admin boolean NOT NULL,
    email_verified boolean DEFAULT false NOT NULL
);


ALTER TABLE augur_operations.users OWNER TO augur;

--
-- Name: explorer_user_repos; Type: MATERIALIZED VIEW; Schema: augur_data; Owner: augur
--

CREATE MATERIALIZED VIEW augur_data.explorer_user_repos AS
 SELECT a.login_name,
    a.user_id,
    b.group_id,
    c.repo_id
   FROM augur_operations.users a,
    augur_operations.user_groups b,
    augur_operations.user_repos c
  WHERE ((a.user_id = b.user_id) AND (b.group_id = c.group_id))
  ORDER BY a.user_id
  WITH NO DATA;


ALTER MATERIALIZED VIEW augur_data.explorer_user_repos OWNER TO augur;

--
-- Name: issue_assignees_issue_assignee_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.issue_assignees_issue_assignee_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.issue_assignees_issue_assignee_id_seq OWNER TO augur;

--
-- Name: issue_assignees; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.issue_assignees (
    issue_assignee_id bigint DEFAULT nextval('augur_data.issue_assignees_issue_assignee_id_seq'::regclass) NOT NULL,
    issue_id bigint,
    repo_id bigint,
    issue_assignee_src_id bigint,
    issue_assignee_src_node character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid
);


ALTER TABLE augur_data.issue_assignees OWNER TO augur;

--
-- Name: COLUMN issue_assignees.issue_assignee_src_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issue_assignees.issue_assignee_src_id IS 'This ID comes from the source. In the case of GitHub, it is the id that is the first field returned from the issue events API in the issue_assignees embedded JSON object. We may discover it is an ID for the person themselves; but my hypothesis is that its not.';


--
-- Name: COLUMN issue_assignees.issue_assignee_src_node; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issue_assignees.issue_assignee_src_node IS 'This character based identifier comes from the source. In the case of GitHub, it is the id that is the second field returned from the issue events API in the issue_assignees embedded JSON object. We may discover it is an ID for the person themselves; but my hypothesis is that its not.';


--
-- Name: issue_labels_issue_label_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.issue_labels_issue_label_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.issue_labels_issue_label_id_seq OWNER TO augur;

--
-- Name: issue_labels; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.issue_labels (
    issue_label_id bigint DEFAULT nextval('augur_data.issue_labels_issue_label_id_seq'::regclass) NOT NULL,
    issue_id bigint,
    repo_id bigint,
    label_text character varying,
    label_description character varying,
    label_color character varying,
    label_src_id bigint,
    label_src_node_id character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.issue_labels OWNER TO augur;

--
-- Name: COLUMN issue_labels.label_src_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.issue_labels.label_src_id IS 'This character based identifier (node) comes from the source. In the case of GitHub, it is the id that is the second field returned from the issue events API JSON subsection for issues.';


--
-- Name: libraries_library_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.libraries_library_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.libraries_library_id_seq OWNER TO augur;

--
-- Name: libraries; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.libraries (
    library_id bigint DEFAULT nextval('augur_data.libraries_library_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    platform character varying,
    name character varying,
    created_timestamp timestamp(0) without time zone DEFAULT NULL::timestamp without time zone,
    updated_timestamp timestamp(0) without time zone DEFAULT NULL::timestamp without time zone,
    library_description character varying(2000) DEFAULT NULL::character varying,
    keywords character varying,
    library_homepage character varying(1000) DEFAULT NULL::character varying,
    license character varying,
    version_count integer,
    latest_release_timestamp character varying,
    latest_release_number character varying,
    package_manager_id character varying,
    dependency_count integer,
    dependent_library_count integer,
    primary_language character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.libraries OWNER TO augur;

--
-- Name: library_dependencies_lib_dependency_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.library_dependencies_lib_dependency_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.library_dependencies_lib_dependency_id_seq OWNER TO augur;

--
-- Name: library_dependencies; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.library_dependencies (
    lib_dependency_id bigint DEFAULT nextval('augur_data.library_dependencies_lib_dependency_id_seq'::regclass) NOT NULL,
    library_id bigint,
    manifest_platform character varying,
    manifest_filepath character varying(1000) DEFAULT NULL::character varying,
    manifest_kind character varying,
    repo_id_branch character varying NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.library_dependencies OWNER TO augur;

--
-- Name: library_version_library_version_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.library_version_library_version_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.library_version_library_version_id_seq OWNER TO augur;

--
-- Name: library_version; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.library_version (
    library_version_id bigint DEFAULT nextval('augur_data.library_version_library_version_id_seq'::regclass) NOT NULL,
    library_id bigint,
    library_platform character varying,
    version_number character varying,
    version_release_date timestamp(0) without time zone DEFAULT NULL::timestamp without time zone,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.library_version OWNER TO augur;

--
-- Name: lstm_anomaly_models_model_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.lstm_anomaly_models_model_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.lstm_anomaly_models_model_id_seq OWNER TO augur;

--
-- Name: lstm_anomaly_models; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.lstm_anomaly_models (
    model_id bigint DEFAULT nextval('augur_data.lstm_anomaly_models_model_id_seq'::regclass) NOT NULL,
    model_name character varying,
    model_description character varying,
    look_back_days bigint,
    training_days bigint,
    batch_size bigint,
    metric character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(6) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.lstm_anomaly_models OWNER TO augur;

--
-- Name: lstm_anomaly_results_result_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.lstm_anomaly_results_result_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.lstm_anomaly_results_result_id_seq OWNER TO augur;

--
-- Name: lstm_anomaly_results; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.lstm_anomaly_results (
    result_id bigint DEFAULT nextval('augur_data.lstm_anomaly_results_result_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    repo_category character varying,
    model_id bigint,
    metric character varying,
    contamination_factor double precision,
    mean_absolute_error double precision,
    remarks character varying,
    metric_field character varying,
    mean_absolute_actual_value double precision,
    mean_absolute_prediction_value double precision,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(6) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.lstm_anomaly_results OWNER TO augur;

--
-- Name: COLUMN lstm_anomaly_results.metric_field; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.lstm_anomaly_results.metric_field IS 'This is a listing of all of the endpoint fields included in the generation of the metric. Sometimes there is one, sometimes there is more than one. This will list them all. ';


--
-- Name: message_analysis_msg_analysis_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.message_analysis_msg_analysis_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.message_analysis_msg_analysis_id_seq OWNER TO augur;

--
-- Name: message_analysis; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.message_analysis (
    msg_analysis_id bigint DEFAULT nextval('augur_data.message_analysis_msg_analysis_id_seq'::regclass) NOT NULL,
    msg_id bigint,
    worker_run_id bigint,
    sentiment_score double precision,
    reconstruction_error double precision,
    novelty_flag boolean,
    feedback_flag boolean,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.message_analysis OWNER TO augur;

--
-- Name: COLUMN message_analysis.worker_run_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis.worker_run_id IS 'This column is used to indicate analyses run by a worker during the same execution period, and is useful for grouping, and time series analysis.  ';


--
-- Name: COLUMN message_analysis.sentiment_score; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis.sentiment_score IS 'A sentiment analysis score. Zero is neutral, negative numbers are negative sentiment, and positive numbers are positive sentiment. ';


--
-- Name: COLUMN message_analysis.reconstruction_error; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis.reconstruction_error IS 'Each message is converted to a 250 dimensin doc2vec vector, so the reconstruction error is the difference between what the predicted vector and the actual vector.';


--
-- Name: COLUMN message_analysis.novelty_flag; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis.novelty_flag IS 'This is an analysis of the degree to which the message is novel when compared to other messages in a repository.  For example when bots are producing numerous identical messages, the novelty score is low. It would also be a low novelty score when several people are making the same coment. ';


--
-- Name: COLUMN message_analysis.feedback_flag; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis.feedback_flag IS 'This exists to provide the user with an opportunity provide feedback on the resulting the sentiment scores. ';


--
-- Name: message_analysis_summary_msg_summary_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.message_analysis_summary_msg_summary_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.message_analysis_summary_msg_summary_id_seq OWNER TO augur;

--
-- Name: message_analysis_summary; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.message_analysis_summary (
    msg_summary_id bigint DEFAULT nextval('augur_data.message_analysis_summary_msg_summary_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    worker_run_id bigint,
    positive_ratio double precision,
    negative_ratio double precision,
    novel_count bigint,
    period timestamp(0) without time zone,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.message_analysis_summary OWNER TO augur;

--
-- Name: TABLE message_analysis_summary; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.message_analysis_summary IS 'In a relationally perfect world, we would have a table called “message_analysis_run” the incremented the “worker_run_id” for both message_analysis and message_analysis_summary. For now, we decided this was overkill. ';


--
-- Name: COLUMN message_analysis_summary.worker_run_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis_summary.worker_run_id IS 'This value should reflect the worker_run_id for the messages summarized in the table. There is not a relation between these two tables for that purpose because its not *really*, relationaly a concept unless we create a third table for "worker_run_id", which we determined was unnecessarily complex. ';


--
-- Name: COLUMN message_analysis_summary.novel_count; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis_summary.novel_count IS 'The number of messages identified as novel during the analyzed period';


--
-- Name: COLUMN message_analysis_summary.period; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_analysis_summary.period IS 'The whole timeline is divided into periods based on the definition of time period for analysis, which is user specified. Timestamp of the first period to look at, until the end of messages at the data of execution. ';


--
-- Name: message_sentiment_msg_analysis_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.message_sentiment_msg_analysis_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.message_sentiment_msg_analysis_id_seq OWNER TO augur;

--
-- Name: message_sentiment; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.message_sentiment (
    msg_analysis_id bigint DEFAULT nextval('augur_data.message_sentiment_msg_analysis_id_seq'::regclass) NOT NULL,
    msg_id bigint,
    worker_run_id bigint,
    sentiment_score double precision,
    reconstruction_error double precision,
    novelty_flag boolean,
    feedback_flag boolean,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.message_sentiment OWNER TO augur;

--
-- Name: COLUMN message_sentiment.worker_run_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment.worker_run_id IS 'This column is used to indicate analyses run by a worker during the same execution period, and is useful for grouping, and time series analysis.  ';


--
-- Name: COLUMN message_sentiment.sentiment_score; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment.sentiment_score IS 'A sentiment analysis score. Zero is neutral, negative numbers are negative sentiment, and positive numbers are positive sentiment. ';


--
-- Name: COLUMN message_sentiment.reconstruction_error; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment.reconstruction_error IS 'Each message is converted to a 250 dimensin doc2vec vector, so the reconstruction error is the difference between what the predicted vector and the actual vector.';


--
-- Name: COLUMN message_sentiment.novelty_flag; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment.novelty_flag IS 'This is an analysis of the degree to which the message is novel when compared to other messages in a repository.  For example when bots are producing numerous identical messages, the novelty score is low. It would also be a low novelty score when several people are making the same coment. ';


--
-- Name: COLUMN message_sentiment.feedback_flag; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment.feedback_flag IS 'This exists to provide the user with an opportunity provide feedback on the resulting the sentiment scores. ';


--
-- Name: message_sentiment_summary_msg_summary_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.message_sentiment_summary_msg_summary_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.message_sentiment_summary_msg_summary_id_seq OWNER TO augur;

--
-- Name: message_sentiment_summary; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.message_sentiment_summary (
    msg_summary_id bigint DEFAULT nextval('augur_data.message_sentiment_summary_msg_summary_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    worker_run_id bigint,
    positive_ratio double precision,
    negative_ratio double precision,
    novel_count bigint,
    period timestamp(0) without time zone,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.message_sentiment_summary OWNER TO augur;

--
-- Name: TABLE message_sentiment_summary; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.message_sentiment_summary IS 'In a relationally perfect world, we would have a table called “message_sentiment_run” the incremented the “worker_run_id” for both message_sentiment and message_sentiment_summary. For now, we decided this was overkill. ';


--
-- Name: COLUMN message_sentiment_summary.worker_run_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment_summary.worker_run_id IS 'This value should reflect the worker_run_id for the messages summarized in the table. There is not a relation between these two tables for that purpose because its not *really*, relationaly a concept unless we create a third table for "worker_run_id", which we determined was unnecessarily complex. ';


--
-- Name: COLUMN message_sentiment_summary.novel_count; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment_summary.novel_count IS 'The number of messages identified as novel during the analyzed period';


--
-- Name: COLUMN message_sentiment_summary.period; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.message_sentiment_summary.period IS 'The whole timeline is divided into periods based on the definition of time period for analysis, which is user specified. Timestamp of the first period to look at, until the end of messages at the data of execution. ';


--
-- Name: platform_pltfrm_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.platform_pltfrm_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.platform_pltfrm_id_seq OWNER TO augur;

--
-- Name: platform; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.platform (
    pltfrm_id bigint DEFAULT nextval('augur_data.platform_pltfrm_id_seq'::regclass) NOT NULL,
    pltfrm_name character varying,
    pltfrm_version character varying,
    pltfrm_release_date date,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.platform OWNER TO augur;

--
-- Name: pull_request_analysis_pull_request_analysis_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_analysis_pull_request_analysis_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_analysis_pull_request_analysis_id_seq OWNER TO augur;

--
-- Name: pull_request_analysis; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_analysis (
    pull_request_analysis_id bigint DEFAULT nextval('augur_data.pull_request_analysis_pull_request_analysis_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    merge_probability numeric(256,250),
    mechanism character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(6) with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE augur_data.pull_request_analysis OWNER TO augur;

--
-- Name: COLUMN pull_request_analysis.pull_request_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_analysis.pull_request_id IS 'It would be better if the pull request worker is run first to fetch the latest PRs before analyzing';


--
-- Name: COLUMN pull_request_analysis.merge_probability; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_analysis.merge_probability IS 'Indicates the probability of the PR being merged';


--
-- Name: COLUMN pull_request_analysis.mechanism; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_analysis.mechanism IS 'the ML model used for prediction (It is XGBoost Classifier at present)';


--
-- Name: pull_request_assignees_pr_assignee_map_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_assignees_pr_assignee_map_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_assignees_pr_assignee_map_id_seq OWNER TO augur;

--
-- Name: pull_request_assignees; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_assignees (
    pr_assignee_map_id bigint DEFAULT nextval('augur_data.pull_request_assignees_pr_assignee_map_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    repo_id bigint,
    pr_assignee_src_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    contrib_id uuid
);


ALTER TABLE augur_data.pull_request_assignees OWNER TO augur;

--
-- Name: pull_request_files_pr_file_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_files_pr_file_id_seq
    START WITH 25150
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_files_pr_file_id_seq OWNER TO augur;

--
-- Name: pull_request_files; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_files (
    pr_file_id bigint DEFAULT nextval('augur_data.pull_request_files_pr_file_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    repo_id bigint,
    pr_file_additions bigint,
    pr_file_deletions bigint,
    pr_file_path character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.pull_request_files OWNER TO augur;

--
-- Name: TABLE pull_request_files; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.pull_request_files IS 'Pull request commits are an enumeration of each commit associated with a pull request. 
Not all pull requests are from a branch or fork into master. 
The commits table intends to count only commits that end up in the master branch (i.e., part of the deployed code base for a project).
Therefore, there will be commit “SHA”’s in this table that are no associated with a commit SHA in the commits table. 
In cases where the PR is to the master branch of a project, you will find a match. In cases where the PR does not involve the master branch, you will not find a corresponding commit SHA in the commits table. This is expected. ';


--
-- Name: pull_request_labels_pr_label_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_labels_pr_label_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_labels_pr_label_id_seq OWNER TO augur;

--
-- Name: pull_request_labels; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_labels (
    pr_label_id bigint DEFAULT nextval('augur_data.pull_request_labels_pr_label_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    repo_id bigint,
    pr_src_id bigint,
    pr_src_node_id character varying,
    pr_src_url character varying,
    pr_src_description character varying,
    pr_src_color character varying,
    pr_src_default_bool boolean,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.pull_request_labels OWNER TO augur;

--
-- Name: pull_request_repo_pr_repo_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_repo_pr_repo_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_repo_pr_repo_id_seq OWNER TO augur;

--
-- Name: pull_request_repo; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_repo (
    pr_repo_id bigint DEFAULT nextval('augur_data.pull_request_repo_pr_repo_id_seq'::regclass) NOT NULL,
    pr_repo_meta_id bigint,
    pr_repo_head_or_base character varying,
    pr_src_repo_id bigint,
    pr_src_node_id character varying,
    pr_repo_name character varying,
    pr_repo_full_name character varying,
    pr_repo_private_bool boolean,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    pr_cntrb_id uuid
);


ALTER TABLE augur_data.pull_request_repo OWNER TO augur;

--
-- Name: TABLE pull_request_repo; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.pull_request_repo IS 'This table is for storing information about forks that exist as part of a pull request. Generally we do not want to track these like ordinary repositories. ';


--
-- Name: COLUMN pull_request_repo.pr_repo_head_or_base; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_repo.pr_repo_head_or_base IS 'For ease of validation checking, we should determine if the repository referenced is the head or base of the pull request. Each pull request should have one and only one of these, which is not enforcable easily in the database.';


--
-- Name: pull_request_reviewers_pr_reviewer_map_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_reviewers_pr_reviewer_map_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_reviewers_pr_reviewer_map_id_seq OWNER TO augur;

--
-- Name: pull_request_reviewers; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_reviewers (
    pr_reviewer_map_id bigint DEFAULT nextval('augur_data.pull_request_reviewers_pr_reviewer_map_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    pr_source_id bigint,
    repo_id bigint,
    pr_reviewer_src_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid
);


ALTER TABLE augur_data.pull_request_reviewers OWNER TO augur;

--
-- Name: COLUMN pull_request_reviewers.pr_source_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_reviewers.pr_source_id IS 'The platform ID for the pull/merge request. Used as part of the natural key, along with pr_reviewer_src_id in this table. ';


--
-- Name: COLUMN pull_request_reviewers.pr_reviewer_src_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.pull_request_reviewers.pr_reviewer_src_id IS 'The platform ID for the pull/merge request reviewer. Used as part of the natural key, along with pr_source_id in this table. ';


--
-- Name: pull_request_teams_pr_team_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.pull_request_teams_pr_team_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.pull_request_teams_pr_team_id_seq OWNER TO augur;

--
-- Name: pull_request_teams; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.pull_request_teams (
    pr_team_id bigint DEFAULT nextval('augur_data.pull_request_teams_pr_team_id_seq'::regclass) NOT NULL,
    pull_request_id bigint,
    pr_src_team_id bigint,
    pr_src_team_node character varying,
    pr_src_team_url character varying,
    pr_team_name character varying,
    pr_team_slug character varying,
    pr_team_description character varying,
    pr_team_privacy character varying,
    pr_team_permission character varying,
    pr_team_src_members_url character varying,
    pr_team_src_repositories_url character varying,
    pr_team_parent_id bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.pull_request_teams OWNER TO augur;

--
-- Name: releases_release_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.releases_release_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.releases_release_id_seq OWNER TO augur;

--
-- Name: releases; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.releases (
    release_id character(256) DEFAULT nextval('augur_data.releases_release_id_seq'::regclass) NOT NULL,
    repo_id bigint NOT NULL,
    release_name character varying,
    release_description character varying,
    release_author character varying,
    release_created_at timestamp(6) without time zone,
    release_published_at timestamp(6) without time zone,
    release_updated_at timestamp(6) without time zone,
    release_is_draft boolean,
    release_is_prerelease boolean,
    release_tag_name character varying,
    release_url character varying,
    tag_only boolean,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(6) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.releases OWNER TO augur;

--
-- Name: repo_badging_badge_collection_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_badging_badge_collection_id_seq
    START WITH 25012
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_badging_badge_collection_id_seq OWNER TO augur;

--
-- Name: repo_badging; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_badging (
    badge_collection_id bigint DEFAULT nextval('augur_data.repo_badging_badge_collection_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    created_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    data jsonb
);


ALTER TABLE augur_data.repo_badging OWNER TO augur;

--
-- Name: TABLE repo_badging; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_badging IS 'This will be collected from the LF’s Badging API
https://bestpractices.coreinfrastructure.org/projects.json?pq=https%3A%2F%2Fgithub.com%2Fchaoss%2Faugur
';


--
-- Name: repo_clones_data_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_clones_data_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_clones_data_id_seq OWNER TO augur;

--
-- Name: repo_clones_data; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_clones_data (
    repo_clone_data_id bigint DEFAULT nextval('augur_data.repo_clones_data_id_seq'::regclass) NOT NULL,
    repo_id bigint NOT NULL,
    unique_clones bigint,
    count_clones bigint,
    clone_data_timestamp timestamp(6) without time zone
);


ALTER TABLE augur_data.repo_clones_data OWNER TO augur;

--
-- Name: repo_cluster_messages_msg_cluster_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_cluster_messages_msg_cluster_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_cluster_messages_msg_cluster_id_seq OWNER TO augur;

--
-- Name: repo_cluster_messages; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_cluster_messages (
    msg_cluster_id bigint DEFAULT nextval('augur_data.repo_cluster_messages_msg_cluster_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    cluster_content integer,
    cluster_mechanism integer,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_cluster_messages OWNER TO augur;

--
-- Name: repo_dependencies_repo_dependencies_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_dependencies_repo_dependencies_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_dependencies_repo_dependencies_id_seq OWNER TO augur;

--
-- Name: repo_dependencies; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_dependencies (
    repo_dependencies_id bigint DEFAULT nextval('augur_data.repo_dependencies_repo_dependencies_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    dep_name character varying,
    dep_count integer,
    dep_language character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_dependencies OWNER TO augur;

--
-- Name: TABLE repo_dependencies; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_dependencies IS 'Contains the dependencies for a repo.';


--
-- Name: COLUMN repo_dependencies.repo_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_dependencies.repo_id IS 'Forign key for repo id. ';


--
-- Name: COLUMN repo_dependencies.dep_name; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_dependencies.dep_name IS 'Name of the dependancy found in project. ';


--
-- Name: COLUMN repo_dependencies.dep_count; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_dependencies.dep_count IS 'Number of times the dependancy was found. ';


--
-- Name: COLUMN repo_dependencies.dep_language; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_dependencies.dep_language IS 'Language of the dependancy. ';


--
-- Name: repo_deps_libyear_repo_deps_libyear_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_deps_libyear_repo_deps_libyear_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_deps_libyear_repo_deps_libyear_id_seq OWNER TO augur;

--
-- Name: repo_deps_libyear; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_deps_libyear (
    repo_deps_libyear_id bigint DEFAULT nextval('augur_data.repo_deps_libyear_repo_deps_libyear_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    name character varying,
    requirement character varying,
    type character varying,
    package_manager character varying,
    current_verion character varying,
    latest_version character varying,
    current_release_date character varying,
    latest_release_date character varying,
    libyear double precision,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_deps_libyear OWNER TO augur;

--
-- Name: repo_deps_scorecard_repo_deps_scorecard_id_seq1; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_deps_scorecard_repo_deps_scorecard_id_seq1
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_deps_scorecard_repo_deps_scorecard_id_seq1 OWNER TO augur;

--
-- Name: repo_deps_scorecard; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_deps_scorecard (
    repo_deps_scorecard_id bigint DEFAULT nextval('augur_data.repo_deps_scorecard_repo_deps_scorecard_id_seq1'::regclass) NOT NULL,
    repo_id bigint,
    name character varying,
    score character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    scorecard_check_details jsonb
);


ALTER TABLE augur_data.repo_deps_scorecard OWNER TO augur;

--
-- Name: repo_group_insights_rgi_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_group_insights_rgi_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_group_insights_rgi_id_seq OWNER TO augur;

--
-- Name: repo_group_insights; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_group_insights (
    rgi_id bigint DEFAULT nextval('augur_data.repo_group_insights_rgi_id_seq'::regclass) NOT NULL,
    repo_group_id bigint,
    rgi_metric character varying,
    rgi_value character varying,
    cms_id bigint,
    rgi_fresh boolean,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_group_insights OWNER TO augur;

--
-- Name: TABLE repo_group_insights; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_group_insights IS 'This table is output from an analytical worker inside of Augur. It runs through the different metrics on a REPOSITORY_GROUP and identifies the five to ten most “interesting” metrics as defined by some kind of delta or other factor. The algorithm is going to evolve. 

Worker Design Notes: The idea is that the "insight worker" will scan through a bunch of active metrics or "synthetic metrics" to list the most important insights. ';


--
-- Name: COLUMN repo_group_insights.rgi_fresh; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_group_insights.rgi_fresh IS 'false if the date is before the statistic that triggered the insight, true if after. This allows us to automatically display only "fresh insights" and avoid displaying "stale insights". The insight worker will populate this table. ';


--
-- Name: repo_groups_list_serve_rgls_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_groups_list_serve_rgls_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_groups_list_serve_rgls_id_seq OWNER TO augur;

--
-- Name: repo_groups_list_serve; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_groups_list_serve (
    rgls_id bigint DEFAULT nextval('augur_data.repo_groups_list_serve_rgls_id_seq'::regclass) NOT NULL,
    repo_group_id bigint NOT NULL,
    rgls_name character varying,
    rgls_description character varying(3000),
    rgls_sponsor character varying,
    rgls_email character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.repo_groups_list_serve OWNER TO augur;

--
-- Name: repo_info_repo_info_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_info_repo_info_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_info_repo_info_id_seq OWNER TO augur;

--
-- Name: repo_info; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_info (
    repo_info_id bigint DEFAULT nextval('augur_data.repo_info_repo_info_id_seq'::regclass) NOT NULL,
    repo_id bigint NOT NULL,
    last_updated timestamp(0) without time zone DEFAULT NULL::timestamp without time zone,
    issues_enabled character varying,
    open_issues integer,
    pull_requests_enabled character varying,
    wiki_enabled character varying,
    pages_enabled character varying,
    fork_count integer,
    default_branch character varying,
    watchers_count integer,
    "UUID" integer,
    license character varying,
    stars_count integer,
    committers_count integer,
    issue_contributors_count character varying,
    changelog_file character varying,
    contributing_file character varying,
    license_file character varying,
    code_of_conduct_file character varying,
    security_issue_file character varying,
    security_audit_file character varying,
    status character varying,
    keywords character varying,
    commit_count bigint,
    issues_count bigint,
    issues_closed bigint,
    pull_request_count bigint,
    pull_requests_open bigint,
    pull_requests_closed bigint,
    pull_requests_merged bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_info OWNER TO augur;

--
-- Name: repo_insights_ri_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_insights_ri_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_insights_ri_id_seq OWNER TO augur;

--
-- Name: repo_insights; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_insights (
    ri_id bigint DEFAULT nextval('augur_data.repo_insights_ri_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    ri_metric character varying,
    ri_value character varying,
    ri_date timestamp(0) without time zone,
    ri_fresh boolean,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP,
    ri_score numeric,
    ri_field character varying,
    ri_detection_method character varying
);


ALTER TABLE augur_data.repo_insights OWNER TO augur;

--
-- Name: TABLE repo_insights; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_insights IS 'This table is output from an analytical worker inside of Augur. It runs through the different metrics on a repository and identifies the five to ten most “interesting” metrics as defined by some kind of delta or other factor. The algorithm is going to evolve. 

Worker Design Notes: The idea is that the "insight worker" will scan through a bunch of active metrics or "synthetic metrics" to list the most important insights. ';


--
-- Name: COLUMN repo_insights.ri_fresh; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights.ri_fresh IS 'false if the date is before the statistic that triggered the insight, true if after. This allows us to automatically display only "fresh insights" and avoid displaying "stale insights". The insight worker will populate this table. ';


--
-- Name: repo_insights_records_ri_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_insights_records_ri_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_insights_records_ri_id_seq OWNER TO augur;

--
-- Name: repo_insights_records; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_insights_records (
    ri_id bigint DEFAULT nextval('augur_data.repo_insights_records_ri_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    ri_metric character varying,
    ri_field character varying,
    ri_value character varying,
    ri_date timestamp(6) without time zone,
    ri_score double precision,
    ri_detection_method character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(6) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_insights_records OWNER TO augur;

--
-- Name: COLUMN repo_insights_records.ri_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.ri_id IS 'Primary key. ';


--
-- Name: COLUMN repo_insights_records.repo_id; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.repo_id IS 'Refers to repo table primary key. Will have a foreign key';


--
-- Name: COLUMN repo_insights_records.ri_metric; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.ri_metric IS 'The metric endpoint';


--
-- Name: COLUMN repo_insights_records.ri_field; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.ri_field IS 'The field in the metric endpoint';


--
-- Name: COLUMN repo_insights_records.ri_value; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.ri_value IS 'The value of the endpoint in ri_field';


--
-- Name: COLUMN repo_insights_records.ri_date; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.ri_date IS 'The date the insight is for; in other words, some anomaly occurred on this date. ';


--
-- Name: COLUMN repo_insights_records.ri_score; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.ri_score IS 'A Score, derived from the algorithm used. ';


--
-- Name: COLUMN repo_insights_records.ri_detection_method; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.ri_detection_method IS 'A confidence interval or other expression of the type of threshold and the value of a threshold met in order for it to be "an insight". Example. "95% confidence interval". ';


--
-- Name: COLUMN repo_insights_records.tool_source; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.tool_source IS 'Standard Augur Metadata';


--
-- Name: COLUMN repo_insights_records.tool_version; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.tool_version IS 'Standard Augur Metadata';


--
-- Name: COLUMN repo_insights_records.data_source; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.data_source IS 'Standard Augur Metadata';


--
-- Name: COLUMN repo_insights_records.data_collection_date; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON COLUMN augur_data.repo_insights_records.data_collection_date IS 'Standard Augur Metadata';


--
-- Name: repo_meta_rmeta_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_meta_rmeta_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_meta_rmeta_id_seq OWNER TO augur;

--
-- Name: repo_meta; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_meta (
    repo_id bigint NOT NULL,
    rmeta_id bigint DEFAULT nextval('augur_data.repo_meta_rmeta_id_seq'::regclass) NOT NULL,
    rmeta_name character varying,
    rmeta_value character varying DEFAULT 0,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.repo_meta OWNER TO augur;

--
-- Name: TABLE repo_meta; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_meta IS 'Project Languages';


--
-- Name: repo_sbom_scans_rsb_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_sbom_scans_rsb_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_sbom_scans_rsb_id_seq OWNER TO augur;

--
-- Name: repo_sbom_scans; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_sbom_scans (
    rsb_id bigint DEFAULT nextval('augur_data.repo_sbom_scans_rsb_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    sbom_scan json
);


ALTER TABLE augur_data.repo_sbom_scans OWNER TO augur;

--
-- Name: repo_stats_rstat_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_stats_rstat_id_seq
    START WITH 25430
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_stats_rstat_id_seq OWNER TO augur;

--
-- Name: repo_stats; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_stats (
    repo_id bigint NOT NULL,
    rstat_id bigint DEFAULT nextval('augur_data.repo_stats_rstat_id_seq'::regclass) NOT NULL,
    rstat_name character varying(400),
    rstat_value bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone
);


ALTER TABLE augur_data.repo_stats OWNER TO augur;

--
-- Name: TABLE repo_stats; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON TABLE augur_data.repo_stats IS 'Project Watchers';


--
-- Name: repo_test_coverage_repo_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_test_coverage_repo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_test_coverage_repo_id_seq OWNER TO augur;

--
-- Name: repo_test_coverage; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_test_coverage (
    repo_id bigint DEFAULT nextval('augur_data.repo_test_coverage_repo_id_seq'::regclass) NOT NULL,
    repo_clone_date timestamp(0) without time zone,
    rtc_analysis_date timestamp(0) without time zone,
    programming_language character varying,
    file_path character varying,
    file_name character varying,
    testing_tool character varying,
    file_statement_count bigint,
    file_subroutine_count bigint,
    file_statements_tested bigint,
    file_subroutines_tested bigint,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_test_coverage OWNER TO augur;

--
-- Name: repo_topic_repo_topic_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.repo_topic_repo_topic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.repo_topic_repo_topic_id_seq OWNER TO augur;

--
-- Name: repo_topic; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repo_topic (
    repo_topic_id bigint DEFAULT nextval('augur_data.repo_topic_repo_topic_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    topic_id integer,
    topic_prob double precision,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.repo_topic OWNER TO augur;

--
-- Name: repos_fetch_log; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.repos_fetch_log (
    repos_id integer NOT NULL,
    status character varying(128) NOT NULL,
    date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE augur_data.repos_fetch_log OWNER TO augur;

--
-- Name: settings; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.settings (
    id integer NOT NULL,
    setting character varying(32) NOT NULL,
    value character varying NOT NULL,
    last_modified timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE augur_data.settings OWNER TO augur;

--
-- Name: topic_words_topic_words_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.topic_words_topic_words_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.topic_words_topic_words_id_seq OWNER TO augur;

--
-- Name: topic_words; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.topic_words (
    topic_words_id bigint DEFAULT nextval('augur_data.topic_words_topic_words_id_seq'::regclass) NOT NULL,
    topic_id bigint,
    word character varying,
    word_prob double precision,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.topic_words OWNER TO augur;

--
-- Name: unknown_cache; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.unknown_cache (
    type character varying(10) NOT NULL,
    repo_group_id integer NOT NULL,
    email character varying(128) NOT NULL,
    domain character varying(128) DEFAULT 'NULL'::character varying,
    added bigint NOT NULL,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.unknown_cache OWNER TO augur;

--
-- Name: unresolved_commit_emails_email_unresolved_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.unresolved_commit_emails_email_unresolved_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.unresolved_commit_emails_email_unresolved_id_seq OWNER TO augur;

--
-- Name: unresolved_commit_emails; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.unresolved_commit_emails (
    email_unresolved_id bigint DEFAULT nextval('augur_data.unresolved_commit_emails_email_unresolved_id_seq'::regclass) NOT NULL,
    email character varying NOT NULL,
    name character varying,
    tool_source character varying,
    tool_version character varying,
    data_source character varying,
    data_collection_date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE augur_data.unresolved_commit_emails OWNER TO augur;

--
-- Name: utility_log_id_seq1; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.utility_log_id_seq1
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.utility_log_id_seq1 OWNER TO augur;

--
-- Name: utility_log; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.utility_log (
    id bigint DEFAULT nextval('augur_data.utility_log_id_seq1'::regclass) NOT NULL,
    level character varying(8) NOT NULL,
    status character varying NOT NULL,
    attempted timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE augur_data.utility_log OWNER TO augur;

--
-- Name: utility_log_id_seq; Type: SEQUENCE; Schema: augur_data; Owner: augur
--

CREATE SEQUENCE augur_data.utility_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_data.utility_log_id_seq OWNER TO augur;

--
-- Name: working_commits; Type: TABLE; Schema: augur_data; Owner: augur
--

CREATE TABLE augur_data.working_commits (
    repos_id integer NOT NULL,
    working_commit character varying(40) DEFAULT 'NULL'::character varying
);


ALTER TABLE augur_data.working_commits OWNER TO augur;

--
-- Name: affiliations_corp_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.affiliations_corp_id_seq
    START WITH 620000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.affiliations_corp_id_seq OWNER TO augur;

--
-- Name: all; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations."all" (
    "Name" character varying,
    "Bytes" character varying,
    "Lines" character varying,
    "Code" character varying,
    "Comment" character varying,
    "Blank" character varying,
    "Complexity" character varying,
    "Count" character varying,
    "WeightedComplexity" character varying,
    "Files" character varying
);


ALTER TABLE augur_operations."all" OWNER TO augur;

--
-- Name: augur_settings_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.augur_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.augur_settings_id_seq OWNER TO augur;

--
-- Name: augur_settings; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.augur_settings (
    id bigint DEFAULT nextval('augur_operations.augur_settings_id_seq'::regclass) NOT NULL,
    setting character varying,
    value character varying,
    last_modified timestamp(0) without time zone DEFAULT CURRENT_DATE
);


ALTER TABLE augur_operations.augur_settings OWNER TO augur;

--
-- Name: TABLE augur_settings; Type: COMMENT; Schema: augur_operations; Owner: augur
--

COMMENT ON TABLE augur_operations.augur_settings IS 'Augur settings include the schema version, and the Augur API Key as of 10/25/2020. Future augur settings may be stored in this table, which has the basic structure of a name-value pair. ';


--
-- Name: client_applications; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.client_applications (
    id character varying NOT NULL,
    api_key character varying NOT NULL,
    user_id integer NOT NULL,
    name character varying NOT NULL,
    redirect_url character varying NOT NULL
);


ALTER TABLE augur_operations.client_applications OWNER TO augur;

--
-- Name: collection_status; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.collection_status (
    repo_id bigint NOT NULL,
    core_data_last_collected timestamp without time zone,
    core_status character varying DEFAULT 'Pending'::character varying NOT NULL,
    core_task_id character varying,
    secondary_data_last_collected timestamp without time zone,
    secondary_status character varying DEFAULT 'Pending'::character varying NOT NULL,
    secondary_task_id character varying,
    event_last_collected timestamp without time zone,
    facade_status character varying DEFAULT 'Pending'::character varying NOT NULL,
    facade_data_last_collected timestamp without time zone,
    facade_task_id character varying,
    core_weight bigint,
    facade_weight bigint,
    secondary_weight bigint,
    issue_pr_sum bigint,
    commit_sum bigint,
    ml_status character varying DEFAULT 'Pending'::character varying NOT NULL,
    ml_data_last_collected timestamp without time zone,
    ml_task_id character varying,
    ml_weight bigint,
    CONSTRAINT core_data_last_collected_check CHECK (((NOT ((core_data_last_collected IS NULL) AND ((core_status)::text = 'Success'::text))) AND (NOT ((core_data_last_collected IS NOT NULL) AND ((core_status)::text = 'Pending'::text))))),
    CONSTRAINT core_secondary_dependency_check CHECK ((NOT (((core_status)::text = 'Pending'::text) AND ((secondary_status)::text = 'Collecting'::text)))),
    CONSTRAINT core_task_id_check CHECK (((NOT ((core_task_id IS NOT NULL) AND ((core_status)::text = ANY ((ARRAY['Pending'::character varying, 'Success'::character varying, 'Error'::character varying])::text[])))) AND (NOT ((core_task_id IS NULL) AND ((core_status)::text = 'Collecting'::text))))),
    CONSTRAINT facade_data_last_collected_check CHECK (((NOT ((facade_data_last_collected IS NULL) AND ((facade_status)::text = 'Success'::text))) AND (NOT ((facade_data_last_collected IS NOT NULL) AND ((facade_status)::text = ANY ((ARRAY['Pending'::character varying, 'Initializing'::character varying, 'Update'::character varying])::text[])))))),
    CONSTRAINT facade_task_id_check CHECK (((NOT ((facade_task_id IS NOT NULL) AND ((facade_status)::text = ANY ((ARRAY['Pending'::character varying, 'Success'::character varying, 'Error'::character varying, 'Failed Clone'::character varying, 'Initializing'::character varying])::text[])))) AND (NOT ((facade_task_id IS NULL) AND ((facade_status)::text = 'Collecting'::text))))),
    CONSTRAINT secondary_data_last_collected_check CHECK (((NOT ((secondary_data_last_collected IS NULL) AND ((secondary_status)::text = 'Success'::text))) AND (NOT ((secondary_data_last_collected IS NOT NULL) AND ((secondary_status)::text = 'Pending'::text))))),
    CONSTRAINT secondary_task_id_check CHECK (((NOT ((secondary_task_id IS NOT NULL) AND ((secondary_status)::text = ANY ((ARRAY['Pending'::character varying, 'Success'::character varying, 'Error'::character varying])::text[])))) AND (NOT ((secondary_task_id IS NULL) AND ((secondary_status)::text = 'Collecting'::text)))))
);


ALTER TABLE augur_operations.collection_status OWNER TO augur;

--
-- Name: config; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.config (
    id smallint NOT NULL,
    section_name character varying NOT NULL,
    setting_name character varying NOT NULL,
    value character varying,
    type character varying
);


ALTER TABLE augur_operations.config OWNER TO augur;

--
-- Name: config_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.config_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.config_id_seq OWNER TO augur;

--
-- Name: config_id_seq; Type: SEQUENCE OWNED BY; Schema: augur_operations; Owner: augur
--

ALTER SEQUENCE augur_operations.config_id_seq OWNED BY augur_operations.config.id;


--
-- Name: gh_worker_history_history_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.gh_worker_history_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.gh_worker_history_history_id_seq OWNER TO augur;

--
-- Name: refresh_tokens; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.refresh_tokens (
    id character varying NOT NULL,
    user_session_token character varying NOT NULL
);


ALTER TABLE augur_operations.refresh_tokens OWNER TO augur;

--
-- Name: repos_fetch_log; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.repos_fetch_log (
    repos_id integer NOT NULL,
    status character varying(128) NOT NULL,
    date timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE augur_operations.repos_fetch_log OWNER TO augur;

--
-- Name: TABLE repos_fetch_log; Type: COMMENT; Schema: augur_operations; Owner: augur
--

COMMENT ON TABLE augur_operations.repos_fetch_log IS 'For future use when we move all working tables to the augur_operations schema. ';


--
-- Name: subscription_types; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.subscription_types (
    id bigint NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE augur_operations.subscription_types OWNER TO augur;

--
-- Name: subscription_types_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.subscription_types_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.subscription_types_id_seq OWNER TO augur;

--
-- Name: subscription_types_id_seq; Type: SEQUENCE OWNED BY; Schema: augur_operations; Owner: augur
--

ALTER SEQUENCE augur_operations.subscription_types_id_seq OWNED BY augur_operations.subscription_types.id;


--
-- Name: subscriptions; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.subscriptions (
    application_id character varying NOT NULL,
    type_id bigint NOT NULL
);


ALTER TABLE augur_operations.subscriptions OWNER TO augur;

--
-- Name: user_groups_group_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.user_groups_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.user_groups_group_id_seq OWNER TO augur;

--
-- Name: user_groups_group_id_seq; Type: SEQUENCE OWNED BY; Schema: augur_operations; Owner: augur
--

ALTER SEQUENCE augur_operations.user_groups_group_id_seq OWNED BY augur_operations.user_groups.group_id;


--
-- Name: user_session_tokens; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.user_session_tokens (
    token character varying NOT NULL,
    user_id integer NOT NULL,
    created_at bigint,
    expiration bigint,
    application_id character varying
);


ALTER TABLE augur_operations.user_session_tokens OWNER TO augur;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.users_user_id_seq OWNER TO augur;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: augur_operations; Owner: augur
--

ALTER SEQUENCE augur_operations.users_user_id_seq OWNED BY augur_operations.users.user_id;


--
-- Name: worker_history; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.worker_history (
    history_id bigint DEFAULT nextval('augur_operations.gh_worker_history_history_id_seq'::regclass) NOT NULL,
    repo_id bigint,
    worker character varying(255) NOT NULL,
    job_model character varying(255) NOT NULL,
    oauth_id integer,
    "timestamp" timestamp(0) without time zone NOT NULL,
    status character varying(7) NOT NULL,
    total_results integer
);


ALTER TABLE augur_operations.worker_history OWNER TO augur;

--
-- Name: TABLE worker_history; Type: COMMENT; Schema: augur_operations; Owner: augur
--

COMMENT ON TABLE augur_operations.worker_history IS 'This table stores the complete history of job execution, including success and failure. It is useful for troubleshooting. ';


--
-- Name: worker_job; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.worker_job (
    job_model character varying(255) NOT NULL,
    state integer DEFAULT 0 NOT NULL,
    zombie_head integer,
    since_id_str character varying(255) DEFAULT '0'::character varying NOT NULL,
    description character varying(255) DEFAULT 'None'::character varying,
    last_count integer,
    last_run timestamp(0) without time zone DEFAULT NULL::timestamp without time zone,
    analysis_state integer DEFAULT 0,
    oauth_id integer NOT NULL
);


ALTER TABLE augur_operations.worker_job OWNER TO augur;

--
-- Name: TABLE worker_job; Type: COMMENT; Schema: augur_operations; Owner: augur
--

COMMENT ON TABLE augur_operations.worker_job IS 'This table stores the jobs workers collect data for. A job is found in the code, and in the augur.config.json under the construct of a “model”. ';


--
-- Name: worker_oauth_oauth_id_seq; Type: SEQUENCE; Schema: augur_operations; Owner: augur
--

CREATE SEQUENCE augur_operations.worker_oauth_oauth_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE augur_operations.worker_oauth_oauth_id_seq OWNER TO augur;

--
-- Name: worker_oauth; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.worker_oauth (
    oauth_id bigint DEFAULT nextval('augur_operations.worker_oauth_oauth_id_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL,
    consumer_key character varying(255) NOT NULL,
    consumer_secret character varying(255) NOT NULL,
    access_token character varying(255) NOT NULL,
    access_token_secret character varying(255) NOT NULL,
    repo_directory character varying,
    platform character varying DEFAULT 'github'::character varying
);


ALTER TABLE augur_operations.worker_oauth OWNER TO augur;

--
-- Name: TABLE worker_oauth; Type: COMMENT; Schema: augur_operations; Owner: augur
--

COMMENT ON TABLE augur_operations.worker_oauth IS 'This table stores credentials for retrieving data from platform API’s. Entries in this table must comply with the terms of service for each platform. ';


--
-- Name: worker_settings_facade; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.worker_settings_facade (
    id integer NOT NULL,
    setting character varying(32) NOT NULL,
    value character varying NOT NULL,
    last_modified timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE augur_operations.worker_settings_facade OWNER TO augur;

--
-- Name: TABLE worker_settings_facade; Type: COMMENT; Schema: augur_operations; Owner: augur
--

COMMENT ON TABLE augur_operations.worker_settings_facade IS 'For future use when we move all working tables to the augur_operations schema. ';


--
-- Name: working_commits; Type: TABLE; Schema: augur_operations; Owner: augur
--

CREATE TABLE augur_operations.working_commits (
    repos_id integer NOT NULL,
    working_commit character varying(40) DEFAULT 'NULL'::character varying
);


ALTER TABLE augur_operations.working_commits OWNER TO augur;

--
-- Name: TABLE working_commits; Type: COMMENT; Schema: augur_operations; Owner: augur
--

COMMENT ON TABLE augur_operations.working_commits IS 'For future use when we move all working tables to the augur_operations schema. ';


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: augur
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO augur;

--
-- Name: test; Type: TABLE; Schema: public; Owner: augur
--

CREATE TABLE public.test (
    test character varying(255)
);


ALTER TABLE public.test OWNER TO augur;

--
-- Name: annotation_types_annotation_type_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.annotation_types_annotation_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.annotation_types_annotation_type_id_seq OWNER TO augur;

--
-- Name: annotation_types; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.annotation_types (
    annotation_type_id integer DEFAULT nextval('spdx.annotation_types_annotation_type_id_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE spdx.annotation_types OWNER TO augur;

--
-- Name: annotations_annotation_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.annotations_annotation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.annotations_annotation_id_seq OWNER TO augur;

--
-- Name: annotations; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.annotations (
    annotation_id integer DEFAULT nextval('spdx.annotations_annotation_id_seq'::regclass) NOT NULL,
    document_id integer NOT NULL,
    annotation_type_id integer NOT NULL,
    identifier_id integer NOT NULL,
    creator_id integer NOT NULL,
    created_ts timestamp(6) with time zone,
    comment text NOT NULL
);


ALTER TABLE spdx.annotations OWNER TO augur;

--
-- Name: augur_repo_map_map_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.augur_repo_map_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.augur_repo_map_map_id_seq OWNER TO augur;

--
-- Name: augur_repo_map; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.augur_repo_map (
    map_id integer DEFAULT nextval('spdx.augur_repo_map_map_id_seq'::regclass) NOT NULL,
    dosocs_pkg_id integer,
    dosocs_pkg_name text,
    repo_id integer,
    repo_path text
);


ALTER TABLE spdx.augur_repo_map OWNER TO augur;

--
-- Name: creator_types_creator_type_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.creator_types_creator_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.creator_types_creator_type_id_seq OWNER TO augur;

--
-- Name: creator_types; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.creator_types (
    creator_type_id integer DEFAULT nextval('spdx.creator_types_creator_type_id_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE spdx.creator_types OWNER TO augur;

--
-- Name: creators_creator_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.creators_creator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.creators_creator_id_seq OWNER TO augur;

--
-- Name: creators; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.creators (
    creator_id integer DEFAULT nextval('spdx.creators_creator_id_seq'::regclass) NOT NULL,
    creator_type_id integer NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL
);


ALTER TABLE spdx.creators OWNER TO augur;

--
-- Name: document_namespaces_document_namespace_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.document_namespaces_document_namespace_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.document_namespaces_document_namespace_id_seq OWNER TO augur;

--
-- Name: document_namespaces; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.document_namespaces (
    document_namespace_id integer DEFAULT nextval('spdx.document_namespaces_document_namespace_id_seq'::regclass) NOT NULL,
    uri character varying(500) NOT NULL
);


ALTER TABLE spdx.document_namespaces OWNER TO augur;

--
-- Name: documents_document_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.documents_document_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.documents_document_id_seq OWNER TO augur;

--
-- Name: documents; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.documents (
    document_id integer DEFAULT nextval('spdx.documents_document_id_seq'::regclass) NOT NULL,
    document_namespace_id integer NOT NULL,
    data_license_id integer NOT NULL,
    spdx_version character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    license_list_version character varying(255) NOT NULL,
    created_ts timestamp(6) with time zone NOT NULL,
    creator_comment text NOT NULL,
    document_comment text NOT NULL,
    package_id integer NOT NULL
);


ALTER TABLE spdx.documents OWNER TO augur;

--
-- Name: documents_creators_document_creator_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.documents_creators_document_creator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.documents_creators_document_creator_id_seq OWNER TO augur;

--
-- Name: documents_creators; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.documents_creators (
    document_creator_id integer DEFAULT nextval('spdx.documents_creators_document_creator_id_seq'::regclass) NOT NULL,
    document_id integer NOT NULL,
    creator_id integer NOT NULL
);


ALTER TABLE spdx.documents_creators OWNER TO augur;

--
-- Name: external_refs_external_ref_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.external_refs_external_ref_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.external_refs_external_ref_id_seq OWNER TO augur;

--
-- Name: external_refs; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.external_refs (
    external_ref_id integer DEFAULT nextval('spdx.external_refs_external_ref_id_seq'::regclass) NOT NULL,
    document_id integer NOT NULL,
    document_namespace_id integer NOT NULL,
    id_string character varying(255) NOT NULL,
    sha256 character varying(64) NOT NULL
);


ALTER TABLE spdx.external_refs OWNER TO augur;

--
-- Name: file_contributors_file_contributor_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.file_contributors_file_contributor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.file_contributors_file_contributor_id_seq OWNER TO augur;

--
-- Name: file_contributors; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.file_contributors (
    file_contributor_id integer DEFAULT nextval('spdx.file_contributors_file_contributor_id_seq'::regclass) NOT NULL,
    file_id integer NOT NULL,
    contributor text NOT NULL
);


ALTER TABLE spdx.file_contributors OWNER TO augur;

--
-- Name: file_types; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.file_types (
    file_type_id integer,
    name character varying(255) NOT NULL
);


ALTER TABLE spdx.file_types OWNER TO augur;

--
-- Name: file_types_file_type_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.file_types_file_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.file_types_file_type_id_seq OWNER TO augur;

--
-- Name: files_file_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.files_file_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.files_file_id_seq OWNER TO augur;

--
-- Name: files; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.files (
    file_id integer DEFAULT nextval('spdx.files_file_id_seq'::regclass) NOT NULL,
    file_type_id integer,
    sha256 character varying(64) NOT NULL,
    copyright_text text,
    package_id integer,
    comment text NOT NULL,
    notice text NOT NULL
);


ALTER TABLE spdx.files OWNER TO augur;

--
-- Name: files_licenses_file_license_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.files_licenses_file_license_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.files_licenses_file_license_id_seq OWNER TO augur;

--
-- Name: files_licenses; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.files_licenses (
    file_license_id integer DEFAULT nextval('spdx.files_licenses_file_license_id_seq'::regclass) NOT NULL,
    file_id integer NOT NULL,
    license_id integer NOT NULL,
    extracted_text text NOT NULL
);


ALTER TABLE spdx.files_licenses OWNER TO augur;

--
-- Name: files_scans_file_scan_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.files_scans_file_scan_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.files_scans_file_scan_id_seq OWNER TO augur;

--
-- Name: files_scans; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.files_scans (
    file_scan_id integer DEFAULT nextval('spdx.files_scans_file_scan_id_seq'::regclass) NOT NULL,
    file_id integer NOT NULL,
    scanner_id integer NOT NULL
);


ALTER TABLE spdx.files_scans OWNER TO augur;

--
-- Name: identifiers_identifier_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.identifiers_identifier_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.identifiers_identifier_id_seq OWNER TO augur;

--
-- Name: identifiers; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.identifiers (
    identifier_id integer DEFAULT nextval('spdx.identifiers_identifier_id_seq'::regclass) NOT NULL,
    document_namespace_id integer NOT NULL,
    id_string character varying(255) NOT NULL,
    document_id integer,
    package_id integer,
    package_file_id integer,
    CONSTRAINT ck_identifier_exactly_one CHECK ((((((document_id IS NOT NULL))::integer + ((package_id IS NOT NULL))::integer) + ((package_file_id IS NOT NULL))::integer) = 1))
);


ALTER TABLE spdx.identifiers OWNER TO augur;

--
-- Name: licenses_license_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.licenses_license_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.licenses_license_id_seq OWNER TO augur;

--
-- Name: licenses; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.licenses (
    license_id integer DEFAULT nextval('spdx.licenses_license_id_seq'::regclass) NOT NULL,
    name character varying(255),
    short_name character varying(255) NOT NULL,
    cross_reference text NOT NULL,
    comment text NOT NULL,
    is_spdx_official boolean NOT NULL
);


ALTER TABLE spdx.licenses OWNER TO augur;

--
-- Name: packages_package_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.packages_package_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.packages_package_id_seq OWNER TO augur;

--
-- Name: packages; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.packages (
    package_id integer DEFAULT nextval('spdx.packages_package_id_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL,
    version character varying(255) NOT NULL,
    file_name text NOT NULL,
    supplier_id integer,
    originator_id integer,
    download_location text,
    verification_code character varying(64) NOT NULL,
    ver_code_excluded_file_id integer,
    sha256 character varying(64),
    home_page text,
    source_info text NOT NULL,
    concluded_license_id integer,
    declared_license_id integer,
    license_comment text NOT NULL,
    copyright_text text,
    summary text NOT NULL,
    description text NOT NULL,
    comment text NOT NULL,
    dosocs2_dir_code character varying(64),
    CONSTRAINT uc_sha256_ds2_dir_code_exactly_one CHECK (((((sha256 IS NOT NULL))::integer + ((dosocs2_dir_code IS NOT NULL))::integer) = 1))
);


ALTER TABLE spdx.packages OWNER TO augur;

--
-- Name: packages_files_package_file_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.packages_files_package_file_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.packages_files_package_file_id_seq OWNER TO augur;

--
-- Name: packages_files; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.packages_files (
    package_file_id integer DEFAULT nextval('spdx.packages_files_package_file_id_seq'::regclass) NOT NULL,
    package_id integer NOT NULL,
    file_id integer NOT NULL,
    concluded_license_id integer,
    license_comment text NOT NULL,
    file_name text NOT NULL
);


ALTER TABLE spdx.packages_files OWNER TO augur;

--
-- Name: packages_scans_package_scan_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.packages_scans_package_scan_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.packages_scans_package_scan_id_seq OWNER TO augur;

--
-- Name: packages_scans; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.packages_scans (
    package_scan_id integer DEFAULT nextval('spdx.packages_scans_package_scan_id_seq'::regclass) NOT NULL,
    package_id integer NOT NULL,
    scanner_id integer NOT NULL
);


ALTER TABLE spdx.packages_scans OWNER TO augur;

--
-- Name: projects_package_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.projects_package_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.projects_package_id_seq OWNER TO augur;

--
-- Name: projects; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.projects (
    package_id integer DEFAULT nextval('spdx.projects_package_id_seq'::regclass) NOT NULL,
    name text NOT NULL,
    homepage text NOT NULL,
    uri text NOT NULL
);


ALTER TABLE spdx.projects OWNER TO augur;

--
-- Name: relationship_types_relationship_type_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.relationship_types_relationship_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.relationship_types_relationship_type_id_seq OWNER TO augur;

--
-- Name: relationship_types; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.relationship_types (
    relationship_type_id integer DEFAULT nextval('spdx.relationship_types_relationship_type_id_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE spdx.relationship_types OWNER TO augur;

--
-- Name: relationships_relationship_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.relationships_relationship_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.relationships_relationship_id_seq OWNER TO augur;

--
-- Name: relationships; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.relationships (
    relationship_id integer DEFAULT nextval('spdx.relationships_relationship_id_seq'::regclass) NOT NULL,
    left_identifier_id integer NOT NULL,
    right_identifier_id integer NOT NULL,
    relationship_type_id integer NOT NULL,
    relationship_comment text NOT NULL
);


ALTER TABLE spdx.relationships OWNER TO augur;

--
-- Name: sbom_scans; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.sbom_scans (
    repo_id integer,
    sbom_scan json
);


ALTER TABLE spdx.sbom_scans OWNER TO augur;

--
-- Name: scanners_scanner_id_seq; Type: SEQUENCE; Schema: spdx; Owner: augur
--

CREATE SEQUENCE spdx.scanners_scanner_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER SEQUENCE spdx.scanners_scanner_id_seq OWNER TO augur;

--
-- Name: scanners; Type: TABLE; Schema: spdx; Owner: augur
--

CREATE TABLE spdx.scanners (
    scanner_id integer DEFAULT nextval('spdx.scanners_scanner_id_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE spdx.scanners OWNER TO augur;

--
-- Name: chaoss_user chaoss_id; Type: DEFAULT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.chaoss_user ALTER COLUMN chaoss_id SET DEFAULT nextval('augur_data.chaoss_user_chaoss_id_seq'::regclass);


--
-- Name: config id; Type: DEFAULT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.config ALTER COLUMN id SET DEFAULT nextval('augur_operations.config_id_seq'::regclass);


--
-- Name: subscription_types id; Type: DEFAULT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.subscription_types ALTER COLUMN id SET DEFAULT nextval('augur_operations.subscription_types_id_seq'::regclass);


--
-- Name: user_groups group_id; Type: DEFAULT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_groups ALTER COLUMN group_id SET DEFAULT nextval('augur_operations.user_groups_group_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.users ALTER COLUMN user_id SET DEFAULT nextval('augur_operations.users_user_id_seq'::regclass);


--
-- Data for Name: analysis_log; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.analysis_log (repos_id, status, date_attempted) FROM stdin;
\.


--
-- Data for Name: chaoss_metric_status; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.chaoss_metric_status (cms_id, cm_group, cm_source, cm_type, cm_backend_status, cm_frontend_status, cm_defined, cm_api_endpoint_repo, cm_api_endpoint_rg, cm_name, cm_working_group, cm_info, tool_source, tool_version, data_source, data_collection_date, cm_working_group_focus_area) FROM stdin;
2	growth-maturity-decline	githubapi	timeseries	implemented	unimplemented	t	/api/unstable/<owner>/<repo>/timeseries/githubapi/issues	\N	Open Issues	growth-maturity-decline	"open-issues"	Insight Worker	0.0.1	githubapi	2019-06-20 22:41:41	\N
3	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/issues	\N	Open Issues	growth-maturity-decline	"open-issues"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:42:15	\N
4	growth-maturity-decline	githubapi	timeseries	implemented	unimplemented	t	/api/unstable/<owner>/<repo>/timeseries/githubapi/issues/closed	\N	Closed Issues	growth-maturity-decline	"closed-issues"	Insight Worker	0.0.1	githubapi	2019-06-20 22:45:53	\N
5	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/issues/closed	\N	Closed Issues	growth-maturity-decline	"closed-issues"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:26	\N
6	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/issues/response_time	\N	First Response To Issue Duration	growth-maturity-decline	"first-response-to-issue-duration"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:27	\N
7	growth-maturity-decline	githubapi	timeseries	implemented	unimplemented	t	/api/unstable/<owner>/<repo>/timeseries/githubapi/commits	\N	Code Commits	growth-maturity-decline	"code-commits"	Insight Worker	0.0.1	githubapi	2019-06-20 22:49:29	\N
8	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/commits	\N	Code Commits	growth-maturity-decline	"code-commits"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:30	\N
9	growth-maturity-decline	githubapi	metric	implemented	unimplemented	t	/api/unstable/<owner>/<repo>/lines_changed	\N	Lines Of Code Changed	growth-maturity-decline	"lines-of-code-changed"	Insight Worker	0.0.1	githubapi	2019-06-20 22:49:32	\N
10	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/pulls/maintainer_response_time	\N	Maintainer Response To Merge Request Duration	growth-maturity-decline	"maintainer-response-to-merge-request-duration"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:33	\N
11	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/code_review_iteration	\N	Code Review Iteration	growth-maturity-decline	"code-review-iteration"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:35	\N
12	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/forks	\N	Forks	growth-maturity-decline	"forks"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:36	\N
13	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/pulls	\N	Pull Requests Open	growth-maturity-decline	"pull-requests-open"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:38	\N
14	growth-maturity-decline	ghtorrent	timeseries	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/timeseries/pulls/closed	\N	Pull Requests Closed	growth-maturity-decline	"pull-requests-closed"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:39	\N
15	growth-maturity-decline	ghtorrent	timeseries	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/timeseries/pulls/response_time	\N	Pull Request Comment Duration	growth-maturity-decline	"pull-request-comment-duration"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:41	\N
16	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/pulls/comments	\N	Pull Request Comments	growth-maturity-decline	"pull-request-comments"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:42	\N
17	growth-maturity-decline	augur_db	metric	implemented	unimplemented	t	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/contributors	\N	Contributors	growth-maturity-decline	"contributors"	Insight Worker	0.0.1	augur_db	2019-06-20 22:49:44	\N
18	growth-maturity-decline	githubapi	metric	implemented	unimplemented	t	/api/unstable/<owner>/<repo>/githubapi/contributors	\N	Contributors	growth-maturity-decline	"contributors"	Insight Worker	0.0.1	githubapi	2019-06-20 22:49:45	\N
19	growth-maturity-decline	ghtorrent	metric	implemented	implemented	t	/api/unstable/<owner>/<repo>/contributors	\N	Contributors	growth-maturity-decline	"contributors"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:47	\N
20	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/community_engagement	\N	Community Engagement	growth-maturity-decline	"community-engagement"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:48	\N
21	growth-maturity-decline	augur_db	metric	implemented	unimplemented	t	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/sub-projects	\N	Sub Projects	growth-maturity-decline	"sub-projects"	Insight Worker	0.0.1	augur_db	2019-06-20 22:49:50	\N
22	growth-maturity-decline	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/contribution_acceptance	\N	Contribution Acceptance	growth-maturity-decline	"contribution-acceptance"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:49:51	\N
23	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/code-changes	\N	Code Changes	experimental	"code-changes"	Insight Worker	0.0.1	augur_db	2019-06-20 22:49:53	\N
24	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/pull-requests-merge-contributor-new	\N	Pull Requests Merge Contributor New	experimental	"pull-requests-merge-contributor-new"	Insight Worker	0.0.1	augur_db	2019-06-20 22:49:55	\N
25	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/issues-first-time-opened	\N	Issues First Time Opened	experimental	"issues-first-time-opened"	Insight Worker	0.0.1	augur_db	2019-06-20 22:49:56	\N
26	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/issues-first-time-closed	\N	Issues First Time Closed	experimental	"issues-first-time-closed"	Insight Worker	0.0.1	augur_db	2019-06-20 22:49:58	\N
27	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/contributors-new	\N	Contributors New	experimental	"contributors-new"	Insight Worker	0.0.1	augur_db	2019-06-20 22:49:59	\N
28	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/code-changes-lines	\N	Code Changes Lines	experimental	"code-changes-lines"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:01	\N
29	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/issues-new	\N	Issues New	experimental	"issues-new"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:02	\N
30	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/issues-closed	\N	Issues Closed	experimental	"issues-closed"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:04	\N
31	experimental	augur_db	metric	implemented	unimplemented	f	none	\N	Issue Duration	experimental	"issue-duration"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:05	\N
32	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/issue-backlog	\N	Issue Backlog	experimental	"issue-backlog"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:07	\N
33	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/issues-open-age	\N	Issues Open Age	experimental	"issues-open-age"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:08	\N
34	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/issues-closed-resolution-duration	\N	Issues Closed Resolution Duration	experimental	"issues-closed-resolution-duration"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:10	\N
35	experimental	augur_db	metric	implemented	unimplemented	f	none	\N	Lines Changed By Author	experimental	"lines-changed-by-author"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:11	\N
36	experimental	augur_db	git	implemented	unimplemented	f	/api/unstable/repo-groups	\N	Repo Groups	experimental	"repo-groups"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:13	\N
37	experimental	augur_db	git	implemented	unimplemented	f	/api/unstable/repos	\N	Downloaded Repos	experimental	"downloaded-repos"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:15	\N
38	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/open-issues-count	\N	Open Issues Count	experimental	"closed-issues-count"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:16	\N
39	experimental	augur_db	metric	implemented	unimplemented	f	/api/unstable/repo-groups/<repo_group_id>/repos/<repo_id>/closed-issues-count	\N	Closed Issues Count	experimental	"closed-issues-count"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:18	\N
40	experimental	augur_db	git	implemented	unimplemented	f	/api/unstable/repos/<owner>/<repo>	\N	Get Repo	experimental	"get-repo"	Insight Worker	0.0.1	augur_db	2019-06-20 22:50:19	\N
41	experimental	downloads	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/downloads	\N	Downloads	experimental	"downloads"	Insight Worker	0.0.1	downloads	2019-06-20 22:50:21	\N
42	experimental	githubapi	metric	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/githubapi/pull_requests_closed	\N	Pull Requests Closed	experimental	"pull_requests_closed"	Insight Worker	0.0.1	githubapi	2019-06-20 22:50:22	\N
43	experimental	githubapi	metric	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/githubapi/pull_requests_merged	\N	Pull Requests Merged	experimental	"pull_requests_merged"	Insight Worker	0.0.1	githubapi	2019-06-20 22:50:24	\N
44	experimental	githubapi	metric	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/githubapi/pull_requests_open	\N	Pull Requests Open	experimental	"pull_requests_open"	Insight Worker	0.0.1	githubapi	2019-06-20 22:50:25	\N
45	experimental	githubapi	metric	implemented	unimplemented	t	/api/unstable/<owner>/<repo>/githubapi/repository_size	\N	Repository Size	experimental	"repository-size"	Insight Worker	0.0.1	githubapi	2019-06-20 22:50:27	\N
46	experimental	githubapi	metric	implemented	implemented	t	/api/unstable/<owner>/<repo>/bus_factor	\N	Bus Factor	experimental	"bus-factor"	Insight Worker	0.0.1	githubapi	2019-06-20 22:50:28	\N
47	experimental	githubapi	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/tags/major	\N	Major Tags	experimental	"major-tags"	Insight Worker	0.0.1	githubapi	2019-06-20 22:50:30	\N
48	experimental	githubapi	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/tags	\N	Tags	experimental	"tags"	Insight Worker	0.0.1	githubapi	2019-06-20 22:50:31	\N
49	experimental	facade	git	implemented	unimplemented	f	/api/unstable/git/repos	\N	Downloaded Repos	experimental	"downloaded-repos"	Insight Worker	0.0.1	facade	2019-06-20 22:50:33	\N
50	experimental	facade	git	implemented	implemented	f	/api/unstable/git/changes_by_author	\N	Lines Changed By Author	experimental	"lines-changed-by-author"	Insight Worker	0.0.1	facade	2019-06-20 22:50:35	\N
51	experimental	facade	git	implemented	unimplemented	f	/api/unstable/git/lines_changed_by_week	\N	Lines Changed By Week	experimental	"lines-changed-by-week"	Insight Worker	0.0.1	facade	2019-06-20 22:50:36	\N
52	experimental	facade	git	implemented	unimplemented	f	/api/unstable/git/lines_changed_by_month	\N	Lines Changed By Month	experimental	"lines-changed-by-month"	Insight Worker	0.0.1	facade	2019-06-20 22:50:38	\N
53	experimental	facade	git	implemented	unimplemented	f	/api/unstable/git/commits_by_week	\N	Commits By Week	experimental	"commits-by-week"	Insight Worker	0.0.1	facade	2019-06-20 22:50:40	\N
54	experimental	facade	git	implemented	implemented	f	/api/unstable/git/facade_project	\N	Facade Project	experimental	"facade-project"	Insight Worker	0.0.1	facade	2019-06-20 22:50:41	\N
55	experimental	facade	metric	implemented	unimplemented	f	none	\N	Annual Commit Count Ranked By New Repo In Repo Group	experimental	"annual-commit-count-ranked-by-new-repo-in-repo-group"	Insight Worker	0.0.1	facade	2019-06-20 22:50:43	\N
56	experimental	facade	metric	implemented	unimplemented	f	none	\N	Annual Lines Of Code Count Ranked By New Repo In Repo Group	experimental	"annual-lines-of-code-count-ranked-by-new-repo-in-repo-group"	Insight Worker	0.0.1	facade	2019-06-20 22:50:44	\N
57	experimental	facade	metric	implemented	unimplemented	f	none	\N	Annual Commit Count Ranked By Repo In Repo Group	experimental	"annual-commit-count-ranked-by-repo-in-repo-group"	Insight Worker	0.0.1	facade	2019-06-20 22:50:46	\N
58	experimental	facade	metric	implemented	unimplemented	f	none	\N	Annual Lines Of Code Count Ranked By Repo In Repo Group	experimental	"annual-lines-of-code-count-ranked-by-repo-in-repo-group"	Insight Worker	0.0.1	facade	2019-06-20 22:50:48	\N
59	experimental	facade	metric	implemented	unimplemented	f	none	\N	Lines Of Code Commit Counts By Calendar Year Grouped	experimental	"lines-of-code-commit-counts-by-calendar-year-grouped"	Insight Worker	0.0.1	facade	2019-06-20 22:50:49	\N
60	experimental	facade	metric	implemented	unimplemented	f	none	\N	Unaffiliated Contributors Lines Of Code Commit Counts By Calendar Year Grouped	experimental	"unaffiliated-contributors-lines-of-code-commit-counts-by-calendar-year-grouped"	Insight Worker	0.0.1	facade	2019-06-20 22:50:51	\N
61	experimental	facade	metric	implemented	unimplemented	f	none	\N	Repo Group Lines Of Code Commit Counts Calendar Year Grouped	experimental	"repo-group-lines-of-code-commit-counts-calendar-year-grouped"	Insight Worker	0.0.1	facade	2019-06-20 22:50:52	\N
62	experimental	ghtorrent	metric	implemented	implemented	f	/api/unstable/<owner>/<repo>/contributing_github_organizations	\N	Contributing Github Organizations	experimental	"contributing-github-organizations"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:50:54	\N
63	experimental	ghtorrent	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/new_contributing_github_organizations	\N	New Contributing Github Organizations	experimental	"new-contributing-github-organizations"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:50:56	\N
64	experimental	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/issue_comments	\N	Issue Comments	experimental	"issue-comments"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:50:57	\N
65	experimental	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/pulls/made_closed	\N	Pull Requests Made Closed	experimental	"pull-requests-made-closed"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:50:59	\N
66	experimental	ghtorrent	timeseries	implemented	implemented	t	/api/unstable/<owner>/<repo>/timeseries/watchers	\N	Watchers	experimental	"watchers"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:00	\N
67	experimental	ghtorrent	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/commits100	\N	Commits100	experimental	"commits100"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:02	\N
68	experimental	ghtorrent	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/commits/comments	\N	Commit Comments	experimental	"commit-comments"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:03	\N
69	experimental	ghtorrent	metric	implemented	implemented	f	/api/unstable/<owner>/<repo>/committer_locations	\N	Committer Locations	experimental	"committer-locations"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:05	\N
70	experimental	ghtorrent	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/total_committers	\N	Total Committers	experimental	"total-committers"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:07	\N
71	experimental	ghtorrent	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/issues/activity	\N	Issue Activity	experimental	"issue-activity"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:08	\N
72	experimental	ghtorrent	timeseries	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/timeseries/pulls/acceptance_rate	\N	Pull Request Acceptance Rate	experimental	"pull-request-acceptance-rate"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:10	\N
73	experimental	ghtorrent	metric	implemented	implemented	f	/api/unstable/<owner>/<repo>/community_age	\N	Community Age	experimental	"community-age"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:11	\N
74	experimental	ghtorrent	metric	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/timeseries/contributions	\N	Contributions	experimental	"contributions"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:13	\N
75	experimental	ghtorrent	metric	implemented	implemented	f	/api/unstable/<owner>/<repo>/project_age	\N	Project Age	experimental	"project-age"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:14	\N
76	experimental	ghtorrent	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/fakes	\N	Fakes	experimental	"fakes"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:16	\N
77	experimental	ghtorrent	timeseries	implemented	unimplemented	f	/api/unstable/<owner>/<repo>/timeseries/total_watchers	\N	Total Watchers	experimental	"total-watchers"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:18	\N
78	experimental	ghtorrent	timeseries	implemented	implemented	f	/api/unstable/<owner>/<repo>/timeseries/new_watchers	\N	New Watchers	experimental	"new-watchers"	Insight Worker	0.0.1	ghtorrent	2019-06-20 22:51:19	\N
79	experimental	librariesio	metric	implemented	implemented	f	/api/unstable/<owner>/<repo>/dependencies	\N	Dependencies	experimental	"dependencies"	Insight Worker	0.0.1	librariesio	2019-06-20 22:51:21	\N
80	experimental	librariesio	metric	implemented	implemented	f	/api/unstable/<owner>/<repo>/dependency_stats	\N	Dependency Stats	experimental	"dependency-stats"	Insight Worker	0.0.1	librariesio	2019-06-20 22:51:23	\N
81	experimental	librariesio	metric	implemented	implemented	f	/api/unstable/<owner>/<repo>/dependents	\N	Dependents	experimental	"dependents"	Insight Worker	0.0.1	librariesio	2019-06-20 22:51:25	\N
\.


--
-- Data for Name: chaoss_user; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.chaoss_user (chaoss_id, chaoss_login_name, chaoss_login_hashword, chaoss_email, chaoss_text_phone, chaoss_first_name, chaoss_last_name, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: commit_comment_ref; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.commit_comment_ref (cmt_comment_id, cmt_id, repo_id, msg_id, user_id, body, line, "position", commit_comment_src_node_id, cmt_comment_src_id, created_at, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: commit_parents; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.commit_parents (cmt_id, parent_id, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: commits; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.commits (cmt_id, repo_id, cmt_commit_hash, cmt_author_name, cmt_author_raw_email, cmt_author_email, cmt_author_date, cmt_author_affiliation, cmt_committer_name, cmt_committer_raw_email, cmt_committer_email, cmt_committer_date, cmt_committer_affiliation, cmt_added, cmt_removed, cmt_whitespace, cmt_filename, cmt_date_attempted, cmt_ght_committer_id, cmt_ght_committed_at, cmt_committer_timestamp, cmt_author_timestamp, cmt_author_platform_username, tool_source, tool_version, data_source, data_collection_date, cmt_ght_author_id) FROM stdin;
\.


--
-- Data for Name: contributor_affiliations; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.contributor_affiliations (ca_id, ca_domain, ca_start_date, ca_last_used, ca_affiliation, ca_active, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
1	samsung.com	1970-01-01	2018-08-01 18:37:54	Samsung	1	load	1.0	load	1970-01-01 00:00:00
2	linuxfoundation.org	1970-01-01	2018-08-01 18:37:54	Linux Foundation	1	load	1.0	load	1970-01-01 00:00:00
3	ibm.com	1970-01-01	2018-08-01 18:37:54	IBM	1	load	1.0	load	1970-01-01 00:00:00
8	walmart.com	1970-01-01	2018-09-01 06:00:00	Walmart	1	load	1.0	load	1970-01-01 00:00:00
9	exxonmobil.com	1970-01-01	2018-09-01 06:00:00	Exxon Mobil	1	load	1.0	load	1970-01-01 00:00:00
10	ge.com	1970-01-01	2018-09-01 06:00:00	General Electric	1	load	1.0	load	1970-01-01 00:00:00
11	dupont.com	1970-01-01	2018-09-01 06:00:00	DuPont	1	load	1.0	load	1970-01-01 00:00:00
12	avnet.com	1970-01-01	2018-09-01 06:00:00	Avnet	1	load	1.0	load	1970-01-01 00:00:00
13	macysinc.com	1970-01-01	2018-09-01 06:00:00	Macys	1	load	1.0	load	1970-01-01 00:00:00
14	enterpriseproducts.com	1970-01-01	2018-09-01 06:00:00	Enterprise Products Partners	1	load	1.0	load	1970-01-01 00:00:00
15	travelers.com	1970-01-01	2018-09-01 06:00:00	Travelers Cos.	1	load	1.0	load	1970-01-01 00:00:00
16	pmi.com	1970-01-01	2018-09-01 06:00:00	Philip Morris International	1	load	1.0	load	1970-01-01 00:00:00
17	riteaid.com	1970-01-01	2018-09-01 06:00:00	Rite Aid	1	load	1.0	load	1970-01-01 00:00:00
18	techdata.com	1970-01-01	2018-09-01 06:00:00	Tech Data	1	load	1.0	load	1970-01-01 00:00:00
25156	pivotal.io	1970-01-01	2020-03-25 00:30:57	VMware	1	Manual Entry	0.0.0	Gabe	2020-03-25 00:30:57
25157	vmware.com	1970-01-01	2020-03-25 00:33:35	VMware	1	Manual Entry	0.0.0	Gabe	2020-03-25 00:33:35
25158	rabbitmq.com	1970-01-01	2020-03-25 00:33:43	VMware	1	Manual Entry	0.0.0	Gabe	2020-03-25 00:33:43
25161	pivotallabs.com	1970-01-01	2020-03-25 00:43:53	VMware	1	Manual Entry	0.0.0	Gabe	2020-03-25 00:43:53
25162	cloudcredo.com	1970-01-01	2020-03-25 00:44:18	VMware	1	Manual Entry	0.0.0	Gabe	2020-03-25 00:44:18
25163	gopivotal.com	1970-01-01	2020-03-25 00:44:25	VMware	1	Manual Entry	0.0.0	Gabe	2020-03-25 00:44:25
25164	heptio.com	1970-01-01	2020-03-25 00:44:32	VMware	1	Manual Entry	0.0.0	Gabe	2020-03-25 00:44:32
19	aboutmcdonalds.com	1970-01-01	2018-09-01 06:00:00	McDonalds	1	load	1.0	load	1970-01-01 00:00:00
20	qualcomm.com	1970-01-01	2018-09-01 06:00:00	Qualcomm	1	load	1.0	load	1970-01-01 00:00:00
21	amerisourcebergen.com	1970-01-01	2018-09-01 06:00:00	AmerisourceBergen	1	load	1.0	load	1970-01-01 00:00:00
22	searsholdings.com	1970-01-01	2018-09-01 06:00:00	Sears Holdings	1	load	1.0	load	1970-01-01 00:00:00
23	capitalone.com	1970-01-01	2018-09-01 06:00:00	Capital One Financial	1	load	1.0	load	1970-01-01 00:00:00
24	emc.com	1970-01-01	2018-09-01 06:00:00	EMC	1	load	1.0	load	1970-01-01 00:00:00
25	usaa.com	1970-01-01	2018-09-01 06:00:00	USAA	1	load	1.0	load	1970-01-01 00:00:00
26	duke-energy.com	1970-01-01	2018-09-01 06:00:00	Duke Energy	1	load	1.0	load	1970-01-01 00:00:00
27	twc.com	1970-01-01	2018-09-01 06:00:00	Time Warner Cable	1	load	1.0	load	1970-01-01 00:00:00
28	halliburton.com	1970-01-01	2018-09-01 06:00:00	Halliburton	1	load	1.0	load	1970-01-01 00:00:00
29	northropgrumman.com	1970-01-01	2018-09-01 06:00:00	Northrop Grumman	1	load	1.0	load	1970-01-01 00:00:00
30	arrow.com	1970-01-01	2018-09-01 06:00:00	Arrow Electronics	1	load	1.0	load	1970-01-01 00:00:00
31	raytheon.com	1970-01-01	2018-09-01 06:00:00	Raytheon	1	load	1.0	load	1970-01-01 00:00:00
32	verizon.com	1970-01-01	2018-09-01 06:00:00	Verizon	1	load	1.0	load	1970-01-01 00:00:00
33	plainsallamerican.com	1970-01-01	2018-09-01 06:00:00	Plains GP Holdings	1	load	1.0	load	1970-01-01 00:00:00
34	usfoods.com	1970-01-01	2018-09-01 06:00:00	US Foods	1	load	1.0	load	1970-01-01 00:00:00
35	abbvie.com	1970-01-01	2018-09-01 06:00:00	AbbVie	1	load	1.0	load	1970-01-01 00:00:00
36	centene.com	1970-01-01	2018-09-01 06:00:00	Centene	1	load	1.0	load	1970-01-01 00:00:00
37	chs.net	1970-01-01	2018-09-01 06:00:00	Community Health Systems	1	load	1.0	load	1970-01-01 00:00:00
38	arconic.com	1970-01-01	2018-09-01 06:00:00	Arconic	1	load	1.0	load	1970-01-01 00:00:00
39	internationalpaper.com	1970-01-01	2018-09-01 06:00:00	International Paper	1	load	1.0	load	1970-01-01 00:00:00
40	emerson.com	1970-01-01	2018-09-01 06:00:00	Emerson Electric	1	load	1.0	load	1970-01-01 00:00:00
41	up.com	1970-01-01	2018-09-01 06:00:00	Union Pacific	1	load	1.0	load	1970-01-01 00:00:00
42	amgen.com	1970-01-01	2018-09-01 06:00:00	Amgen	1	load	1.0	load	1970-01-01 00:00:00
43	chevron.com	1970-01-01	2018-09-01 06:00:00	Chevron	1	load	1.0	load	1970-01-01 00:00:00
44	usbank.com	1970-01-01	2018-09-01 06:00:00	U.S. Bancorp	1	load	1.0	load	1970-01-01 00:00:00
45	staples.com	1970-01-01	2018-09-01 06:00:00	Staples	1	load	1.0	load	1970-01-01 00:00:00
46	danaher.com	1970-01-01	2018-09-01 06:00:00	Danaher	1	load	1.0	load	1970-01-01 00:00:00
47	whirlpoolcorp.com	1970-01-01	2018-09-01 06:00:00	Whirlpool	1	load	1.0	load	1970-01-01 00:00:00
48	aflac.com	1970-01-01	2018-09-01 06:00:00	Aflac	1	load	1.0	load	1970-01-01 00:00:00
49	autonation.com	1970-01-01	2018-09-01 06:00:00	AutoNation	1	load	1.0	load	1970-01-01 00:00:00
50	progressive.com	1970-01-01	2018-09-01 06:00:00	Progressive	1	load	1.0	load	1970-01-01 00:00:00
51	abbott.com	1970-01-01	2018-09-01 06:00:00	Abbott Laboratories	1	load	1.0	load	1970-01-01 00:00:00
52	dollargeneral.com	1970-01-01	2018-09-01 06:00:00	Dollar General	1	load	1.0	load	1970-01-01 00:00:00
53	tenethealth.com	1970-01-01	2018-09-01 06:00:00	Tenet Healthcare	1	load	1.0	load	1970-01-01 00:00:00
54	costco.com	1970-01-01	2018-09-01 06:00:00	Costco	1	load	1.0	load	1970-01-01 00:00:00
55	lilly.com	1970-01-01	2018-09-01 06:00:00	Eli Lilly	1	load	1.0	load	1970-01-01 00:00:00
56	southwest.com	1970-01-01	2018-09-01 06:00:00	Southwest Airlines	1	load	1.0	load	1970-01-01 00:00:00
57	penskeautomotive.com	1970-01-01	2018-09-01 06:00:00	Penske Automotive Group	1	load	1.0	load	1970-01-01 00:00:00
58	manpowergroup.com	1970-01-01	2018-09-01 06:00:00	ManpowerGroup	1	load	1.0	load	1970-01-01 00:00:00
59	kohlscorporation.com	1970-01-01	2018-09-01 06:00:00	Kohls	1	load	1.0	load	1970-01-01 00:00:00
60	starbucks.com	1970-01-01	2018-09-01 06:00:00	Starbucks	1	load	1.0	load	1970-01-01 00:00:00
61	paccar.com	1970-01-01	2018-09-01 06:00:00	Paccar	1	load	1.0	load	1970-01-01 00:00:00
62	cummins.com	1970-01-01	2018-09-01 06:00:00	Cummins	1	load	1.0	load	1970-01-01 00:00:00
63	altria.com	1970-01-01	2018-09-01 06:00:00	Altria Group	1	load	1.0	load	1970-01-01 00:00:00
64	xerox.com	1970-01-01	2018-09-01 06:00:00	Xerox	1	load	1.0	load	1970-01-01 00:00:00
65	fanniemae.com	1970-01-01	2018-09-01 06:00:00	Fannie Mae	1	load	1.0	load	1970-01-01 00:00:00
66	kimberly-clark.com	1970-01-01	2018-09-01 06:00:00	Kimberly-Clark	1	load	1.0	load	1970-01-01 00:00:00
67	thehartford.com	1970-01-01	2018-09-01 06:00:00	Hartford Financial Services Group	1	load	1.0	load	1970-01-01 00:00:00
68	kraftheinzcompany.com	1970-01-01	2018-09-01 06:00:00	Kraft Heinz	1	load	1.0	load	1970-01-01 00:00:00
69	lear.com	1970-01-01	2018-09-01 06:00:00	Lear	1	load	1.0	load	1970-01-01 00:00:00
70	fluor.com	1970-01-01	2018-09-01 06:00:00	Fluor	1	load	1.0	load	1970-01-01 00:00:00
71	aecom.com	1970-01-01	2018-09-01 06:00:00	AECOM	1	load	1.0	load	1970-01-01 00:00:00
72	facebook.com	1970-01-01	2018-09-01 06:00:00	Facebook	1	load	1.0	load	1970-01-01 00:00:00
73	jabil.com	1970-01-01	2018-09-01 06:00:00	Jabil Circuit	1	load	1.0	load	1970-01-01 00:00:00
74	centurylink.com	1970-01-01	2018-09-01 06:00:00	CenturyLink	1	load	1.0	load	1970-01-01 00:00:00
75	supervalu.com	1970-01-01	2018-09-01 06:00:00	Supervalu	1	load	1.0	load	1970-01-01 00:00:00
76	thekrogerco.com	1970-01-01	2018-09-01 06:00:00	Kroger	1	load	1.0	load	1970-01-01 00:00:00
77	generalmills.com	1970-01-01	2018-09-01 06:00:00	General Mills	1	load	1.0	load	1970-01-01 00:00:00
78	southerncompany.com	1970-01-01	2018-09-01 06:00:00	Southern	1	load	1.0	load	1970-01-01 00:00:00
79	nexteraenergy.com	1970-01-01	2018-09-01 06:00:00	NextEra Energy	1	load	1.0	load	1970-01-01 00:00:00
80	thermofisher.com	1970-01-01	2018-09-01 06:00:00	Thermo Fisher Scientific	1	load	1.0	load	1970-01-01 00:00:00
81	aep.com	1970-01-01	2018-09-01 06:00:00	American Electric Power	1	load	1.0	load	1970-01-01 00:00:00
82	pge.com	1970-01-01	2018-09-01 06:00:00	PG&E Corp.	1	load	1.0	load	1970-01-01 00:00:00
83	nglenergypartners.com	1970-01-01	2018-09-01 06:00:00	NGL Energy Partners	1	load	1.0	load	1970-01-01 00:00:00
84	bms.com	1970-01-01	2018-09-01 06:00:00	Bristol-Myers Squibb	1	load	1.0	load	1970-01-01 00:00:00
85	goodyear.com	1970-01-01	2018-09-01 06:00:00	Goodyear Tire & Rubber	1	load	1.0	load	1970-01-01 00:00:00
86	nucor.com	1970-01-01	2018-09-01 06:00:00	Nucor	1	load	1.0	load	1970-01-01 00:00:00
87	amazon.com	1970-01-01	2018-09-01 06:00:00	Amazon.com	1	load	1.0	load	1970-01-01 00:00:00
88	pnc.com	1970-01-01	2018-09-01 06:00:00	PNC Financial Services Group	1	load	1.0	load	1970-01-01 00:00:00
89	healthnet.com	1970-01-01	2018-09-01 06:00:00	Health Net	1	load	1.0	load	1970-01-01 00:00:00
90	micron.com	1970-01-01	2018-09-01 06:00:00	Micron Technology	1	load	1.0	load	1970-01-01 00:00:00
91	colgatepalmolive.com	1970-01-01	2018-09-01 06:00:00	Colgate-Palmolive	1	load	1.0	load	1970-01-01 00:00:00
92	fcx.com	1970-01-01	2018-09-01 06:00:00	Freeport-McMoRan	1	load	1.0	load	1970-01-01 00:00:00
93	conagrafoods.com	1970-01-01	2018-09-01 06:00:00	ConAgra Foods	1	load	1.0	load	1970-01-01 00:00:00
94	gapinc.com	1970-01-01	2018-09-01 06:00:00	Gap	1	load	1.0	load	1970-01-01 00:00:00
95	bakerhughes.com	1970-01-01	2018-09-01 06:00:00	Baker Hughes	1	load	1.0	load	1970-01-01 00:00:00
96	bnymellon.com	1970-01-01	2018-09-01 06:00:00	Bank of New York Mellon Corp.	1	load	1.0	load	1970-01-01 00:00:00
97	dollartree.com	1970-01-01	2018-09-01 06:00:00	Dollar Tree	1	load	1.0	load	1970-01-01 00:00:00
98	walgreensbootsalliance.com	1970-01-01	2018-09-01 06:00:00	Walgreens	1	load	1.0	load	1970-01-01 00:00:00
99	wholefoodsmarket.com	1970-01-01	2018-09-01 06:00:00	Whole Foods Market	1	load	1.0	load	1970-01-01 00:00:00
100	ppg.com	1970-01-01	2018-09-01 06:00:00	PPG Industries	1	load	1.0	load	1970-01-01 00:00:00
101	genpt.com	1970-01-01	2018-09-01 06:00:00	Genuine Parts	1	load	1.0	load	1970-01-01 00:00:00
102	ielp.com	1970-01-01	2018-09-01 06:00:00	Icahn Enterprises	1	load	1.0	load	1970-01-01 00:00:00
103	pfgc.com	1970-01-01	2018-09-01 06:00:00	Performance Food Group	1	load	1.0	load	1970-01-01 00:00:00
104	omnicomgroup.com	1970-01-01	2018-09-01 06:00:00	Omnicom Group	1	load	1.0	load	1970-01-01 00:00:00
105	dish.com	1970-01-01	2018-09-01 06:00:00	DISH Network	1	load	1.0	load	1970-01-01 00:00:00
106	firstenergycorp.com	1970-01-01	2018-09-01 06:00:00	FirstEnergy	1	load	1.0	load	1970-01-01 00:00:00
107	monsanto.com	1970-01-01	2018-09-01 06:00:00	Monsanto	1	load	1.0	load	1970-01-01 00:00:00
108	aes.com	1970-01-01	2018-09-01 06:00:00	AES	1	load	1.0	load	1970-01-01 00:00:00
109	hp.com	1970-01-01	2018-09-01 06:00:00	HP	1	load	1.0	load	1970-01-01 00:00:00
110	carmax.com	1970-01-01	2018-09-01 06:00:00	CarMax	1	load	1.0	load	1970-01-01 00:00:00
111	nov.com	1970-01-01	2018-09-01 06:00:00	National Oilwell Varco	1	load	1.0	load	1970-01-01 00:00:00
112	nrgenergy.com	1970-01-01	2018-09-01 06:00:00	NRG Energy	1	load	1.0	load	1970-01-01 00:00:00
113	westerndigital.com	1970-01-01	2018-09-01 06:00:00	Western Digital	1	load	1.0	load	1970-01-01 00:00:00
114	marriott.com	1970-01-01	2018-09-01 06:00:00	Marriott International	1	load	1.0	load	1970-01-01 00:00:00
115	officedepot.com	1970-01-01	2018-09-01 06:00:00	Office Depot	1	load	1.0	load	1970-01-01 00:00:00
116	nordstrom.com	1970-01-01	2018-09-01 06:00:00	Nordstrom	1	load	1.0	load	1970-01-01 00:00:00
117	kindermorgan.com	1970-01-01	2018-09-01 06:00:00	Kinder Morgan	1	load	1.0	load	1970-01-01 00:00:00
118	aramark.com	1970-01-01	2018-09-01 06:00:00	Aramark	1	load	1.0	load	1970-01-01 00:00:00
119	davita.com	1970-01-01	2018-09-01 06:00:00	DaVita	1	load	1.0	load	1970-01-01 00:00:00
120	apple.com	1970-01-01	2018-09-01 06:00:00	Apple	1	load	1.0	load	1970-01-01 00:00:00
121	cardinal.com	1970-01-01	2018-09-01 06:00:00	Cardinal Health	1	load	1.0	load	1970-01-01 00:00:00
122	molinahealthcare.com	1970-01-01	2018-09-01 06:00:00	Molina Healthcare	1	load	1.0	load	1970-01-01 00:00:00
123	wellcare.com	1970-01-01	2018-09-01 06:00:00	WellCare Health Plans	1	load	1.0	load	1970-01-01 00:00:00
124	cbscorporation.com	1970-01-01	2018-09-01 06:00:00	CBS	1	load	1.0	load	1970-01-01 00:00:00
125	visa.com	1970-01-01	2018-09-01 06:00:00	Visa	1	load	1.0	load	1970-01-01 00:00:00
126	lfg.com	1970-01-01	2018-09-01 06:00:00	Lincoln National	1	load	1.0	load	1970-01-01 00:00:00
127	ecolab.com	1970-01-01	2018-09-01 06:00:00	Ecolab	1	load	1.0	load	1970-01-01 00:00:00
128	kelloggcompany.com	1970-01-01	2018-09-01 06:00:00	Kellogg	1	load	1.0	load	1970-01-01 00:00:00
129	chrobinson.com	1970-01-01	2018-09-01 06:00:00	C.H. Robinson Worldwide	1	load	1.0	load	1970-01-01 00:00:00
130	textron.com	1970-01-01	2018-09-01 06:00:00	Textron	1	load	1.0	load	1970-01-01 00:00:00
131	loews.com	1970-01-01	2018-09-01 06:00:00	Loews	1	load	1.0	load	1970-01-01 00:00:00
132	express-scripts.com	1970-01-01	2018-09-01 06:00:00	Express Scripts Holding	1	load	1.0	load	1970-01-01 00:00:00
133	itw.com	1970-01-01	2018-09-01 06:00:00	Illinois Tool Works	1	load	1.0	load	1970-01-01 00:00:00
134	synnex.com	1970-01-01	2018-09-01 06:00:00	Synnex	1	load	1.0	load	1970-01-01 00:00:00
135	viacom.com	1970-01-01	2018-09-01 06:00:00	Viacom	1	load	1.0	load	1970-01-01 00:00:00
136	hollyfrontier.com	1970-01-01	2018-09-01 06:00:00	HollyFrontier	1	load	1.0	load	1970-01-01 00:00:00
137	landolakesinc.com	1970-01-01	2018-09-01 06:00:00	Land O Lakes	1	load	1.0	load	1970-01-01 00:00:00
138	devonenergy.com	1970-01-01	2018-09-01 06:00:00	Devon Energy	1	load	1.0	load	1970-01-01 00:00:00
139	pbfenergy.com	1970-01-01	2018-09-01 06:00:00	PBF Energy	1	load	1.0	load	1970-01-01 00:00:00
140	yum.com	1970-01-01	2018-09-01 06:00:00	Yum Brands	1	load	1.0	load	1970-01-01 00:00:00
141	ti.com	1970-01-01	2018-09-01 06:00:00	Texas Instruments	1	load	1.0	load	1970-01-01 00:00:00
142	cdw.com	1970-01-01	2018-09-01 06:00:00	CDW	1	load	1.0	load	1970-01-01 00:00:00
143	jpmorganchase.com	1970-01-01	2018-09-01 06:00:00	J.P. Morgan Chase	1	load	1.0	load	1970-01-01 00:00:00
144	wm.com	1970-01-01	2018-09-01 06:00:00	Waste Management	1	load	1.0	load	1970-01-01 00:00:00
145	mmc.com	1970-01-01	2018-09-01 06:00:00	Marsh & McLennan	1	load	1.0	load	1970-01-01 00:00:00
146	chk.com	1970-01-01	2018-09-01 06:00:00	Chesapeake Energy	1	load	1.0	load	1970-01-01 00:00:00
147	parker.com	1970-01-01	2018-09-01 06:00:00	Parker-Hannifin	1	load	1.0	load	1970-01-01 00:00:00
148	oxy.com	1970-01-01	2018-09-01 06:00:00	Occidental Petroleum	1	load	1.0	load	1970-01-01 00:00:00
149	guardianlife.com	1970-01-01	2018-09-01 06:00:00	Guardian Life Ins. Co. of America	1	load	1.0	load	1970-01-01 00:00:00
150	farmers.com	1970-01-01	2018-09-01 06:00:00	Farmers Insurance Exchange	1	load	1.0	load	1970-01-01 00:00:00
151	jcpenney.com	1970-01-01	2018-09-01 06:00:00	J.C. Penney	1	load	1.0	load	1970-01-01 00:00:00
152	conedison.com	1970-01-01	2018-09-01 06:00:00	Consolidated Edison	1	load	1.0	load	1970-01-01 00:00:00
153	cognizant.com	1970-01-01	2018-09-01 06:00:00	Cognizant Technology Solutions	1	load	1.0	load	1970-01-01 00:00:00
154	boeing.com	1970-01-01	2018-09-01 06:00:00	Boeing	1	load	1.0	load	1970-01-01 00:00:00
155	vfc.com	1970-01-01	2018-09-01 06:00:00	VF	1	load	1.0	load	1970-01-01 00:00:00
156	ameriprise.com	1970-01-01	2018-09-01 06:00:00	Ameriprise Financial	1	load	1.0	load	1970-01-01 00:00:00
157	csc.com	1970-01-01	2018-09-01 06:00:00	Computer Sciences	1	load	1.0	load	1970-01-01 00:00:00
158	lb.com	1970-01-01	2018-09-01 06:00:00	L Brands	1	load	1.0	load	1970-01-01 00:00:00
159	jacobs.com	1970-01-01	2018-09-01 06:00:00	Jacobs Engineering Group	1	load	1.0	load	1970-01-01 00:00:00
160	principal.com	1970-01-01	2018-09-01 06:00:00	Principal Financial Group	1	load	1.0	load	1970-01-01 00:00:00
161	rossstores.com	1970-01-01	2018-09-01 06:00:00	Ross Stores	1	load	1.0	load	1970-01-01 00:00:00
162	bedbathandbeyond.com	1970-01-01	2018-09-01 06:00:00	Bed Bath & Beyond	1	load	1.0	load	1970-01-01 00:00:00
163	csx.com	1970-01-01	2018-09-01 06:00:00	CSX	1	load	1.0	load	1970-01-01 00:00:00
164	toysrusinc.com	1970-01-01	2018-09-01 06:00:00	Toys \\"R\\" Us	1	load	1.0	load	1970-01-01 00:00:00
165	microsoft.com	1970-01-01	2018-09-01 06:00:00	Microsoft	1	load	1.0	load	1970-01-01 00:00:00
166	sands.com	1970-01-01	2018-09-01 06:00:00	Las Vegas Sands	1	load	1.0	load	1970-01-01 00:00:00
167	leucadia.com	1970-01-01	2018-09-01 06:00:00	Leucadia National	1	load	1.0	load	1970-01-01 00:00:00
168	dom.com	1970-01-01	2018-09-01 06:00:00	Dominion Resources	1	load	1.0	load	1970-01-01 00:00:00
169	ussteel.com	1970-01-01	2018-09-01 06:00:00	United States Steel	1	load	1.0	load	1970-01-01 00:00:00
170	l-3com.com	1970-01-01	2018-09-01 06:00:00	L-3 Communications	1	load	1.0	load	1970-01-01 00:00:00
171	edisoninvestor.com	1970-01-01	2018-09-01 06:00:00	Edison International	1	load	1.0	load	1970-01-01 00:00:00
172	entergy.com	1970-01-01	2018-09-01 06:00:00	Entergy	1	load	1.0	load	1970-01-01 00:00:00
173	adp.com	1970-01-01	2018-09-01 06:00:00	ADP	1	load	1.0	load	1970-01-01 00:00:00
174	firstdata.com	1970-01-01	2018-09-01 06:00:00	First Data	1	load	1.0	load	1970-01-01 00:00:00
175	blackrock.com	1970-01-01	2018-09-01 06:00:00	BlackRock	1	load	1.0	load	1970-01-01 00:00:00
176	bankofamerica.com	1970-01-01	2018-09-01 06:00:00	Bank of America Corp.	1	load	1.0	load	1970-01-01 00:00:00
177	westrock.com	1970-01-01	2018-09-01 06:00:00	WestRock	1	load	1.0	load	1970-01-01 00:00:00
178	voya.com	1970-01-01	2018-09-01 06:00:00	Voya Financial	1	load	1.0	load	1970-01-01 00:00:00
179	sherwin.com	1970-01-01	2018-09-01 06:00:00	Sherwin-Williams	1	load	1.0	load	1970-01-01 00:00:00
180	hiltonworldwide.com	1970-01-01	2018-09-01 06:00:00	Hilton Worldwide Holdings	1	load	1.0	load	1970-01-01 00:00:00
181	rrdonnelley.com	1970-01-01	2018-09-01 06:00:00	R.R. Donnelley & Sons	1	load	1.0	load	1970-01-01 00:00:00
182	stanleyblackanddecker.com	1970-01-01	2018-09-01 06:00:00	Stanley Black & Decker	1	load	1.0	load	1970-01-01 00:00:00
183	xcelenergy.com	1970-01-01	2018-09-01 06:00:00	Xcel Energy	1	load	1.0	load	1970-01-01 00:00:00
184	corporate.murphyusa.com	1970-01-01	2018-09-01 06:00:00	Murphy USA	1	load	1.0	load	1970-01-01 00:00:00
185	cbre.com	1970-01-01	2018-09-01 06:00:00	CBRE Group	1	load	1.0	load	1970-01-01 00:00:00
186	drhorton.com	1970-01-01	2018-09-01 06:00:00	D.R. Horton	1	load	1.0	load	1970-01-01 00:00:00
187	wellsfargo.com	1970-01-01	2018-09-01 06:00:00	Wells Fargo	1	load	1.0	load	1970-01-01 00:00:00
188	elcompanies.com	1970-01-01	2018-09-01 06:00:00	Estee Lauder	1	load	1.0	load	1970-01-01 00:00:00
189	praxair.com	1970-01-01	2018-09-01 06:00:00	Praxair	1	load	1.0	load	1970-01-01 00:00:00
190	biogen.com	1970-01-01	2018-09-01 06:00:00	Biogen	1	load	1.0	load	1970-01-01 00:00:00
191	statestreet.com	1970-01-01	2018-09-01 06:00:00	State Street Corp.	1	load	1.0	load	1970-01-01 00:00:00
192	unum.com	1970-01-01	2018-09-01 06:00:00	Unum Group	1	load	1.0	load	1970-01-01 00:00:00
193	reynoldsamerican.com	1970-01-01	2018-09-01 06:00:00	Reynolds American	1	load	1.0	load	1970-01-01 00:00:00
194	group1auto.com	1970-01-01	2018-09-01 06:00:00	Group 1 Automotive	1	load	1.0	load	1970-01-01 00:00:00
195	henryschein.com	1970-01-01	2018-09-01 06:00:00	Henry Schein	1	load	1.0	load	1970-01-01 00:00:00
196	hertz.com	1970-01-01	2018-09-01 06:00:00	Hertz Global Holdings	1	load	1.0	load	1970-01-01 00:00:00
197	nscorp.com	1970-01-01	2018-09-01 06:00:00	Norfolk Southern	1	load	1.0	load	1970-01-01 00:00:00
198	homedepot.com	1970-01-01	2018-09-01 06:00:00	Home Depot	1	load	1.0	load	1970-01-01 00:00:00
199	rgare.com	1970-01-01	2018-09-01 06:00:00	Reinsurance Group of America	1	load	1.0	load	1970-01-01 00:00:00
200	pseg.com	1970-01-01	2018-09-01 06:00:00	Public Service Enterprise Group	1	load	1.0	load	1970-01-01 00:00:00
201	bbt.com	1970-01-01	2018-09-01 06:00:00	BB&T Corp.	1	load	1.0	load	1970-01-01 00:00:00
202	dteenergy.com	1970-01-01	2018-09-01 06:00:00	DTE Energy	1	load	1.0	load	1970-01-01 00:00:00
203	assurant.com	1970-01-01	2018-09-01 06:00:00	Assurant	1	load	1.0	load	1970-01-01 00:00:00
204	globalp.com	1970-01-01	2018-09-01 06:00:00	Global Partners	1	load	1.0	load	1970-01-01 00:00:00
205	huntsman.com	1970-01-01	2018-09-01 06:00:00	Huntsman	1	load	1.0	load	1970-01-01 00:00:00
206	bd.com	1970-01-01	2018-09-01 06:00:00	Becton Dickinson	1	load	1.0	load	1970-01-01 00:00:00
207	sempra.com	1970-01-01	2018-09-01 06:00:00	Sempra Energy	1	load	1.0	load	1970-01-01 00:00:00
208	autozone.com	1970-01-01	2018-09-01 06:00:00	AutoZone	1	load	1.0	load	1970-01-01 00:00:00
209	citigroup.com	1970-01-01	2018-09-01 06:00:00	Citigroup	1	load	1.0	load	1970-01-01 00:00:00
210	navistar.com	1970-01-01	2018-09-01 06:00:00	Navistar International	1	load	1.0	load	1970-01-01 00:00:00
211	precast.com	1970-01-01	2018-09-01 06:00:00	Precision Castparts	1	load	1.0	load	1970-01-01 00:00:00
212	discoverfinancial.com	1970-01-01	2018-09-01 06:00:00	Discover Financial Services	1	load	1.0	load	1970-01-01 00:00:00
213	libertyinteractive.com	1970-01-01	2018-09-01 06:00:00	Liberty Interactive	1	load	1.0	load	1970-01-01 00:00:00
214	grainger.com	1970-01-01	2018-09-01 06:00:00	W.W. Grainger	1	load	1.0	load	1970-01-01 00:00:00
215	baxter.com	1970-01-01	2018-09-01 06:00:00	Baxter International	1	load	1.0	load	1970-01-01 00:00:00
216	stryker.com	1970-01-01	2018-09-01 06:00:00	Stryker	1	load	1.0	load	1970-01-01 00:00:00
217	airproducts.com	1970-01-01	2018-09-01 06:00:00	Air Products & Chemicals	1	load	1.0	load	1970-01-01 00:00:00
218	wnr.com	1970-01-01	2018-09-01 06:00:00	Western Refining	1	load	1.0	load	1970-01-01 00:00:00
219	uhsinc.com	1970-01-01	2018-09-01 06:00:00	Universal Health Services	1	load	1.0	load	1970-01-01 00:00:00
220	phillips66.com	1970-01-01	2018-09-01 06:00:00	Phillips 66	1	load	1.0	load	1970-01-01 00:00:00
221	owens-minor.com	1970-01-01	2018-09-01 06:00:00	Owens & Minor	1	load	1.0	load	1970-01-01 00:00:00
222	charter.com	1970-01-01	2018-09-01 06:00:00	Charter Communications	1	load	1.0	load	1970-01-01 00:00:00
223	advanceautoparts.com	1970-01-01	2018-09-01 06:00:00	Advance Auto Parts	1	load	1.0	load	1970-01-01 00:00:00
224	mastercard.com	1970-01-01	2018-09-01 06:00:00	MasterCard	1	load	1.0	load	1970-01-01 00:00:00
225	appliedmaterials.com	1970-01-01	2018-09-01 06:00:00	Applied Materials	1	load	1.0	load	1970-01-01 00:00:00
226	eastman.com	1970-01-01	2018-09-01 06:00:00	Eastman Chemical	1	load	1.0	load	1970-01-01 00:00:00
227	sonicautomotive.com	1970-01-01	2018-09-01 06:00:00	Sonic Automotive	1	load	1.0	load	1970-01-01 00:00:00
228	ally.com	1970-01-01	2018-09-01 06:00:00	Ally Financial	1	load	1.0	load	1970-01-01 00:00:00
229	cstbrands.com	1970-01-01	2018-09-01 06:00:00	CST Brands	1	load	1.0	load	1970-01-01 00:00:00
230	ebay.com	1970-01-01	2018-09-01 06:00:00	eBay	1	load	1.0	load	1970-01-01 00:00:00
231	berkshirehathaway.com	1970-01-01	2018-09-01 06:00:00	Berkshire Hathaway	1	load	1.0	load	1970-01-01 00:00:00
233	lennar.com	1970-01-01	2018-09-01 06:00:00	Lennar	1	load	1.0	load	1970-01-01 00:00:00
234	gamestopcorp.com	1970-01-01	2018-09-01 06:00:00	GameStop	1	load	1.0	load	1970-01-01 00:00:00
235	rsac.com	1970-01-01	2018-09-01 06:00:00	Reliance Steel & Aluminum	1	load	1.0	load	1970-01-01 00:00:00
236	hormelfoods.com	1970-01-01	2018-09-01 06:00:00	Hormel Foods	1	load	1.0	load	1970-01-01 00:00:00
237	celgene.com	1970-01-01	2018-09-01 06:00:00	Celgene	1	load	1.0	load	1970-01-01 00:00:00
238	genworth.com	1970-01-01	2018-09-01 06:00:00	Genworth Financial	1	load	1.0	load	1970-01-01 00:00:00
239	paypal.com	1970-01-01	2018-09-01 06:00:00	PayPal Holdings	1	load	1.0	load	1970-01-01 00:00:00
240	pricelinegroup.com	1970-01-01	2018-09-01 06:00:00	Priceline Group	1	load	1.0	load	1970-01-01 00:00:00
241	mgmresorts.com	1970-01-01	2018-09-01 06:00:00	MGM Resorts International	1	load	1.0	load	1970-01-01 00:00:00
242	autoliv.com	1970-01-01	2018-09-01 06:00:00	Autoliv	1	load	1.0	load	1970-01-01 00:00:00
243	valero.com	1970-01-01	2018-09-01 06:00:00	Valero Energy	1	load	1.0	load	1970-01-01 00:00:00
244	fnf.com	1970-01-01	2018-09-01 06:00:00	Fidelity National Financial	1	load	1.0	load	1970-01-01 00:00:00
245	republicservices.com	1970-01-01	2018-09-01 06:00:00	Republic Services	1	load	1.0	load	1970-01-01 00:00:00
246	corning.com	1970-01-01	2018-09-01 06:00:00	Corning	1	load	1.0	load	1970-01-01 00:00:00
247	kiewit.com	1970-01-01	2018-09-01 06:00:00	Peter Kiewit Sons	1	load	1.0	load	1970-01-01 00:00:00
248	univar.com	1970-01-01	2018-09-01 06:00:00	Univar	1	load	1.0	load	1970-01-01 00:00:00
249	mosaicco.com	1970-01-01	2018-09-01 06:00:00	Mosaic	1	load	1.0	load	1970-01-01 00:00:00
250	core-mark.com	1970-01-01	2018-09-01 06:00:00	Core-Mark Holding	1	load	1.0	load	1970-01-01 00:00:00
251	thrivent.com	1970-01-01	2018-09-01 06:00:00	Thrivent Financial for Lutherans	1	load	1.0	load	1970-01-01 00:00:00
252	c-a-m.com	1970-01-01	2018-09-01 06:00:00	Cameron International	1	load	1.0	load	1970-01-01 00:00:00
253	hdsupply.com	1970-01-01	2018-09-01 06:00:00	HD Supply Holdings	1	load	1.0	load	1970-01-01 00:00:00
254	antheminc.com	1970-01-01	2018-09-01 06:00:00	Anthem	1	load	1.0	load	1970-01-01 00:00:00
255	crowncork.com	1970-01-01	2018-09-01 06:00:00	Crown Holdings	1	load	1.0	load	1970-01-01 00:00:00
256	eogresources.com	1970-01-01	2018-09-01 06:00:00	EOG Resources	1	load	1.0	load	1970-01-01 00:00:00
257	veritivcorp.com	1970-01-01	2018-09-01 06:00:00	Veritiv	1	load	1.0	load	1970-01-01 00:00:00
258	anadarko.com	1970-01-01	2018-09-01 06:00:00	Anadarko Petroleum	1	load	1.0	load	1970-01-01 00:00:00
259	labcorp.com	1970-01-01	2018-09-01 06:00:00	Laboratory Corp. of America	1	load	1.0	load	1970-01-01 00:00:00
260	pacificlife.com	1970-01-01	2018-09-01 06:00:00	Pacific Life	1	load	1.0	load	1970-01-01 00:00:00
261	newscorp.com	1970-01-01	2018-09-01 06:00:00	News Corp.	1	load	1.0	load	1970-01-01 00:00:00
262	jarden.com	1970-01-01	2018-09-01 06:00:00	Jarden	1	load	1.0	load	1970-01-01 00:00:00
263	suntrust.com	1970-01-01	2018-09-01 06:00:00	SunTrust Banks	1	load	1.0	load	1970-01-01 00:00:00
264	avisbudgetgroup.com	1970-01-01	2018-09-01 06:00:00	Avis Budget Group	1	load	1.0	load	1970-01-01 00:00:00
265	pg.com	1970-01-01	2018-09-01 06:00:00	Procter & Gamble	1	load	1.0	load	1970-01-01 00:00:00
266	broadcom.com	1970-01-01	2018-09-01 06:00:00	Broadcom	1	load	1.0	load	1970-01-01 00:00:00
267	amfam.com	1970-01-01	2018-09-01 06:00:00	American Family Insurance Group	1	load	1.0	load	1970-01-01 00:00:00
268	level3.com	1970-01-01	2018-09-01 06:00:00	Level 3 Communications	1	load	1.0	load	1970-01-01 00:00:00
269	tenneco.com	1970-01-01	2018-09-01 06:00:00	Tenneco	1	load	1.0	load	1970-01-01 00:00:00
270	unfi.com	1970-01-01	2018-09-01 06:00:00	United Natural Foods	1	load	1.0	load	1970-01-01 00:00:00
271	deanfoods.com	1970-01-01	2018-09-01 06:00:00	Dean Foods	1	load	1.0	load	1970-01-01 00:00:00
272	campbellsoupcompany.com	1970-01-01	2018-09-01 06:00:00	Campbell Soup	1	load	1.0	load	1970-01-01 00:00:00
273	mohawkind.com	1970-01-01	2018-09-01 06:00:00	Mohawk Industries	1	load	1.0	load	1970-01-01 00:00:00
274	borgwarner.com	1970-01-01	2018-09-01 06:00:00	BorgWarner	1	load	1.0	load	1970-01-01 00:00:00
275	pvh.com	1970-01-01	2018-09-01 06:00:00	PVH	1	load	1.0	load	1970-01-01 00:00:00
276	statefarm.com	1970-01-01	2018-09-01 06:00:00	State Farm Insurance Cos.	1	load	1.0	load	1970-01-01 00:00:00
277	ball.com	1970-01-01	2018-09-01 06:00:00	Ball	1	load	1.0	load	1970-01-01 00:00:00
278	oreillyauto.com	1970-01-01	2018-09-01 06:00:00	O Reilly Automotive	1	load	1.0	load	1970-01-01 00:00:00
279	eversource.com	1970-01-01	2018-09-01 06:00:00	Eversource Energy	1	load	1.0	load	1970-01-01 00:00:00
280	franklinresources.com	1970-01-01	2018-09-01 06:00:00	Franklin Resources	1	load	1.0	load	1970-01-01 00:00:00
281	masco.com	1970-01-01	2018-09-01 06:00:00	Masco	1	load	1.0	load	1970-01-01 00:00:00
282	lithia.com	1970-01-01	2018-09-01 06:00:00	Lithia Motors	1	load	1.0	load	1970-01-01 00:00:00
283	kkr.com	1970-01-01	2018-09-01 06:00:00	KKR	1	load	1.0	load	1970-01-01 00:00:00
284	oneok.com	1970-01-01	2018-09-01 06:00:00	Oneok	1	load	1.0	load	1970-01-01 00:00:00
285	newmont.com	1970-01-01	2018-09-01 06:00:00	Newmont Mining	1	load	1.0	load	1970-01-01 00:00:00
286	pplweb.com	1970-01-01	2018-09-01 06:00:00	PPL	1	load	1.0	load	1970-01-01 00:00:00
287	google.com	1970-01-01	2018-09-01 06:00:00	Alphabet	1	load	1.0	load	1970-01-01 00:00:00
288	spartannash.com	1970-01-01	2018-09-01 06:00:00	SpartanNash	1	load	1.0	load	1970-01-01 00:00:00
289	quantaservices.com	1970-01-01	2018-09-01 06:00:00	Quanta Services	1	load	1.0	load	1970-01-01 00:00:00
290	xpo.com	1970-01-01	2018-09-01 06:00:00	XPO Logistics	1	load	1.0	load	1970-01-01 00:00:00
291	ralphlauren.com	1970-01-01	2018-09-01 06:00:00	Ralph Lauren	1	load	1.0	load	1970-01-01 00:00:00
292	interpublic.com	1970-01-01	2018-09-01 06:00:00	Interpublic Group	1	load	1.0	load	1970-01-01 00:00:00
293	steeldynamics.com	1970-01-01	2018-09-01 06:00:00	Steel Dynamics	1	load	1.0	load	1970-01-01 00:00:00
294	wesco.com	1970-01-01	2018-09-01 06:00:00	WESCO International	1	load	1.0	load	1970-01-01 00:00:00
295	questdiagnostics.com	1970-01-01	2018-09-01 06:00:00	Quest Diagnostics	1	load	1.0	load	1970-01-01 00:00:00
296	bostonscientific.com	1970-01-01	2018-09-01 06:00:00	Boston Scientific	1	load	1.0	load	1970-01-01 00:00:00
297	agcocorp.com	1970-01-01	2018-09-01 06:00:00	AGCO	1	load	1.0	load	1970-01-01 00:00:00
298	comcastcorporation.com	1970-01-01	2018-09-01 06:00:00	Comcast	1	load	1.0	load	1970-01-01 00:00:00
299	footlocker-inc.com	1970-01-01	2018-09-01 06:00:00	Foot Locker	1	load	1.0	load	1970-01-01 00:00:00
300	thehersheycompany.com	1970-01-01	2018-09-01 06:00:00	Hershey	1	load	1.0	load	1970-01-01 00:00:00
450	nvrinc.com	1970-01-01	2018-09-01 06:00:00	NVR	1	load	1.0	load	1970-01-01 00:00:00
301	centerpointenergy.com	1970-01-01	2018-09-01 06:00:00	CenterPoint Energy	1	load	1.0	load	1970-01-01 00:00:00
302	williams.com	1970-01-01	2018-09-01 06:00:00	Williams	1	load	1.0	load	1970-01-01 00:00:00
303	dickssportinggoods.com	1970-01-01	2018-09-01 06:00:00	Dicks Sporting Goods	1	load	1.0	load	1970-01-01 00:00:00
304	livenation.com	1970-01-01	2018-09-01 06:00:00	Live Nation Entertainment	1	load	1.0	load	1970-01-01 00:00:00
305	mutualofomaha.com	1970-01-01	2018-09-01 06:00:00	Mutual of Omaha Insurance	1	load	1.0	load	1970-01-01 00:00:00
306	wrberkley.com	1970-01-01	2018-09-01 06:00:00	W.R. Berkley	1	load	1.0	load	1970-01-01 00:00:00
307	lkqcorp.com	1970-01-01	2018-09-01 06:00:00	LKQ	1	load	1.0	load	1970-01-01 00:00:00
308	avoncompany.com	1970-01-01	2018-09-01 06:00:00	Avon Products	1	load	1.0	load	1970-01-01 00:00:00
309	target.com	1970-01-01	2018-09-01 06:00:00	Target	1	load	1.0	load	1970-01-01 00:00:00
310	darden.com	1970-01-01	2018-09-01 06:00:00	Darden Restaurants	1	load	1.0	load	1970-01-01 00:00:00
311	kindredhealthcare.com	1970-01-01	2018-09-01 06:00:00	Kindred Healthcare	1	load	1.0	load	1970-01-01 00:00:00
312	weyerhaeuser.com	1970-01-01	2018-09-01 06:00:00	Weyerhaeuser	1	load	1.0	load	1970-01-01 00:00:00
313	caseys.com	1970-01-01	2018-09-01 06:00:00	Caseys General Stores	1	load	1.0	load	1970-01-01 00:00:00
314	sealedair.com	1970-01-01	2018-09-01 06:00:00	Sealed Air	1	load	1.0	load	1970-01-01 00:00:00
315	53.com	1970-01-01	2018-09-01 06:00:00	Fifth Third Bancorp	1	load	1.0	load	1970-01-01 00:00:00
316	dovercorporation.com	1970-01-01	2018-09-01 06:00:00	Dover	1	load	1.0	load	1970-01-01 00:00:00
317	huntingtoningalls.com	1970-01-01	2018-09-01 06:00:00	Huntington Ingalls Industries	1	load	1.0	load	1970-01-01 00:00:00
318	netflix.com	1970-01-01	2018-09-01 06:00:00	Netflix	1	load	1.0	load	1970-01-01 00:00:00
319	dillards.com	1970-01-01	2018-09-01 06:00:00	Dillards	1	load	1.0	load	1970-01-01 00:00:00
320	jnj.com	1970-01-01	2018-09-01 06:00:00	Johnson & Johnson	1	load	1.0	load	1970-01-01 00:00:00
321	emcorgroup.com	1970-01-01	2018-09-01 06:00:00	EMCOR Group	1	load	1.0	load	1970-01-01 00:00:00
322	edwardjones.com	1970-01-01	2018-09-01 06:00:00	Jones Financial	1	load	1.0	load	1970-01-01 00:00:00
323	aksteel.com	1970-01-01	2018-09-01 06:00:00	AK Steel Holding	1	load	1.0	load	1970-01-01 00:00:00
324	ugicorp.com	1970-01-01	2018-09-01 06:00:00	UGI	1	load	1.0	load	1970-01-01 00:00:00
325	expediainc.com	1970-01-01	2018-09-01 06:00:00	Expedia	1	load	1.0	load	1970-01-01 00:00:00
326	salesforce.com	1970-01-01	2018-09-01 06:00:00	salesforce.com	1	load	1.0	load	1970-01-01 00:00:00
327	targaresources.com	1970-01-01	2018-09-01 06:00:00	Targa Resources	1	load	1.0	load	1970-01-01 00:00:00
328	apachecorp.com	1970-01-01	2018-09-01 06:00:00	Apache	1	load	1.0	load	1970-01-01 00:00:00
329	spiritaero.com	1970-01-01	2018-09-01 06:00:00	Spirit AeroSystems Holdings	1	load	1.0	load	1970-01-01 00:00:00
330	expeditors.com	1970-01-01	2018-09-01 06:00:00	Expeditors International of Washington	1	load	1.0	load	1970-01-01 00:00:00
331	metlife.com	1970-01-01	2018-09-01 06:00:00	MetLife	1	load	1.0	load	1970-01-01 00:00:00
332	anixter.com	1970-01-01	2018-09-01 06:00:00	Anixter International	1	load	1.0	load	1970-01-01 00:00:00
333	fisglobal.com	1970-01-01	2018-09-01 06:00:00	Fidelity National Information Services	1	load	1.0	load	1970-01-01 00:00:00
334	asburyauto.com	1970-01-01	2018-09-01 06:00:00	Asbury Automotive Group	1	load	1.0	load	1970-01-01 00:00:00
335	hess.com	1970-01-01	2018-09-01 06:00:00	Hess	1	load	1.0	load	1970-01-01 00:00:00
336	ryder.com	1970-01-01	2018-09-01 06:00:00	Ryder System	1	load	1.0	load	1970-01-01 00:00:00
337	terex.com	1970-01-01	2018-09-01 06:00:00	Terex	1	load	1.0	load	1970-01-01 00:00:00
338	cokecce.com	1970-01-01	2018-09-01 06:00:00	Coca-Cola European Partners	1	load	1.0	load	1970-01-01 00:00:00
339	auto-owners.com	1970-01-01	2018-09-01 06:00:00	Auto-Owners Insurance	1	load	1.0	load	1970-01-01 00:00:00
340	cablevision.com	1970-01-01	2018-09-01 06:00:00	Cablevision Systems	1	load	1.0	load	1970-01-01 00:00:00
341	symantec.com	1970-01-01	2018-09-01 06:00:00	Symantec	1	load	1.0	load	1970-01-01 00:00:00
342	mckesson.com	1970-01-01	2018-09-01 06:00:00	McKesson	1	load	1.0	load	1970-01-01 00:00:00
343	adm.com	1970-01-01	2018-09-01 06:00:00	Archer Daniels Midland	1	load	1.0	load	1970-01-01 00:00:00
344	aboutschwab.com	1970-01-01	2018-09-01 06:00:00	Charles Schwab	1	load	1.0	load	1970-01-01 00:00:00
345	calpine.com	1970-01-01	2018-09-01 06:00:00	Calpine	1	load	1.0	load	1970-01-01 00:00:00
346	cmsenergy.com	1970-01-01	2018-09-01 06:00:00	CMS Energy	1	load	1.0	load	1970-01-01 00:00:00
347	alliancedata.com	1970-01-01	2018-09-01 06:00:00	Alliance Data Systems	1	load	1.0	load	1970-01-01 00:00:00
348	jetblue.com	1970-01-01	2018-09-01 06:00:00	JetBlue Airways	1	load	1.0	load	1970-01-01 00:00:00
349	discoverycommunications.com	1970-01-01	2018-09-01 06:00:00	Discovery Communications	1	load	1.0	load	1970-01-01 00:00:00
350	trin.net	1970-01-01	2018-09-01 06:00:00	Trinity Industries	1	load	1.0	load	1970-01-01 00:00:00
351	sanmina.com	1970-01-01	2018-09-01 06:00:00	Sanmina	1	load	1.0	load	1970-01-01 00:00:00
352	ncr.com	1970-01-01	2018-09-01 06:00:00	NCR	1	load	1.0	load	1970-01-01 00:00:00
353	fmctechnologies.com	1970-01-01	2018-09-01 06:00:00	FMC Technologies	1	load	1.0	load	1970-01-01 00:00:00
354	marathonpetroleum.com	1970-01-01	2018-09-01 06:00:00	Marathon Petroleum	1	load	1.0	load	1970-01-01 00:00:00
355	erieinsurance.com	1970-01-01	2018-09-01 06:00:00	Erie Insurance Group	1	load	1.0	load	1970-01-01 00:00:00
356	rockwellautomation.com	1970-01-01	2018-09-01 06:00:00	Rockwell Automation	1	load	1.0	load	1970-01-01 00:00:00
357	drpeppersnapplegroup.com	1970-01-01	2018-09-01 06:00:00	Dr Pepper Snapple Group	1	load	1.0	load	1970-01-01 00:00:00
358	iheartmedia.com	1970-01-01	2018-09-01 06:00:00	iHeartMedia	1	load	1.0	load	1970-01-01 00:00:00
359	tractorsupply.com	1970-01-01	2018-09-01 06:00:00	Tractor Supply	1	load	1.0	load	1970-01-01 00:00:00
360	jbhunt.com	1970-01-01	2018-09-01 06:00:00	J.B. Hunt Transport Services	1	load	1.0	load	1970-01-01 00:00:00
361	cmc.com	1970-01-01	2018-09-01 06:00:00	Commercial Metals	1	load	1.0	load	1970-01-01 00:00:00
362	o-i.com	1970-01-01	2018-09-01 06:00:00	Owens-Illinois	1	load	1.0	load	1970-01-01 00:00:00
363	harman.com	1970-01-01	2018-09-01 06:00:00	Harman International Industries	1	load	1.0	load	1970-01-01 00:00:00
364	baxalta.com	1970-01-01	2018-09-01 06:00:00	Baxalta	1	load	1.0	load	1970-01-01 00:00:00
365	freddiemac.com	1970-01-01	2018-09-01 06:00:00	Freddie Mac	1	load	1.0	load	1970-01-01 00:00:00
366	afginc.com	1970-01-01	2018-09-01 06:00:00	American Financial Group	1	load	1.0	load	1970-01-01 00:00:00
367	netapp.com	1970-01-01	2018-09-01 06:00:00	NetApp	1	load	1.0	load	1970-01-01 00:00:00
368	graybar.com	1970-01-01	2018-09-01 06:00:00	Graybar Electric	1	load	1.0	load	1970-01-01 00:00:00
369	oshkoshcorporation.com	1970-01-01	2018-09-01 06:00:00	Oshkosh	1	load	1.0	load	1970-01-01 00:00:00
370	ameren.com	1970-01-01	2018-09-01 06:00:00	Ameren	1	load	1.0	load	1970-01-01 00:00:00
371	amark.com	1970-01-01	2018-09-01 06:00:00	A-Mark Precious Metals	1	load	1.0	load	1970-01-01 00:00:00
372	barnesandnobleinc.com	1970-01-01	2018-09-01 06:00:00	Barnes & Noble	1	load	1.0	load	1970-01-01 00:00:00
373	dana.com	1970-01-01	2018-09-01 06:00:00	Dana Holding	1	load	1.0	load	1970-01-01 00:00:00
374	cbrands.com	1970-01-01	2018-09-01 06:00:00	Constellation Brands	1	load	1.0	load	1970-01-01 00:00:00
375	lifepointhealth.net	1970-01-01	2018-09-01 06:00:00	LifePoint Health	1	load	1.0	load	1970-01-01 00:00:00
376	pepsico.com	1970-01-01	2018-09-01 06:00:00	PepsiCo	1	load	1.0	load	1970-01-01 00:00:00
377	zimmerbiomet.com	1970-01-01	2018-09-01 06:00:00	Zimmer Biomet Holdings	1	load	1.0	load	1970-01-01 00:00:00
378	harley-davidson.com	1970-01-01	2018-09-01 06:00:00	Harley-Davidson	1	load	1.0	load	1970-01-01 00:00:00
379	pultegroupinc.com	1970-01-01	2018-09-01 06:00:00	PulteGroup	1	load	1.0	load	1970-01-01 00:00:00
380	newellbrands.com	1970-01-01	2018-09-01 06:00:00	Newell Brands	1	load	1.0	load	1970-01-01 00:00:00
381	averydennison.com	1970-01-01	2018-09-01 06:00:00	Avery Dennison	1	load	1.0	load	1970-01-01 00:00:00
382	jll.com	1970-01-01	2018-09-01 06:00:00	Jones Lang LaSalle	1	load	1.0	load	1970-01-01 00:00:00
383	wecenergygroup.com	1970-01-01	2018-09-01 06:00:00	WEC Energy Group	1	load	1.0	load	1970-01-01 00:00:00
384	marathonoil.com	1970-01-01	2018-09-01 06:00:00	Marathon Oil	1	load	1.0	load	1970-01-01 00:00:00
385	ta-petrol.com	1970-01-01	2018-09-01 06:00:00	TravelCenters of America	1	load	1.0	load	1970-01-01 00:00:00
386	unitedrentals.com	1970-01-01	2018-09-01 06:00:00	United Rentals	1	load	1.0	load	1970-01-01 00:00:00
387	utc.com	1970-01-01	2018-09-01 06:00:00	United Technologies	1	load	1.0	load	1970-01-01 00:00:00
388	hrggroup.com	1970-01-01	2018-09-01 06:00:00	HRG Group	1	load	1.0	load	1970-01-01 00:00:00
389	oldrepublic.com	1970-01-01	2018-09-01 06:00:00	Old Republic International	1	load	1.0	load	1970-01-01 00:00:00
390	windstream.com	1970-01-01	2018-09-01 06:00:00	Windstream Holdings	1	load	1.0	load	1970-01-01 00:00:00
391	starwoodhotels.com	1970-01-01	2018-09-01 06:00:00	Starwood Hotels & Resorts	1	load	1.0	load	1970-01-01 00:00:00
392	delekus.com	1970-01-01	2018-09-01 06:00:00	Delek US Holdings	1	load	1.0	load	1970-01-01 00:00:00
393	packagingcorp.com	1970-01-01	2018-09-01 06:00:00	Packaging Corp. of America	1	load	1.0	load	1970-01-01 00:00:00
394	quintiles.com	1970-01-01	2018-09-01 06:00:00	Quintiles IMS Holdings	1	load	1.0	load	1970-01-01 00:00:00
395	hanes.com	1970-01-01	2018-09-01 06:00:00	Hanesbrands	1	load	1.0	load	1970-01-01 00:00:00
396	realogy.com	1970-01-01	2018-09-01 06:00:00	Realogy Holdings	1	load	1.0	load	1970-01-01 00:00:00
397	mattel.com	1970-01-01	2018-09-01 06:00:00	Mattel	1	load	1.0	load	1970-01-01 00:00:00
398	aetna.com	1970-01-01	2018-09-01 06:00:00	Aetna	1	load	1.0	load	1970-01-01 00:00:00
399	motorolasolutions.com	1970-01-01	2018-09-01 06:00:00	Motorola Solutions	1	load	1.0	load	1970-01-01 00:00:00
400	jmsmucker.com	1970-01-01	2018-09-01 06:00:00	J.M. Smucker	1	load	1.0	load	1970-01-01 00:00:00
401	regions.com	1970-01-01	2018-09-01 06:00:00	Regions Financial	1	load	1.0	load	1970-01-01 00:00:00
402	celanese.com	1970-01-01	2018-09-01 06:00:00	Celanese	1	load	1.0	load	1970-01-01 00:00:00
403	thecloroxcompany.com	1970-01-01	2018-09-01 06:00:00	Clorox	1	load	1.0	load	1970-01-01 00:00:00
404	ingredion.com	1970-01-01	2018-09-01 06:00:00	Ingredion	1	load	1.0	load	1970-01-01 00:00:00
405	genesishcc.com	1970-01-01	2018-09-01 06:00:00	Genesis Healthcare	1	load	1.0	load	1970-01-01 00:00:00
406	peabodyenergy.com	1970-01-01	2018-09-01 06:00:00	Peabody Energy	1	load	1.0	load	1970-01-01 00:00:00
407	alaskaair.com	1970-01-01	2018-09-01 06:00:00	Alaska Air Group	1	load	1.0	load	1970-01-01 00:00:00
408	seaboardcorp.com	1970-01-01	2018-09-01 06:00:00	Seaboard	1	load	1.0	load	1970-01-01 00:00:00
409	lowes.com	1970-01-01	2018-09-01 06:00:00	Lowes	1	load	1.0	load	1970-01-01 00:00:00
410	frontier.com	1970-01-01	2018-09-01 06:00:00	Frontier Communications	1	load	1.0	load	1970-01-01 00:00:00
411	amphenol.com	1970-01-01	2018-09-01 06:00:00	Amphenol	1	load	1.0	load	1970-01-01 00:00:00
412	lansingtradegroup.com	1970-01-01	2018-09-01 06:00:00	Lansing Trade Group	1	load	1.0	load	1970-01-01 00:00:00
413	sandisk.com	1970-01-01	2018-09-01 06:00:00	SanDisk	1	load	1.0	load	1970-01-01 00:00:00
414	sjm.com	1970-01-01	2018-09-01 06:00:00	St. Jude Medical	1	load	1.0	load	1970-01-01 00:00:00
415	wyndhamworldwide.com	1970-01-01	2018-09-01 06:00:00	Wyndham Worldwide	1	load	1.0	load	1970-01-01 00:00:00
416	kellyservices.com	1970-01-01	2018-09-01 06:00:00	Kelly Services	1	load	1.0	load	1970-01-01 00:00:00
417	westernunion.com	1970-01-01	2018-09-01 06:00:00	Western Union	1	load	1.0	load	1970-01-01 00:00:00
418	evhc.net	1970-01-01	2018-09-01 06:00:00	Envision Healthcare Holdings	1	load	1.0	load	1970-01-01 00:00:00
419	visteon.com	1970-01-01	2018-09-01 06:00:00	Visteon	1	load	1.0	load	1970-01-01 00:00:00
420	ups.com	1970-01-01	2018-09-01 06:00:00	UPS	1	load	1.0	load	1970-01-01 00:00:00
421	ajg.com	1970-01-01	2018-09-01 06:00:00	Arthur J. Gallagher	1	load	1.0	load	1970-01-01 00:00:00
422	hosthotels.com	1970-01-01	2018-09-01 06:00:00	Host Hotels & Resorts	1	load	1.0	load	1970-01-01 00:00:00
423	ashland.com	1970-01-01	2018-09-01 06:00:00	Ashland	1	load	1.0	load	1970-01-01 00:00:00
424	insight.com	1970-01-01	2018-09-01 06:00:00	Insight Enterprises	1	load	1.0	load	1970-01-01 00:00:00
425	energyfutureholdings.com	1970-01-01	2018-09-01 06:00:00	Energy Future Holdings	1	load	1.0	load	1970-01-01 00:00:00
426	markelcorp.com	1970-01-01	2018-09-01 06:00:00	Markel	1	load	1.0	load	1970-01-01 00:00:00
427	essendant.com	1970-01-01	2018-09-01 06:00:00	Essendant	1	load	1.0	load	1970-01-01 00:00:00
428	ch2m.com	1970-01-01	2018-09-01 06:00:00	CH2M Hill	1	load	1.0	load	1970-01-01 00:00:00
429	westernsouthern.com	1970-01-01	2018-09-01 06:00:00	Western & Southern Financial Group	1	load	1.0	load	1970-01-01 00:00:00
430	owenscorning.com	1970-01-01	2018-09-01 06:00:00	Owens Corning	1	load	1.0	load	1970-01-01 00:00:00
431	aig.com	1970-01-01	2018-09-01 06:00:00	AIG	1	load	1.0	load	1970-01-01 00:00:00
432	spglobal.com	1970-01-01	2018-09-01 06:00:00	S&P Global	1	load	1.0	load	1970-01-01 00:00:00
433	raymondjames.com	1970-01-01	2018-09-01 06:00:00	Raymond James Financial	1	load	1.0	load	1970-01-01 00:00:00
434	nisource.com	1970-01-01	2018-09-01 06:00:00	NiSource	1	load	1.0	load	1970-01-01 00:00:00
435	airgas.com	1970-01-01	2018-09-01 06:00:00	Airgas	1	load	1.0	load	1970-01-01 00:00:00
436	abm.com	1970-01-01	2018-09-01 06:00:00	ABM Industries	1	load	1.0	load	1970-01-01 00:00:00
437	citizensbank.com	1970-01-01	2018-09-01 06:00:00	Citizens Financial Group	1	load	1.0	load	1970-01-01 00:00:00
438	boozallen.com	1970-01-01	2018-09-01 06:00:00	Booz Allen Hamilton Holding	1	load	1.0	load	1970-01-01 00:00:00
439	simon.com	1970-01-01	2018-09-01 06:00:00	Simon Property Group	1	load	1.0	load	1970-01-01 00:00:00
440	domtar.com	1970-01-01	2018-09-01 06:00:00	Domtar	1	load	1.0	load	1970-01-01 00:00:00
441	rockwellcollins.com	1970-01-01	2018-09-01 06:00:00	Rockwell Collins	1	load	1.0	load	1970-01-01 00:00:00
442	prudential.com	1970-01-01	2018-09-01 06:00:00	Prudential Financial	1	load	1.0	load	1970-01-01 00:00:00
443	lamresearch.com	1970-01-01	2018-09-01 06:00:00	Lam Research	1	load	1.0	load	1970-01-01 00:00:00
444	fiserv.com	1970-01-01	2018-09-01 06:00:00	Fiserv	1	load	1.0	load	1970-01-01 00:00:00
445	spectraenergy.com	1970-01-01	2018-09-01 06:00:00	Spectra Energy	1	load	1.0	load	1970-01-01 00:00:00
446	navient.com	1970-01-01	2018-09-01 06:00:00	Navient	1	load	1.0	load	1970-01-01 00:00:00
447	biglots.com	1970-01-01	2018-09-01 06:00:00	Big Lots	1	load	1.0	load	1970-01-01 00:00:00
448	tdsinc.com	1970-01-01	2018-09-01 06:00:00	Telephone & Data Systems	1	load	1.0	load	1970-01-01 00:00:00
449	firstam.com	1970-01-01	2018-09-01 06:00:00	First American Financial	1	load	1.0	load	1970-01-01 00:00:00
451	cinfin.com	1970-01-01	2018-09-01 06:00:00	Cincinnati Financial	1	load	1.0	load	1970-01-01 00:00:00
452	burlingtonstores.com	1970-01-01	2018-09-01 06:00:00	Burlington Stores	1	load	1.0	load	1970-01-01 00:00:00
453	unitedhealthgroup.com	1970-01-01	2018-09-01 06:00:00	UnitedHealth Group	1	load	1.0	load	1970-01-01 00:00:00
454	intel.com	1970-01-01	2018-09-01 06:00:00	Intel	1	load	1.0	load	1970-01-01 00:00:00
455	humana.com	1970-01-01	2018-09-01 06:00:00	Humana	1	load	1.0	load	1970-01-01 00:00:00
456	disney.com	1970-01-01	2018-09-01 06:00:00	Disney	1	load	1.0	load	1970-01-01 00:00:00
457	cisco.com	1970-01-01	2018-09-01 06:00:00	Cisco Systems	1	load	1.0	load	1970-01-01 00:00:00
458	pfizer.com	1970-01-01	2018-09-01 06:00:00	Pfizer	1	load	1.0	load	1970-01-01 00:00:00
459	dow.com	1970-01-01	2018-09-01 06:00:00	Dow Chemical	1	load	1.0	load	1970-01-01 00:00:00
460	sysco.com	1970-01-01	2018-09-01 06:00:00	Sysco	1	load	1.0	load	1970-01-01 00:00:00
461	fedex.com	1970-01-01	2018-09-01 06:00:00	FedEx	1	load	1.0	load	1970-01-01 00:00:00
462	caterpillar.com	1970-01-01	2018-09-01 06:00:00	Caterpillar	1	load	1.0	load	1970-01-01 00:00:00
463	lockheedmartin.com	1970-01-01	2018-09-01 06:00:00	Lockheed Martin	1	load	1.0	load	1970-01-01 00:00:00
464	cvshealth.com	1970-01-01	2018-09-01 06:00:00	CVS Health	1	load	1.0	load	1970-01-01 00:00:00
465	newyorklife.com	1970-01-01	2018-09-01 06:00:00	New York Life Insurance	1	load	1.0	load	1970-01-01 00:00:00
466	coca-colacompany.com	1970-01-01	2018-09-01 06:00:00	Coca-Cola	1	load	1.0	load	1970-01-01 00:00:00
467	hcahealthcare.com	1970-01-01	2018-09-01 06:00:00	HCA Holdings	1	load	1.0	load	1970-01-01 00:00:00
468	ingrammicro.com	1970-01-01	2018-09-01 06:00:00	Ingram Micro	1	load	1.0	load	1970-01-01 00:00:00
469	energytransfer.com	1970-01-01	2018-09-01 06:00:00	Energy Transfer Equity	1	load	1.0	load	1970-01-01 00:00:00
470	tysonfoods.com	1970-01-01	2018-09-01 06:00:00	Tyson Foods	1	load	1.0	load	1970-01-01 00:00:00
471	aa.com	1970-01-01	2018-09-01 06:00:00	American Airlines Group	1	load	1.0	load	1970-01-01 00:00:00
472	delta.com	1970-01-01	2018-09-01 06:00:00	Delta Air Lines	1	load	1.0	load	1970-01-01 00:00:00
473	nationwide.com	1970-01-01	2018-09-01 06:00:00	Nationwide	1	load	1.0	load	1970-01-01 00:00:00
474	johnsoncontrols.com	1970-01-01	2018-09-01 06:00:00	Johnson Controls	1	load	1.0	load	1970-01-01 00:00:00
475	gm.com	1970-01-01	2018-09-01 06:00:00	General Motors	1	load	1.0	load	1970-01-01 00:00:00
476	bestbuy.com	1970-01-01	2018-09-01 06:00:00	Best Buy	1	load	1.0	load	1970-01-01 00:00:00
477	merck.com	1970-01-01	2018-09-01 06:00:00	Merck	1	load	1.0	load	1970-01-01 00:00:00
478	libertymutual.com	1970-01-01	2018-09-01 06:00:00	Liberty Mutual Insurance Group	1	load	1.0	load	1970-01-01 00:00:00
479	gs.com	1970-01-01	2018-09-01 06:00:00	Goldman Sachs Group	1	load	1.0	load	1970-01-01 00:00:00
480	honeywell.com	1970-01-01	2018-09-01 06:00:00	Honeywell International	1	load	1.0	load	1970-01-01 00:00:00
481	massmutual.com	1970-01-01	2018-09-01 06:00:00	Massachusetts Mutual Life Insurance	1	load	1.0	load	1970-01-01 00:00:00
482	oracle.com	1970-01-01	2018-09-01 06:00:00	Oracle	1	load	1.0	load	1970-01-01 00:00:00
483	morganstanley.com	1970-01-01	2018-09-01 06:00:00	Morgan Stanley	1	load	1.0	load	1970-01-01 00:00:00
484	cigna.com	1970-01-01	2018-09-01 06:00:00	Cigna	1	load	1.0	load	1970-01-01 00:00:00
485	unitedcontinentalholdings.com	1970-01-01	2018-09-01 06:00:00	United Continental Holdings	1	load	1.0	load	1970-01-01 00:00:00
486	ford.com	1970-01-01	2018-09-01 06:00:00	Ford Motor	1	load	1.0	load	1970-01-01 00:00:00
487	allstate.com	1970-01-01	2018-09-01 06:00:00	Allstate	1	load	1.0	load	1970-01-01 00:00:00
488	tiaa.org	1970-01-01	2018-09-01 06:00:00	TIAA	1	load	1.0	load	1970-01-01 00:00:00
489	intlfcstone.com	1970-01-01	2018-09-01 06:00:00	INTL FCStone	1	load	1.0	load	1970-01-01 00:00:00
490	chsinc.com	1970-01-01	2018-09-01 06:00:00	CHS	1	load	1.0	load	1970-01-01 00:00:00
491	americanexpress.com	1970-01-01	2018-09-01 06:00:00	American Express	1	load	1.0	load	1970-01-01 00:00:00
492	gilead.com	1970-01-01	2018-09-01 06:00:00	Gilead Sciences	1	load	1.0	load	1970-01-01 00:00:00
493	publix.com	1970-01-01	2018-09-01 06:00:00	Publix Super Markets	1	load	1.0	load	1970-01-01 00:00:00
494	generaldynamics.com	1970-01-01	2018-09-01 06:00:00	General Dynamics	1	load	1.0	load	1970-01-01 00:00:00
495	tjx.com	1970-01-01	2018-09-01 06:00:00	TJX	1	load	1.0	load	1970-01-01 00:00:00
496	conocophillips.com	1970-01-01	2018-09-01 06:00:00	ConocoPhillips	1	load	1.0	load	1970-01-01 00:00:00
497	att.com	1970-01-01	2018-09-01 06:00:00	AT&T	1	load	1.0	load	1970-01-01 00:00:00
498	nike.com	1970-01-01	2018-09-01 06:00:00	Nike	1	load	1.0	load	1970-01-01 00:00:00
499	wfscorp.com	1970-01-01	2018-09-01 06:00:00	World Fuel Services	1	load	1.0	load	1970-01-01 00:00:00
500	3m.com	1970-01-01	2018-09-01 06:00:00	3M	1	load	1.0	load	1970-01-01 00:00:00
501	mondelezinternational.com	1970-01-01	2018-09-01 06:00:00	Mondelez International	1	load	1.0	load	1970-01-01 00:00:00
502	exeloncorp.com	1970-01-01	2018-09-01 06:00:00	Exelon	1	load	1.0	load	1970-01-01 00:00:00
503	21cf.com	1970-01-01	2018-09-01 06:00:00	Twenty-First Century Fox	1	load	1.0	load	1970-01-01 00:00:00
504	johndeere.com	1970-01-01	2018-09-01 06:00:00	Deere	1	load	1.0	load	1970-01-01 00:00:00
505	tsocorp.com	1970-01-01	2018-09-01 06:00:00	Tesoro	1	load	1.0	load	1970-01-01 00:00:00
506	timewarner.com	1970-01-01	2018-09-01 06:00:00	Time Warner	1	load	1.0	load	1970-01-01 00:00:00
507	redhat.com	1970-01-01	2018-09-01 06:00:00	Red Hat	1	load	1.0	load	1970-01-01 00:00:00
509	openwrt.org	1970-01-01	2018-09-01 06:00:00	OpenWRT	1	load	1.0	load	1970-01-01 00:00:00
510	panasonic.com	1970-01-01	2018-09-01 06:00:00	Panasonic	1	load	1.0	load	1970-01-01 00:00:00
511	comcast.net	1970-01-01	2018-09-01 06:00:00	Comcast	1	load	1.0	load	1970-01-01 00:00:00
512	linux.org	1970-01-01	2018-09-01 06:00:00	Linux	1	load	1.0	load	1970-01-01 00:00:00
514	northwesternmutual.com	1970-01-01	2018-09-01 06:00:00	Northwestern Mutual	1	load	1.0	load	1970-01-01 00:00:00
515	kde.org	1970-01-01	2018-09-01 06:00:00	KDE	1	load	1.0	load	1970-01-01 00:00:00
516	twitter.com	1970-01-01	2018-09-01 06:00:00	Twitter	1	load	1.0	load	1970-01-01 00:00:00
517	adobe.com	1970-01-01	2018-09-01 06:00:00	Adobe	1	load	1.0	load	1970-01-01 00:00:00
519	acm.org	1970-01-01	2018-09-12 02:01:59	ACM	1	load	1.0	load	1970-01-01 00:00:00
520	outdoors@acm.org	1970-01-01	2018-09-12 02:32:53	University of Missouri	1	load	1.0	load	2013-07-15 00:00:00
521	freebsd.org	1970-01-01	2018-09-13 21:15:22	Free BSD	1	load	1.0	load	1970-01-01 00:00:00
\.


--
-- Data for Name: contributor_repo; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.contributor_repo (cntrb_repo_id, repo_git, repo_name, gh_repo_id, cntrb_category, event_id, created_at, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: contributors; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.contributors (cntrb_login, cntrb_email, cntrb_full_name, cntrb_company, cntrb_created_at, cntrb_type, cntrb_fake, cntrb_deleted, cntrb_long, cntrb_lat, cntrb_country_code, cntrb_state, cntrb_city, cntrb_location, cntrb_canonical, cntrb_last_used, gh_user_id, gh_login, gh_url, gh_html_url, gh_node_id, gh_avatar_url, gh_gravatar_id, gh_followers_url, gh_following_url, gh_gists_url, gh_starred_url, gh_subscriptions_url, gh_organizations_url, gh_repos_url, gh_events_url, gh_received_events_url, gh_type, gh_site_admin, gl_web_url, gl_avatar_url, gl_state, gl_username, gl_full_name, gl_id, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
not-provided	\N	\N	\N	2019-06-13 11:33:39	\N	0	0	\N	\N	\N	\N	\N	\N	\N	\N	1	nobody	http://fake.me	http://fake.me	x	http://fake.me	\N	http://fake.me	http://fake.me	http://fake.me	http://fake.me	http://fake.me	http://fake.me	http://fake.me	http://fake.me	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2019-06-13 16:35:25	00000000-0000-0000-0000-000000000000
nan	kannayoshihiro@gmail.com	KANNA Yoshihiro	UTMC	2009-04-17 12:43:58	\N	0	0	\N	\N	\N	\N	\N	\N	kannayoshihiro@gmail.com	2021-01-28 21:56:10-06	74832	nan	https://api.github.com/users/nan	https://github.com/nan	MDQ6VXNlcjc0ODMy	https://avatars.githubusercontent.com/u/74832?v=4		https://api.github.com/users/nan/followers	https://api.github.com/users/nan/following{/other_user}	https://api.github.com/users/nan/gists{/gist_id}	https://api.github.com/users/nan/starred{/owner}{/repo}	https://api.github.com/users/nan/subscriptions	https://api.github.com/users/nan/orgs	https://api.github.com/users/nan/repos	https://api.github.com/users/nan/events{/privacy}	https://api.github.com/users/nan/received_events	User	false	\N	\N	\N	\N	\N	\N	GitHub API Worker	1.0.0	GitHub API	2021-10-28 15:23:46	01000000-0000-0000-0000-000000000000
\.


--
-- Data for Name: contributors_aliases; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.contributors_aliases (cntrb_alias_id, canonical_email, alias_email, cntrb_active, cntrb_last_modified, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: discourse_insights; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.discourse_insights (msg_discourse_id, msg_id, discourse_act, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: dm_repo_annual; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.dm_repo_annual (repo_id, email, affiliation, year, added, removed, whitespace, files, patches, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: dm_repo_group_annual; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.dm_repo_group_annual (repo_group_id, email, affiliation, year, added, removed, whitespace, files, patches, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: dm_repo_group_monthly; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.dm_repo_group_monthly (repo_group_id, email, affiliation, month, year, added, removed, whitespace, files, patches, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: dm_repo_group_weekly; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.dm_repo_group_weekly (repo_group_id, email, affiliation, week, year, added, removed, whitespace, files, patches, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: dm_repo_monthly; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.dm_repo_monthly (repo_id, email, affiliation, month, year, added, removed, whitespace, files, patches, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: dm_repo_weekly; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.dm_repo_weekly (repo_id, email, affiliation, week, year, added, removed, whitespace, files, patches, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: exclude; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.exclude (id, projects_id, email, domain) FROM stdin;
\.


--
-- Data for Name: issue_assignees; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.issue_assignees (issue_assignee_id, issue_id, repo_id, issue_assignee_src_id, issue_assignee_src_node, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: issue_events; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.issue_events (event_id, issue_id, repo_id, action, action_commit_hash, created_at, node_id, node_url, platform_id, issue_event_src_id, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: issue_labels; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.issue_labels (issue_label_id, issue_id, repo_id, label_text, label_description, label_color, label_src_id, label_src_node_id, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: issue_message_ref; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.issue_message_ref (issue_msg_ref_id, issue_id, repo_id, msg_id, issue_msg_ref_src_node_id, issue_msg_ref_src_comment_id, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: issues; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.issues (issue_id, repo_id, pull_request, pull_request_id, created_at, issue_title, issue_body, comment_count, updated_at, closed_at, due_on, repository_url, issue_url, labels_url, comments_url, events_url, html_url, issue_state, issue_node_id, gh_issue_number, gh_issue_id, gh_user_id, tool_source, tool_version, data_source, data_collection_date, reporter_id, cntrb_id) FROM stdin;
\.


--
-- Data for Name: libraries; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.libraries (library_id, repo_id, platform, name, created_timestamp, updated_timestamp, library_description, keywords, library_homepage, license, version_count, latest_release_timestamp, latest_release_number, package_manager_id, dependency_count, dependent_library_count, primary_language, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: library_dependencies; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.library_dependencies (lib_dependency_id, library_id, manifest_platform, manifest_filepath, manifest_kind, repo_id_branch, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: library_version; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.library_version (library_version_id, library_id, library_platform, version_number, version_release_date, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: lstm_anomaly_models; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.lstm_anomaly_models (model_id, model_name, model_description, look_back_days, training_days, batch_size, metric, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: lstm_anomaly_results; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.lstm_anomaly_results (result_id, repo_id, repo_category, model_id, metric, contamination_factor, mean_absolute_error, remarks, metric_field, mean_absolute_actual_value, mean_absolute_prediction_value, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: message; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.message (msg_id, rgls_id, platform_msg_id, platform_node_id, repo_id, msg_text, msg_timestamp, msg_sender_email, msg_header, pltfrm_id, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: message_analysis; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.message_analysis (msg_analysis_id, msg_id, worker_run_id, sentiment_score, reconstruction_error, novelty_flag, feedback_flag, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: message_analysis_summary; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.message_analysis_summary (msg_summary_id, repo_id, worker_run_id, positive_ratio, negative_ratio, novel_count, period, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: message_sentiment; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.message_sentiment (msg_analysis_id, msg_id, worker_run_id, sentiment_score, reconstruction_error, novelty_flag, feedback_flag, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: message_sentiment_summary; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.message_sentiment_summary (msg_summary_id, repo_id, worker_run_id, positive_ratio, negative_ratio, novel_count, period, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: platform; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.platform (pltfrm_id, pltfrm_name, pltfrm_version, pltfrm_release_date, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
1	GitHub	3	2019-06-05	Manual Entry	Sean Goggins	GitHub	2019-06-05 17:23:42
0	Unresolved	0	2019-06-05	Manual Entry	Sean Goggins	GitHub	2022-07-28 20:43:00
2	GitLab	2	2019-06-05	Manual Entry	Sean Goggins	GitHub	2022-07-28 20:43:00
\.


--
-- Data for Name: pull_request_analysis; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_analysis (pull_request_analysis_id, pull_request_id, merge_probability, mechanism, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: pull_request_assignees; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_assignees (pr_assignee_map_id, pull_request_id, repo_id, pr_assignee_src_id, tool_source, tool_version, data_source, data_collection_date, contrib_id) FROM stdin;
\.


--
-- Data for Name: pull_request_commits; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_commits (pr_cmt_id, pull_request_id, repo_id, pr_cmt_sha, pr_cmt_node_id, pr_cmt_message, pr_cmt_comments_url, pr_cmt_timestamp, pr_cmt_author_email, tool_source, tool_version, data_source, data_collection_date, pr_cmt_author_cntrb_id) FROM stdin;
\.


--
-- Data for Name: pull_request_events; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_events (pr_event_id, pull_request_id, repo_id, action, action_commit_hash, created_at, issue_event_src_id, node_id, node_url, platform_id, pr_platform_event_id, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: pull_request_files; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_files (pr_file_id, pull_request_id, repo_id, pr_file_additions, pr_file_deletions, pr_file_path, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: pull_request_labels; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_labels (pr_label_id, pull_request_id, repo_id, pr_src_id, pr_src_node_id, pr_src_url, pr_src_description, pr_src_color, pr_src_default_bool, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: pull_request_message_ref; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_message_ref (pr_msg_ref_id, pull_request_id, repo_id, msg_id, pr_message_ref_src_comment_id, pr_message_ref_src_node_id, pr_issue_url, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: pull_request_meta; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_meta (pr_repo_meta_id, pull_request_id, repo_id, pr_head_or_base, pr_src_meta_label, pr_src_meta_ref, pr_sha, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: pull_request_repo; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_repo (pr_repo_id, pr_repo_meta_id, pr_repo_head_or_base, pr_src_repo_id, pr_src_node_id, pr_repo_name, pr_repo_full_name, pr_repo_private_bool, tool_source, tool_version, data_source, data_collection_date, pr_cntrb_id) FROM stdin;
\.


--
-- Data for Name: pull_request_review_message_ref; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_review_message_ref (pr_review_msg_ref_id, pr_review_id, repo_id, msg_id, pr_review_msg_url, pr_review_src_id, pr_review_msg_src_id, pr_review_msg_node_id, pr_review_msg_diff_hunk, pr_review_msg_path, pr_review_msg_position, pr_review_msg_original_position, pr_review_msg_commit_id, pr_review_msg_original_commit_id, pr_review_msg_updated_at, pr_review_msg_html_url, pr_url, pr_review_msg_author_association, pr_review_msg_start_line, pr_review_msg_original_start_line, pr_review_msg_start_side, pr_review_msg_line, pr_review_msg_original_line, pr_review_msg_side, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: pull_request_reviewers; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_reviewers (pr_reviewer_map_id, pull_request_id, pr_source_id, repo_id, pr_reviewer_src_id, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: pull_request_reviews; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_reviews (pr_review_id, pull_request_id, repo_id, pr_review_author_association, pr_review_state, pr_review_body, pr_review_submitted_at, pr_review_src_id, pr_review_node_id, pr_review_html_url, pr_review_pull_request_url, pr_review_commit_id, platform_id, tool_source, tool_version, data_source, data_collection_date, cntrb_id) FROM stdin;
\.


--
-- Data for Name: pull_request_teams; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_request_teams (pr_team_id, pull_request_id, pr_src_team_id, pr_src_team_node, pr_src_team_url, pr_team_name, pr_team_slug, pr_team_description, pr_team_privacy, pr_team_permission, pr_team_src_members_url, pr_team_src_repositories_url, pr_team_parent_id, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: pull_requests; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.pull_requests (pull_request_id, repo_id, pr_url, pr_src_id, pr_src_node_id, pr_html_url, pr_diff_url, pr_patch_url, pr_issue_url, pr_augur_issue_id, pr_src_number, pr_src_state, pr_src_locked, pr_src_title, pr_body, pr_created_at, pr_updated_at, pr_closed_at, pr_merged_at, pr_merge_commit_sha, pr_teams, pr_milestone, pr_commits_url, pr_review_comments_url, pr_review_comment_url, pr_comments_url, pr_statuses_url, pr_meta_head_id, pr_meta_base_id, pr_src_issue_url, pr_src_comments_url, pr_src_review_comments_url, pr_src_commits_url, pr_src_statuses_url, pr_src_author_association, tool_source, tool_version, data_source, data_collection_date, pr_augur_contributor_id) FROM stdin;
\.


--
-- Data for Name: releases; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.releases (release_id, repo_id, release_name, release_description, release_author, release_created_at, release_published_at, release_updated_at, release_is_draft, release_is_prerelease, release_tag_name, release_url, tag_only, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo (repo_id, repo_group_id, repo_git, repo_path, repo_name, repo_added, repo_type, url, owner_id, description, primary_language, created_at, forked_from, updated_at, repo_archived_date_collected, repo_archived, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
25452	10	https://github.com/chaoss/whitepaper	\N	\N	2024-08-05 12:20:22		\N	\N	\N	\N	\N	Parent not available	\N	\N	0	CLI	1.0	Git	2021-04-17 21:40:42
24441	10	https://github.com/operate-first/operate-first-twitter	\N	\N	2024-08-05 12:20:22		\N	\N	\N	\N	\N	Parent not available	\N	\N	0	CLI	1.0	Git	2021-08-25 16:47:47
24442	10	https://github.com/operate-first/blueprint	\N	\N	2024-08-05 12:20:22		\N	\N	\N	\N	\N	Parent not available	\N	\N	0	CLI	1.0	Git	2021-08-25 16:47:47
25445	10	https://github.com/chaoss/grimoirelab-perceval-opnfv	\N	\N	2024-08-05 12:20:22		\N	\N	\N	\N	\N	Parent not available	\N	\N	0	CLI	1.0	Git	2021-04-17 21:40:39
1	1	https://github.com/chaoss/augur	\N	\N	2024-08-05 12:20:22		\N	\N	\N	\N	\N	Parent not available	\N	\N	0	data load	one	git	2021-06-05 18:41:14
25430	10	https://github.com/SociallyCompute/update-test	\N	\N	2024-08-05 12:20:22		\N	\N	\N	\N	\N	Parent not available	\N	\N	0	\N	\N	\N	\N
25450	10	https://github.com/chaoss/grimoirelab-hatstall	\N	\N	2024-08-05 12:20:22		\N	\N	\N	\N	\N	Parent not available	\N	\N	0	CLI	1.0	Git	2021-04-17 21:40:42
\.


--
-- Data for Name: repo_badging; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_badging (badge_collection_id, repo_id, created_at, tool_source, tool_version, data_source, data_collection_date, data) FROM stdin;
\.


--
-- Data for Name: repo_clones_data; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_clones_data (repo_clone_data_id, repo_id, unique_clones, count_clones, clone_data_timestamp) FROM stdin;
\.


--
-- Data for Name: repo_cluster_messages; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_cluster_messages (msg_cluster_id, repo_id, cluster_content, cluster_mechanism, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_dependencies; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_dependencies (repo_dependencies_id, repo_id, dep_name, dep_count, dep_language, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_deps_libyear; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_deps_libyear (repo_deps_libyear_id, repo_id, name, requirement, type, package_manager, current_verion, latest_version, current_release_date, latest_release_date, libyear, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_deps_scorecard; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_deps_scorecard (repo_deps_scorecard_id, repo_id, name, score, tool_source, tool_version, data_source, data_collection_date, scorecard_check_details) FROM stdin;
\.


--
-- Data for Name: repo_group_insights; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_group_insights (rgi_id, repo_group_id, rgi_metric, rgi_value, cms_id, rgi_fresh, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_groups; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_groups (repo_group_id, rg_name, rg_description, rg_website, rg_recache, rg_last_modified, rg_type, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
1	Default Repo Group	The default repo group created by the schema generation script		0	2019-06-03 15:55:20	GitHub Organization	load	one	git	2019-06-05 13:36:25
10	Default Repo Group	The default repo group created by the schema generation script		0	2021-06-03 15:55:20	GitHub Organization	load	one	git	2019-06-05 13:36:25
25430	Frontend Repos	DO NOT DELETE OR FRONTEND REPOS WILL BREAK		0	2023-02-17 15:00:00	\N	\N	\N	\N	\N
\.


--
-- Data for Name: repo_groups_list_serve; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_groups_list_serve (rgls_id, repo_group_id, rgls_name, rgls_description, rgls_sponsor, rgls_email, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_info; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_info (repo_info_id, repo_id, last_updated, issues_enabled, open_issues, pull_requests_enabled, wiki_enabled, pages_enabled, fork_count, default_branch, watchers_count, "UUID", license, stars_count, committers_count, issue_contributors_count, changelog_file, contributing_file, license_file, code_of_conduct_file, security_issue_file, security_audit_file, status, keywords, commit_count, issues_count, issues_closed, pull_request_count, pull_requests_open, pull_requests_closed, pull_requests_merged, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_insights; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_insights (ri_id, repo_id, ri_metric, ri_value, ri_date, ri_fresh, tool_source, tool_version, data_source, data_collection_date, ri_score, ri_field, ri_detection_method) FROM stdin;
\.


--
-- Data for Name: repo_insights_records; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_insights_records (ri_id, repo_id, ri_metric, ri_field, ri_value, ri_date, ri_score, ri_detection_method, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_labor; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_labor (repo_labor_id, repo_id, repo_clone_date, rl_analysis_date, programming_language, file_path, file_name, total_lines, code_lines, comment_lines, blank_lines, code_complexity, repo_url, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_meta; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_meta (repo_id, rmeta_id, rmeta_name, rmeta_value, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_sbom_scans; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_sbom_scans (rsb_id, repo_id, sbom_scan) FROM stdin;
\.


--
-- Data for Name: repo_stats; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_stats (repo_id, rstat_id, rstat_name, rstat_value, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_test_coverage; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_test_coverage (repo_id, repo_clone_date, rtc_analysis_date, programming_language, file_path, file_name, testing_tool, file_statement_count, file_subroutine_count, file_statements_tested, file_subroutines_tested, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repo_topic; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repo_topic (repo_topic_id, repo_id, topic_id, topic_prob, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: repos_fetch_log; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.repos_fetch_log (repos_id, status, date) FROM stdin;
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.settings (id, setting, value, last_modified) FROM stdin;
5	report_date	committer	2019-05-07 12:47:26
6	report_attribution	author	2019-05-07 12:47:26
10	google_analytics	disabled	2019-05-07 12:47:26
11	update_frequency	24	2019-05-07 12:47:26
12	database_version	7	2019-05-07 12:47:26
13	results_visibility	show	2019-05-07 12:47:26
1	start_date	2001-01-01	1900-01-22 20:34:51
4	log_level	Debug	2019-05-07 12:47:26
2	repo_directory	/augur/repos/	2019-05-07 12:47:26
8	affiliations_processed	2001-08-26 10:03:29.815013+00	1900-01-22 20:36:27
9	aliases_processed	2001-08-26 10:03:29.815013+00	1900-01-22 20:36:27
7	working_author	done	1900-01-22 20:23:43
3	utility_status	Idle	1900-01-22 20:38:07
\.


--
-- Data for Name: topic_words; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.topic_words (topic_words_id, topic_id, word, word_prob, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: unknown_cache; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.unknown_cache (type, repo_group_id, email, domain, added, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: unresolved_commit_emails; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.unresolved_commit_emails (email_unresolved_id, email, name, tool_source, tool_version, data_source, data_collection_date) FROM stdin;
\.


--
-- Data for Name: utility_log; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.utility_log (id, level, status, attempted) FROM stdin;
\.


--
-- Data for Name: working_commits; Type: TABLE DATA; Schema: augur_data; Owner: augur
--

COPY augur_data.working_commits (repos_id, working_commit) FROM stdin;
\.


--
-- Data for Name: all; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations."all" ("Name", "Bytes", "Lines", "Code", "Comment", "Blank", "Complexity", "Count", "WeightedComplexity", "Files") FROM stdin;
\.


--
-- Data for Name: augur_settings; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.augur_settings (id, setting, value, last_modified) FROM stdin;
1	augur_data_version	100	2021-10-12 08:41:51
\.


--
-- Data for Name: client_applications; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.client_applications (id, api_key, user_id, name, redirect_url) FROM stdin;
\.


--
-- Data for Name: collection_status; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.collection_status (repo_id, core_data_last_collected, core_status, core_task_id, secondary_data_last_collected, secondary_status, secondary_task_id, event_last_collected, facade_status, facade_data_last_collected, facade_task_id, core_weight, facade_weight, secondary_weight, issue_pr_sum, commit_sum, ml_status, ml_data_last_collected, ml_task_id, ml_weight) FROM stdin;
\.


--
-- Data for Name: config; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.config (id, section_name, setting_name, value, type) FROM stdin;
\.


--
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.refresh_tokens (id, user_session_token) FROM stdin;
\.


--
-- Data for Name: repos_fetch_log; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.repos_fetch_log (repos_id, status, date) FROM stdin;
\.


--
-- Data for Name: subscription_types; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.subscription_types (id, name) FROM stdin;
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.subscriptions (application_id, type_id) FROM stdin;
\.


--
-- Data for Name: user_groups; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.user_groups (group_id, user_id, name, favorited) FROM stdin;
1	1	default	f
\.


--
-- Data for Name: user_repos; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.user_repos (repo_id, group_id) FROM stdin;
1	1
\.


--
-- Data for Name: user_session_tokens; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.user_session_tokens (token, user_id, created_at, expiration, application_id) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.users (user_id, login_name, login_hashword, email, text_phone, first_name, last_name, tool_source, tool_version, data_source, data_collection_date, admin, email_verified) FROM stdin;
1	cli_user	pbkdf2:sha256:260000$oDmAfipU8Ef8TAau$835fce1fc3290b57b5e02ec83aef4613cc06664e6e7535bb6d267dc44563d5d5	cli_user	\N	cli_user	cli_user	Schema Generaation	\N	Schema Generation	2022-10-02 21:49:13	f	f
\.


--
-- Data for Name: worker_history; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.worker_history (history_id, repo_id, worker, job_model, oauth_id, "timestamp", status, total_results) FROM stdin;
1	1	workers.repo_info_worker.50723	repo_info	0	2021-10-17 12:05:22	Success	1
2	1	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:34:30	Success	0
3	1	workers.github_worker.9396	repo_info	0	2021-12-20 10:34:32	Stopped	0
4	1	workers.github_worker.9396	issues	0	2021-12-20 10:34:50	Error	0
5	1	workers.repo_info_worker.9176	repo_info	0	2021-12-20 10:34:33	Success	1
6	1	workers.insight_worker.9082	insights	0	2021-12-20 10:34:32	Success	0
7	1	workers.linux_badge_worker.9447	badges	0	2021-12-20 10:34:32	Success	1
8	24441	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:36:31	Success	0
9	24441	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 10:36:33	Success	0
10	24441	workers.github_worker.9396	issues	0	2021-12-20 10:36:34	Error	0
11	24441	workers.repo_info_worker.9176	repo_info	0	2021-12-20 10:36:34	Success	1
12	24441	workers.linux_badge_worker.9447	badges	0	2021-12-20 10:36:33	Success	0
13	24441	workers.pull_request_worker.9145	repo_info	0	2021-12-20 10:36:33	Stopped	0
14	24442	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:38:32	Success	0
15	1	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 10:39:00	Success	0
16	24442	workers.github_worker.9396	issues	0	2021-12-20 10:38:35	Error	0
17	24442	workers.insight_worker.9082	insights	0	2021-12-20 10:38:33	Success	0
18	24442	workers.repo_info_worker.9176	repo_info	0	2021-12-20 10:38:34	Success	1
19	24442	workers.pull_request_worker.9145	repo_info	0	2021-12-20 10:39:00	Stopped	0
20	25430	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:40:32	Success	0
21	24442	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 10:40:33	Success	0
22	25430	workers.insight_worker.9082	insights	0	2021-12-20 10:40:34	Success	0
23	25430	workers.linux_badge_worker.9447	badges	0	2021-12-20 10:40:34	Success	0
24	25430	workers.pull_request_worker.9145	repo_info	0	2021-12-20 10:40:34	Stopped	0
25	25430	workers.repo_info_worker.9176	repo_info	0	2021-12-20 10:40:35	Success	1
26	25430	workers.insight_worker.9082	insights	0	2021-12-20 10:50:56	Success	0
27	1	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 10:51:26	Success	0
28	1	workers.github_worker.9396	issues	0	2021-12-20 10:51:14	Error	0
29	1	workers.release_worker.9488	releases	0	2021-12-20 10:51:01	Success	1
30	25430	workers.linux_badge_worker.9447	badges	0	2021-12-20 10:50:56	Success	0
31	25430	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:51:26	Success	0
32	25430	workers.pull_request_worker.9145	repo_info	0	2021-12-20 10:51:26	Stopped	0
33	24441	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 10:52:57	Success	0
34	1	workers.insight_worker.9082	insights	0	2021-12-20 10:52:56	Success	0
35	1	workers.repo_info_worker.9176	repo_info	0	2021-12-20 10:52:58	Success	1
36	1	workers.linux_badge_worker.9447	badges	0	2021-12-20 10:52:57	Success	1
37	24441	workers.release_worker.9488	repo_info	0	2021-12-20 10:52:56	Stopped	0
38	1	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:52:57	Success	0
39	1	workers.pull_request_worker.9145	repo_info	0	2021-12-20 10:52:57	Stopped	0
40	24441	workers.insight_worker.9082	insights	0	2021-12-20 10:54:59	Success	2
41	24442	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 10:54:57	Success	0
42	24442	workers.github_worker.9396	issues	0	2021-12-20 10:54:58	Error	0
43	24441	workers.repo_info_worker.9176	repo_info	0	2021-12-20 10:54:58	Success	1
44	24441	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:54:57	Success	0
45	24441	workers.pull_request_worker.9145	repo_info	0	2021-12-20 10:54:57	Stopped	0
46	25430	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 10:56:56	Success	0
47	24442	workers.insight_worker.9082	insights	0	2021-12-20 10:56:57	Success	0
48	24442	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 10:56:56	Success	0
49	24442	workers.pull_request_worker.9145	repo_info	0	2021-12-20 10:56:56	Stopped	0
50	24442	workers.repo_info_worker.9176	repo_info	0	2021-12-20 10:56:58	Success	1
51	24442	workers.linux_badge_worker.9447	badges	0	2021-12-20 10:56:58	Success	0
52	24442	workers.insight_worker.9082	insights	0	2021-12-20 11:37:29	Success	0
53	24442	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:37:28	Success	1
54	1	workers.github_worker.9396	issues	0	2021-12-20 11:38:35	Error	0
55	1	workers.release_worker.9488	releases	0	2021-12-20 11:37:32	Success	1
56	24442	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 11:37:27	Success	0
57	24442	workers.pull_request_worker.9145	repo_info	0	2021-12-20 11:37:27	Stopped	0
58	1	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 11:38:25	Success	0
59	25430	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:39:29	Success	1
60	25430	workers.linux_badge_worker.9447	badges	0	2021-12-20 11:39:28	Success	0
61	24441	workers.github_worker.9396	issues	0	2021-12-20 11:39:49	Success	0
62	25430	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 11:39:27	Success	0
63	25430	workers.pull_request_worker.9145	repo_info	0	2021-12-20 11:39:27	Stopped	0
64	24441	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 11:39:47	Success	0
65	25430	workers.insight_worker.9082	insights	0	2021-12-20 11:39:29	Success	0
66	1	workers.insight_worker.9082	insights	0	2021-12-20 11:41:32	Success	1
67	1	workers.linux_badge_worker.9447	badges	0	2021-12-20 11:41:28	Success	1
68	24442	workers.github_worker.9396	issues	0	2021-12-20 11:42:22	Success	0
69	1	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:41:30	Success	1
70	1	workers.pull_request_worker.9145	repo_info	0	2021-12-20 11:41:28	Stopped	0
71	24442	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 11:42:05	Success	0
72	24441	workers.insight_worker.9082	insights	0	2021-12-20 11:43:33	Success	1
73	24441	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:43:29	Success	1
74	25430	workers.github_worker.9396	issues	0	2021-12-20 11:43:31	Success	0
75	24441	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 11:43:49	Success	0
76	24441	workers.pull_request_worker.9145	repo_info	0	2021-12-20 11:43:49	Stopped	0
77	25430	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 11:44:10	Success	0
78	24441	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 11:52:46	Success	0
79	24441	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:52:31	Success	1
80	24441	workers.github_worker.9396	repo_info	0	2021-12-20 12:05:59	Stopped	0
81	24442	workers.github_worker.9396	repo_info	0	2021-12-20 12:06:20	Stopped	0
82	25430	workers.github_worker.9396	repo_info	0	2021-12-20 12:07:08	Stopped	0
83	25430	workers.github_worker.9396	issues	0	2021-12-20 12:07:11	Success	0
84	24441	workers.pull_request_worker.9145	repo_info	0	2021-12-20 11:53:12	Stopped	0
85	24442	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 11:54:45	Success	0
86	24442	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:54:28	Success	1
87	24442	workers.linux_badge_worker.9447	badges	0	2021-12-20 11:54:28	Success	0
88	24441	workers.release_worker.9488	repo_info	0	2021-12-20 11:54:28	Stopped	0
89	24442	workers.insight_worker.9082	insights	0	2021-12-20 11:54:31	Success	0
90	24442	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 12:16:33	Success	0
91	25430	workers.linux_badge_worker.9447	badges	0	2021-12-20 11:56:31	Success	0
92	25430	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:56:32	Success	1
93	25430	workers.insight_worker.9082	insights	0	2021-12-20 11:56:34	Success	0
94	1	workers.linux_badge_worker.9447	badges	0	2021-12-20 11:58:31	Success	1
95	1	workers.repo_info_worker.9176	repo_info	0	2021-12-20 11:58:33	Success	1
96	1	workers.insight_worker.9082	insights	0	2021-12-20 11:58:34	Success	0
97	24442	workers.pull_request_worker.9145	repo_info	0	2021-12-20 12:16:33	Stopped	0
98	25430	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 12:17:02	Success	0
99	25430	workers.pull_request_worker.9145	pull_requests	0	2021-12-20 12:17:06	Success	0
100	25430	workers.pull_request_worker.9145	repo_info	0	2021-12-20 12:17:07	Stopped	0
101	1	workers.pull_request_worker.9145	pull_request_files	0	2021-12-20 12:17:08	Success	0
102	1	workers.pull_request_worker.9145	repo_info	0	2021-12-20 12:17:08	Stopped	0
103	1	workers.insight_worker.9082	insights	0	2021-12-20 12:43:41	Success	0
104	25430	workers.pull_request_worker.9145	repo_info	0	2021-12-20 12:43:38	Stopped	0
105	24441	workers.github_worker.9396	repo_info	14	2021-12-20 12:55:23	Stopped	0
106	24442	workers.github_worker.9396	repo_info	14	2021-12-20 12:55:44	Stopped	0
107	25430	workers.github_worker.9396	repo_info	14	2021-12-20 12:56:32	Stopped	0
108	1	workers.pull_request_worker.9145	pull_requests	1017	2021-12-20 12:58:53	Success	0
109	24441	workers.insight_worker.9082	insights	0	2021-12-20 12:45:43	Success	1
110	24441	workers.linux_badge_worker.9447	badges	0	2021-12-20 12:45:39	Success	0
111	24441	workers.release_worker.9488	repo_info	0	2021-12-20 12:45:38	Stopped	0
112	24441	workers.repo_info_worker.9176	repo_info	0	2021-12-20 12:45:41	Success	1
113	24442	workers.insight_worker.9082	insights	0	2021-12-20 12:47:41	Success	0
114	24442	workers.repo_info_worker.9176	repo_info	1022	2021-12-20 12:47:48	Success	1
115	24442	workers.linux_badge_worker.9447	badges	0	2021-12-20 12:47:40	Success	0
116	25430	workers.insight_worker.9082	insights	0	2021-12-20 12:49:41	Success	0
117	25430	workers.repo_info_worker.9176	repo_info	14	2021-12-20 12:49:48	Success	1
118	25430	workers.linux_badge_worker.9447	badges	0	2021-12-20 12:49:40	Success	0
119	1	workers.pull_request_worker.9145	pull_request_files	1017	2021-12-20 13:09:07	Success	0
120	1	workers.pull_request_worker.9145	repo_info	1017	2021-12-20 13:09:07	Stopped	0
\.


--
-- Data for Name: worker_job; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.worker_job (job_model, state, zombie_head, since_id_str, description, last_count, last_run, analysis_state, oauth_id) FROM stdin;
\.


--
-- Data for Name: worker_oauth; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.worker_oauth (oauth_id, name, consumer_key, consumer_secret, access_token, access_token_secret, repo_directory, platform) FROM stdin;
\.


--
-- Data for Name: worker_settings_facade; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.worker_settings_facade (id, setting, value, last_modified) FROM stdin;
\.


--
-- Data for Name: working_commits; Type: TABLE DATA; Schema: augur_operations; Owner: augur
--

COPY augur_operations.working_commits (repos_id, working_commit) FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: augur
--

COPY public.alembic_version (version_num) FROM stdin;
28
\.


--
-- Data for Name: test; Type: TABLE DATA; Schema: public; Owner: augur
--

COPY public.test (test) FROM stdin;
\.


--
-- Data for Name: annotation_types; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.annotation_types (annotation_type_id, name) FROM stdin;
1	REVIEW
2	OTHER
\.


--
-- Data for Name: annotations; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.annotations (annotation_id, document_id, annotation_type_id, identifier_id, creator_id, created_ts, comment) FROM stdin;
\.


--
-- Data for Name: augur_repo_map; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.augur_repo_map (map_id, dosocs_pkg_id, dosocs_pkg_name, repo_id, repo_path) FROM stdin;
\.


--
-- Data for Name: creator_types; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.creator_types (creator_type_id, name) FROM stdin;
1	Person
2	Organization
3	Tool
\.


--
-- Data for Name: creators; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.creators (creator_id, creator_type_id, name, email) FROM stdin;
1	3	dosocs2-0.16.1	
\.


--
-- Data for Name: document_namespaces; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.document_namespaces (document_namespace_id, uri) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.documents (document_id, document_namespace_id, data_license_id, spdx_version, name, license_list_version, created_ts, creator_comment, document_comment, package_id) FROM stdin;
\.


--
-- Data for Name: documents_creators; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.documents_creators (document_creator_id, document_id, creator_id) FROM stdin;
\.


--
-- Data for Name: external_refs; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.external_refs (external_ref_id, document_id, document_namespace_id, id_string, sha256) FROM stdin;
\.


--
-- Data for Name: file_contributors; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.file_contributors (file_contributor_id, file_id, contributor) FROM stdin;
\.


--
-- Data for Name: file_types; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.file_types (file_type_id, name) FROM stdin;
4	APPLICATION
3	ARCHIVE
5	AUDIO
2	BINARY
9	DOCUMENTATION
6	IMAGE
11	OTHER
1	SOURCE
10	SPDX
7	TEXT
8	VIDEO
\.


--
-- Data for Name: files; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.files (file_id, file_type_id, sha256, copyright_text, package_id, comment, notice) FROM stdin;
\.


--
-- Data for Name: files_licenses; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.files_licenses (file_license_id, file_id, license_id, extracted_text) FROM stdin;
\.


--
-- Data for Name: files_scans; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.files_scans (file_scan_id, file_id, scanner_id) FROM stdin;
\.


--
-- Data for Name: identifiers; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.identifiers (identifier_id, document_namespace_id, id_string, document_id, package_id, package_file_id) FROM stdin;
\.


--
-- Data for Name: licenses; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.licenses (license_id, name, short_name, cross_reference, comment, is_spdx_official) FROM stdin;
1	3dfx Glide License	Glide	http://spdx.org/licenses/Glide.html		t
2	Abstyles License	Abstyles	http://spdx.org/licenses/Abstyles.html		t
3	Academic Free License v1.1	AFL-1.1	http://spdx.org/licenses/AFL-1.1.html		t
4	Academic Free License v1.2	AFL-1.2	http://spdx.org/licenses/AFL-1.2.html		t
5	Academic Free License v2.0	AFL-2.0	http://spdx.org/licenses/AFL-2.0.html		t
6	Academic Free License v2.1	AFL-2.1	http://spdx.org/licenses/AFL-2.1.html		t
7	Academic Free License v3.0	AFL-3.0	http://spdx.org/licenses/AFL-3.0.html		t
8	Academy of Motion Picture Arts and Sciences BSD	AMPAS	http://spdx.org/licenses/AMPAS.html		t
9	Adaptive Public License 1.0	APL-1.0	http://spdx.org/licenses/APL-1.0.html		t
10	Adobe Glyph List License	Adobe-Glyph	http://spdx.org/licenses/Adobe-Glyph.html		t
11	Adobe Postscript AFM License	APAFML	http://spdx.org/licenses/APAFML.html		t
12	Adobe Systems Incorporated Source Code License Agreement	Adobe-2006	http://spdx.org/licenses/Adobe-2006.html		t
13	Affero General Public License v1.0	AGPL-1.0	http://spdx.org/licenses/AGPL-1.0.html		t
14	Afmparse License	Afmparse	http://spdx.org/licenses/Afmparse.html		t
15	Aladdin Free Public License	Aladdin	http://spdx.org/licenses/Aladdin.html		t
16	Amazon Digital Services License	ADSL	http://spdx.org/licenses/ADSL.html		t
17	AMD's plpa_map.c License	AMDPLPA	http://spdx.org/licenses/AMDPLPA.html		t
18	ANTLR Software Rights Notice	ANTLR-PD	http://spdx.org/licenses/ANTLR-PD.html		t
19	Apache License 1.0	Apache-1.0	http://spdx.org/licenses/Apache-1.0.html		t
20	Apache License 1.1	Apache-1.1	http://spdx.org/licenses/Apache-1.1.html		t
21	Apache License 2.0	Apache-2.0	http://spdx.org/licenses/Apache-2.0.html		t
22	Apple MIT License	AML	http://spdx.org/licenses/AML.html		t
23	Apple Public Source License 1.0	APSL-1.0	http://spdx.org/licenses/APSL-1.0.html		t
24	Apple Public Source License 1.1	APSL-1.1	http://spdx.org/licenses/APSL-1.1.html		t
25	Apple Public Source License 1.2	APSL-1.2	http://spdx.org/licenses/APSL-1.2.html		t
26	Apple Public Source License 2.0	APSL-2.0	http://spdx.org/licenses/APSL-2.0.html		t
27	Artistic License 1.0	Artistic-1.0	http://spdx.org/licenses/Artistic-1.0.html		t
28	Artistic License 1.0 (Perl)	Artistic-1.0-Perl	http://spdx.org/licenses/Artistic-1.0-Perl.html		t
29	Artistic License 1.0 w/clause 8	Artistic-1.0-cl8	http://spdx.org/licenses/Artistic-1.0-cl8.html		t
30	Artistic License 2.0	Artistic-2.0	http://spdx.org/licenses/Artistic-2.0.html		t
31	Attribution Assurance License	AAL	http://spdx.org/licenses/AAL.html		t
32	Bahyph License	Bahyph	http://spdx.org/licenses/Bahyph.html		t
33	Barr License	Barr	http://spdx.org/licenses/Barr.html		t
34	Beerware License	Beerware	http://spdx.org/licenses/Beerware.html		t
35	BitTorrent Open Source License v1.0	BitTorrent-1.0	http://spdx.org/licenses/BitTorrent-1.0.html		t
36	BitTorrent Open Source License v1.1	BitTorrent-1.1	http://spdx.org/licenses/BitTorrent-1.1.html		t
37	Boost Software License 1.0	BSL-1.0	http://spdx.org/licenses/BSL-1.0.html		t
38	Borceux license	Borceux	http://spdx.org/licenses/Borceux.html		t
39	BSD 2-clause "Simplified" License	BSD-2-Clause	http://spdx.org/licenses/BSD-2-Clause.html		t
40	BSD 2-clause FreeBSD License	BSD-2-Clause-FreeBSD	http://spdx.org/licenses/BSD-2-Clause-FreeBSD.html		t
41	BSD 2-clause NetBSD License	BSD-2-Clause-NetBSD	http://spdx.org/licenses/BSD-2-Clause-NetBSD.html		t
42	BSD 3-clause "New" or "Revised" License	BSD-3-Clause	http://spdx.org/licenses/BSD-3-Clause.html		t
43	BSD 3-clause Clear License	BSD-3-Clause-Clear	http://spdx.org/licenses/BSD-3-Clause-Clear.html		t
44	BSD 4-clause "Original" or "Old" License	BSD-4-Clause	http://spdx.org/licenses/BSD-4-Clause.html		t
45	BSD Protection License	BSD-Protection	http://spdx.org/licenses/BSD-Protection.html		t
46	BSD with attribution	BSD-3-Clause-Attribution	http://spdx.org/licenses/BSD-3-Clause-Attribution.html		t
47	BSD Zero Clause License	0BSD	http://spdx.org/licenses/0BSD.html		t
48	BSD-4-Clause (University of California-Specific)	BSD-4-Clause-UC	http://spdx.org/licenses/BSD-4-Clause-UC.html		t
49	bzip2 and libbzip2 License v1.0.5	bzip2-1.0.5	http://spdx.org/licenses/bzip2-1.0.5.html		t
50	bzip2 and libbzip2 License v1.0.6	bzip2-1.0.6	http://spdx.org/licenses/bzip2-1.0.6.html		t
51	Caldera License	Caldera	http://spdx.org/licenses/Caldera.html		t
52	CeCILL Free Software License Agreement v1.0	CECILL-1.0	http://spdx.org/licenses/CECILL-1.0.html		t
53	CeCILL Free Software License Agreement v1.1	CECILL-1.1	http://spdx.org/licenses/CECILL-1.1.html		t
54	CeCILL Free Software License Agreement v2.0	CECILL-2.0	http://spdx.org/licenses/CECILL-2.0.html		t
55	CeCILL Free Software License Agreement v2.1	CECILL-2.1	http://spdx.org/licenses/CECILL-2.1.html		t
56	CeCILL-B Free Software License Agreement	CECILL-B	http://spdx.org/licenses/CECILL-B.html		t
57	CeCILL-C Free Software License Agreement	CECILL-C	http://spdx.org/licenses/CECILL-C.html		t
58	Clarified Artistic License	ClArtistic	http://spdx.org/licenses/ClArtistic.html		t
59	CMU License	MIT-CMU	http://spdx.org/licenses/MIT-CMU.html		t
60	CNRI Jython License	CNRI-Jython	http://spdx.org/licenses/CNRI-Jython.html		t
61	CNRI Python License	CNRI-Python	http://spdx.org/licenses/CNRI-Python.html		t
62	CNRI Python Open Source GPL Compatible License Agreement	CNRI-Python-GPL-Compatible	http://spdx.org/licenses/CNRI-Python-GPL-Compatible.html		t
63	Code Project Open License 1.02	CPOL-1.02	http://spdx.org/licenses/CPOL-1.02.html		t
64	Common Development and Distribution License 1.0	CDDL-1.0	http://spdx.org/licenses/CDDL-1.0.html		t
65	Common Development and Distribution License 1.1	CDDL-1.1	http://spdx.org/licenses/CDDL-1.1.html		t
66	Common Public Attribution License 1.0	CPAL-1.0	http://spdx.org/licenses/CPAL-1.0.html		t
67	Common Public License 1.0	CPL-1.0	http://spdx.org/licenses/CPL-1.0.html		t
68	Computer Associates Trusted Open Source License 1.1	CATOSL-1.1	http://spdx.org/licenses/CATOSL-1.1.html		t
69	Condor Public License v1.1	Condor-1.1	http://spdx.org/licenses/Condor-1.1.html		t
70	Creative Commons Attribution 1.0	CC-BY-1.0	http://spdx.org/licenses/CC-BY-1.0.html		t
71	Creative Commons Attribution 2.0	CC-BY-2.0	http://spdx.org/licenses/CC-BY-2.0.html		t
72	Creative Commons Attribution 2.5	CC-BY-2.5	http://spdx.org/licenses/CC-BY-2.5.html		t
73	Creative Commons Attribution 3.0	CC-BY-3.0	http://spdx.org/licenses/CC-BY-3.0.html		t
74	Creative Commons Attribution 4.0	CC-BY-4.0	http://spdx.org/licenses/CC-BY-4.0.html		t
75	Creative Commons Attribution No Derivatives 1.0	CC-BY-ND-1.0	http://spdx.org/licenses/CC-BY-ND-1.0.html		t
76	Creative Commons Attribution No Derivatives 2.0	CC-BY-ND-2.0	http://spdx.org/licenses/CC-BY-ND-2.0.html		t
77	Creative Commons Attribution No Derivatives 2.5	CC-BY-ND-2.5	http://spdx.org/licenses/CC-BY-ND-2.5.html		t
78	Creative Commons Attribution No Derivatives 3.0	CC-BY-ND-3.0	http://spdx.org/licenses/CC-BY-ND-3.0.html		t
79	Creative Commons Attribution No Derivatives 4.0	CC-BY-ND-4.0	http://spdx.org/licenses/CC-BY-ND-4.0.html		t
80	Creative Commons Attribution Non Commercial 1.0	CC-BY-NC-1.0	http://spdx.org/licenses/CC-BY-NC-1.0.html		t
81	Creative Commons Attribution Non Commercial 2.0	CC-BY-NC-2.0	http://spdx.org/licenses/CC-BY-NC-2.0.html		t
82	Creative Commons Attribution Non Commercial 2.5	CC-BY-NC-2.5	http://spdx.org/licenses/CC-BY-NC-2.5.html		t
83	Creative Commons Attribution Non Commercial 3.0	CC-BY-NC-3.0	http://spdx.org/licenses/CC-BY-NC-3.0.html		t
84	Creative Commons Attribution Non Commercial 4.0	CC-BY-NC-4.0	http://spdx.org/licenses/CC-BY-NC-4.0.html		t
85	Creative Commons Attribution Non Commercial No Derivatives 1.0	CC-BY-NC-ND-1.0	http://spdx.org/licenses/CC-BY-NC-ND-1.0.html		t
86	Creative Commons Attribution Non Commercial No Derivatives 2.0	CC-BY-NC-ND-2.0	http://spdx.org/licenses/CC-BY-NC-ND-2.0.html		t
87	Creative Commons Attribution Non Commercial No Derivatives 2.5	CC-BY-NC-ND-2.5	http://spdx.org/licenses/CC-BY-NC-ND-2.5.html		t
88	Creative Commons Attribution Non Commercial No Derivatives 3.0	CC-BY-NC-ND-3.0	http://spdx.org/licenses/CC-BY-NC-ND-3.0.html		t
89	Creative Commons Attribution Non Commercial No Derivatives 4.0	CC-BY-NC-ND-4.0	http://spdx.org/licenses/CC-BY-NC-ND-4.0.html		t
90	Creative Commons Attribution Non Commercial Share Alike 1.0	CC-BY-NC-SA-1.0	http://spdx.org/licenses/CC-BY-NC-SA-1.0.html		t
91	Creative Commons Attribution Non Commercial Share Alike 2.0	CC-BY-NC-SA-2.0	http://spdx.org/licenses/CC-BY-NC-SA-2.0.html		t
92	Creative Commons Attribution Non Commercial Share Alike 2.5	CC-BY-NC-SA-2.5	http://spdx.org/licenses/CC-BY-NC-SA-2.5.html		t
93	Creative Commons Attribution Non Commercial Share Alike 3.0	CC-BY-NC-SA-3.0	http://spdx.org/licenses/CC-BY-NC-SA-3.0.html		t
94	Creative Commons Attribution Non Commercial Share Alike 4.0	CC-BY-NC-SA-4.0	http://spdx.org/licenses/CC-BY-NC-SA-4.0.html		t
95	Creative Commons Attribution Share Alike 1.0	CC-BY-SA-1.0	http://spdx.org/licenses/CC-BY-SA-1.0.html		t
96	Creative Commons Attribution Share Alike 2.0	CC-BY-SA-2.0	http://spdx.org/licenses/CC-BY-SA-2.0.html		t
97	Creative Commons Attribution Share Alike 2.5	CC-BY-SA-2.5	http://spdx.org/licenses/CC-BY-SA-2.5.html		t
98	Creative Commons Attribution Share Alike 3.0	CC-BY-SA-3.0	http://spdx.org/licenses/CC-BY-SA-3.0.html		t
99	Creative Commons Attribution Share Alike 4.0	CC-BY-SA-4.0	http://spdx.org/licenses/CC-BY-SA-4.0.html		t
100	Creative Commons Zero v1.0 Universal	CC0-1.0	http://spdx.org/licenses/CC0-1.0.html		t
101	Crossword License	Crossword	http://spdx.org/licenses/Crossword.html		t
102	CrystalStacker License	CrystalStacker	http://spdx.org/licenses/CrystalStacker.html		t
103	CUA Office Public License v1.0	CUA-OPL-1.0	http://spdx.org/licenses/CUA-OPL-1.0.html		t
104	Cube License	Cube	http://spdx.org/licenses/Cube.html		t
105	Deutsche Freie Software Lizenz	D-FSL-1.0	http://spdx.org/licenses/D-FSL-1.0.html		t
106	diffmark license	diffmark	http://spdx.org/licenses/diffmark.html		t
107	Do What The F*ck You Want To Public License	WTFPL	http://spdx.org/licenses/WTFPL.html		t
108	DOC License	DOC	http://spdx.org/licenses/DOC.html		t
109	Dotseqn License	Dotseqn	http://spdx.org/licenses/Dotseqn.html		t
110	DSDP License	DSDP	http://spdx.org/licenses/DSDP.html		t
111	dvipdfm License	dvipdfm	http://spdx.org/licenses/dvipdfm.html		t
112	Eclipse Public License 1.0	EPL-1.0	http://spdx.org/licenses/EPL-1.0.html		t
113	Educational Community License v1.0	ECL-1.0	http://spdx.org/licenses/ECL-1.0.html		t
114	Educational Community License v2.0	ECL-2.0	http://spdx.org/licenses/ECL-2.0.html		t
115	eGenix.com Public License 1.1.0	eGenix	http://spdx.org/licenses/eGenix.html		t
116	Eiffel Forum License v1.0	EFL-1.0	http://spdx.org/licenses/EFL-1.0.html		t
117	Eiffel Forum License v2.0	EFL-2.0	http://spdx.org/licenses/EFL-2.0.html		t
118	Enlightenment License (e16)	MIT-advertising	http://spdx.org/licenses/MIT-advertising.html		t
119	enna License	MIT-enna	http://spdx.org/licenses/MIT-enna.html		t
120	Entessa Public License v1.0	Entessa	http://spdx.org/licenses/Entessa.html		t
121	Erlang Public License v1.1	ErlPL-1.1	http://spdx.org/licenses/ErlPL-1.1.html		t
122	EU DataGrid Software License	EUDatagrid	http://spdx.org/licenses/EUDatagrid.html		t
123	European Union Public License 1.0	EUPL-1.0	http://spdx.org/licenses/EUPL-1.0.html		t
124	European Union Public License 1.1	EUPL-1.1	http://spdx.org/licenses/EUPL-1.1.html		t
125	Eurosym License	Eurosym	http://spdx.org/licenses/Eurosym.html		t
126	Fair License	Fair	http://spdx.org/licenses/Fair.html		t
127	feh License	MIT-feh	http://spdx.org/licenses/MIT-feh.html		t
128	Frameworx Open License 1.0	Frameworx-1.0	http://spdx.org/licenses/Frameworx-1.0.html		t
129	FreeImage Public License v1.0	FreeImage	http://spdx.org/licenses/FreeImage.html		t
130	Freetype Project License	FTL	http://spdx.org/licenses/FTL.html		t
131	FSF Unlimited License	FSFUL	http://spdx.org/licenses/FSFUL.html		t
132	FSF Unlimited License (with License Retention)	FSFULLR	http://spdx.org/licenses/FSFULLR.html		t
133	Giftware License	Giftware	http://spdx.org/licenses/Giftware.html		t
134	GL2PS License	GL2PS	http://spdx.org/licenses/GL2PS.html		t
135	Glulxe License	Glulxe	http://spdx.org/licenses/Glulxe.html		t
136	GNU Affero General Public License v3.0	AGPL-3.0	http://spdx.org/licenses/AGPL-3.0.html		t
137	GNU Free Documentation License v1.1	GFDL-1.1	http://spdx.org/licenses/GFDL-1.1.html		t
138	GNU Free Documentation License v1.2	GFDL-1.2	http://spdx.org/licenses/GFDL-1.2.html		t
139	GNU Free Documentation License v1.3	GFDL-1.3	http://spdx.org/licenses/GFDL-1.3.html		t
140	GNU General Public License v1.0 only	GPL-1.0	http://spdx.org/licenses/GPL-1.0.html		t
141	GNU General Public License v2.0 only	GPL-2.0	http://spdx.org/licenses/GPL-2.0.html		t
142	GNU General Public License v3.0 only	GPL-3.0	http://spdx.org/licenses/GPL-3.0.html		t
143	GNU Lesser General Public License v2.1 only	LGPL-2.1	http://spdx.org/licenses/LGPL-2.1.html		t
144	GNU Lesser General Public License v3.0 only	LGPL-3.0	http://spdx.org/licenses/LGPL-3.0.html		t
145	GNU Library General Public License v2 only	LGPL-2.0	http://spdx.org/licenses/LGPL-2.0.html		t
146	gnuplot License	gnuplot	http://spdx.org/licenses/gnuplot.html		t
147	gSOAP Public License v1.3b	gSOAP-1.3b	http://spdx.org/licenses/gSOAP-1.3b.html		t
148	Haskell Language Report License	HaskellReport	http://spdx.org/licenses/HaskellReport.html		t
149	Historic Permission Notice and Disclaimer	HPND	http://spdx.org/licenses/HPND.html		t
150	IBM PowerPC Initialization and Boot Software	IBM-pibs	http://spdx.org/licenses/IBM-pibs.html		t
151	IBM Public License v1.0	IPL-1.0	http://spdx.org/licenses/IPL-1.0.html		t
152	ICU License	ICU	http://spdx.org/licenses/ICU.html		t
153	ImageMagick License	ImageMagick	http://spdx.org/licenses/ImageMagick.html		t
154	iMatix Standard Function Library Agreement	iMatix	http://spdx.org/licenses/iMatix.html		t
155	Imlib2 License	Imlib2	http://spdx.org/licenses/Imlib2.html		t
156	Independent JPEG Group License	IJG	http://spdx.org/licenses/IJG.html		t
157	Intel ACPI Software License Agreement	Intel-ACPI	http://spdx.org/licenses/Intel-ACPI.html		t
158	Intel Open Source License	Intel	http://spdx.org/licenses/Intel.html		t
159	Interbase Public License v1.0	Interbase-1.0	http://spdx.org/licenses/Interbase-1.0.html		t
160	IPA Font License	IPA	http://spdx.org/licenses/IPA.html		t
161	ISC License	ISC	http://spdx.org/licenses/ISC.html		t
162	JasPer License	JasPer-2.0	http://spdx.org/licenses/JasPer-2.0.html		t
163	JSON License	JSON	http://spdx.org/licenses/JSON.html		t
164	LaTeX Project Public License 1.3a	LPPL-1.3a	http://spdx.org/licenses/LPPL-1.3a.html		t
165	LaTeX Project Public License v1.0	LPPL-1.0	http://spdx.org/licenses/LPPL-1.0.html		t
166	LaTeX Project Public License v1.1	LPPL-1.1	http://spdx.org/licenses/LPPL-1.1.html		t
167	LaTeX Project Public License v1.2	LPPL-1.2	http://spdx.org/licenses/LPPL-1.2.html		t
168	LaTeX Project Public License v1.3c	LPPL-1.3c	http://spdx.org/licenses/LPPL-1.3c.html		t
169	Latex2e License	Latex2e	http://spdx.org/licenses/Latex2e.html		t
170	Lawrence Berkeley National Labs BSD variant license	BSD-3-Clause-LBNL	http://spdx.org/licenses/BSD-3-Clause-LBNL.html		t
171	Leptonica License	Leptonica	http://spdx.org/licenses/Leptonica.html		t
172	Lesser General Public License For Linguistic Resources	LGPLLR	http://spdx.org/licenses/LGPLLR.html		t
173	libpng License	Libpng	http://spdx.org/licenses/Libpng.html		t
174	libtiff License	libtiff	http://spdx.org/licenses/libtiff.html		t
175	Lucent Public License v1.02	LPL-1.02	http://spdx.org/licenses/LPL-1.02.html		t
176	Lucent Public License Version 1.0	LPL-1.0	http://spdx.org/licenses/LPL-1.0.html		t
177	MakeIndex License	MakeIndex	http://spdx.org/licenses/MakeIndex.html		t
178	Matrix Template Library License	MTLL	http://spdx.org/licenses/MTLL.html		t
179	Microsoft Public License	MS-PL	http://spdx.org/licenses/MS-PL.html		t
180	Microsoft Reciprocal License	MS-RL	http://spdx.org/licenses/MS-RL.html		t
181	MirOS Licence	MirOS	http://spdx.org/licenses/MirOS.html		t
182	MIT +no-false-attribs license	MITNFA	http://spdx.org/licenses/MITNFA.html		t
183	MIT License	MIT	http://spdx.org/licenses/MIT.html		t
184	Motosoto License	Motosoto	http://spdx.org/licenses/Motosoto.html		t
185	Mozilla Public License 1.0	MPL-1.0	http://spdx.org/licenses/MPL-1.0.html		t
186	Mozilla Public License 1.1	MPL-1.1	http://spdx.org/licenses/MPL-1.1.html		t
187	Mozilla Public License 2.0	MPL-2.0	http://spdx.org/licenses/MPL-2.0.html		t
188	Mozilla Public License 2.0 (no copyleft exception)	MPL-2.0-no-copyleft-exception	http://spdx.org/licenses/MPL-2.0-no-copyleft-exception.html		t
189	mpich2 License	mpich2	http://spdx.org/licenses/mpich2.html		t
190	Multics License	Multics	http://spdx.org/licenses/Multics.html		t
191	Mup License	Mup	http://spdx.org/licenses/Mup.html		t
192	NASA Open Source Agreement 1.3	NASA-1.3	http://spdx.org/licenses/NASA-1.3.html		t
193	Naumen Public License	Naumen	http://spdx.org/licenses/Naumen.html		t
194	Net Boolean Public License v1	NBPL-1.0	http://spdx.org/licenses/NBPL-1.0.html		t
195	NetCDF license	NetCDF	http://spdx.org/licenses/NetCDF.html		t
196	Nethack General Public License	NGPL	http://spdx.org/licenses/NGPL.html		t
197	Netizen Open Source License	NOSL	http://spdx.org/licenses/NOSL.html		t
198	Netscape Public License v1.0	NPL-1.0	http://spdx.org/licenses/NPL-1.0.html		t
199	Netscape Public License v1.1	NPL-1.1	http://spdx.org/licenses/NPL-1.1.html		t
200	Newsletr License	Newsletr	http://spdx.org/licenses/Newsletr.html		t
201	No Limit Public License	NLPL	http://spdx.org/licenses/NLPL.html		t
202	Nokia Open Source License	Nokia	http://spdx.org/licenses/Nokia.html		t
203	Non-Profit Open Software License 3.0	NPOSL-3.0	http://spdx.org/licenses/NPOSL-3.0.html		t
204	Noweb License	Noweb	http://spdx.org/licenses/Noweb.html		t
205	NRL License	NRL	http://spdx.org/licenses/NRL.html		t
206	NTP License	NTP	http://spdx.org/licenses/NTP.html		t
207	Nunit License	Nunit	http://spdx.org/licenses/Nunit.html		t
208	OCLC Research Public License 2.0	OCLC-2.0	http://spdx.org/licenses/OCLC-2.0.html		t
209	ODC Open Database License v1.0	ODbL-1.0	http://spdx.org/licenses/ODbL-1.0.html		t
210	ODC Public Domain Dedication &amp; License 1.0	PDDL-1.0	http://spdx.org/licenses/PDDL-1.0.html		t
211	Open Group Test Suite License	OGTSL	http://spdx.org/licenses/OGTSL.html		t
212	Open LDAP Public License  2.2.2	OLDAP-2.2.2	http://spdx.org/licenses/OLDAP-2.2.2.html		t
213	Open LDAP Public License v1.1	OLDAP-1.1	http://spdx.org/licenses/OLDAP-1.1.html		t
214	Open LDAP Public License v1.2	OLDAP-1.2	http://spdx.org/licenses/OLDAP-1.2.html		t
215	Open LDAP Public License v1.3	OLDAP-1.3	http://spdx.org/licenses/OLDAP-1.3.html		t
216	Open LDAP Public License v1.4	OLDAP-1.4	http://spdx.org/licenses/OLDAP-1.4.html		t
217	Open LDAP Public License v2.0 (or possibly 2.0A and 2.0B)	OLDAP-2.0	http://spdx.org/licenses/OLDAP-2.0.html		t
218	Open LDAP Public License v2.0.1	OLDAP-2.0.1	http://spdx.org/licenses/OLDAP-2.0.1.html		t
219	Open LDAP Public License v2.1	OLDAP-2.1	http://spdx.org/licenses/OLDAP-2.1.html		t
220	Open LDAP Public License v2.2	OLDAP-2.2	http://spdx.org/licenses/OLDAP-2.2.html		t
221	Open LDAP Public License v2.2.1	OLDAP-2.2.1	http://spdx.org/licenses/OLDAP-2.2.1.html		t
222	Open LDAP Public License v2.3	OLDAP-2.3	http://spdx.org/licenses/OLDAP-2.3.html		t
223	Open LDAP Public License v2.4	OLDAP-2.4	http://spdx.org/licenses/OLDAP-2.4.html		t
224	Open LDAP Public License v2.5	OLDAP-2.5	http://spdx.org/licenses/OLDAP-2.5.html		t
225	Open LDAP Public License v2.6	OLDAP-2.6	http://spdx.org/licenses/OLDAP-2.6.html		t
226	Open LDAP Public License v2.7	OLDAP-2.7	http://spdx.org/licenses/OLDAP-2.7.html		t
227	Open LDAP Public License v2.8	OLDAP-2.8	http://spdx.org/licenses/OLDAP-2.8.html		t
228	Open Market License	OML	http://spdx.org/licenses/OML.html		t
229	Open Public License v1.0	OPL-1.0	http://spdx.org/licenses/OPL-1.0.html		t
230	Open Software License 1.0	OSL-1.0	http://spdx.org/licenses/OSL-1.0.html		t
231	Open Software License 1.1	OSL-1.1	http://spdx.org/licenses/OSL-1.1.html		t
232	Open Software License 2.0	OSL-2.0	http://spdx.org/licenses/OSL-2.0.html		t
233	Open Software License 2.1	OSL-2.1	http://spdx.org/licenses/OSL-2.1.html		t
234	Open Software License 3.0	OSL-3.0	http://spdx.org/licenses/OSL-3.0.html		t
235	OpenSSL License	OpenSSL	http://spdx.org/licenses/OpenSSL.html		t
236	PHP License v3.0	PHP-3.0	http://spdx.org/licenses/PHP-3.0.html		t
237	PHP License v3.01	PHP-3.01	http://spdx.org/licenses/PHP-3.01.html		t
238	Plexus Classworlds License	Plexus	http://spdx.org/licenses/Plexus.html		t
239	PostgreSQL License	PostgreSQL	http://spdx.org/licenses/PostgreSQL.html		t
240	psfrag License	psfrag	http://spdx.org/licenses/psfrag.html		t
241	psutils License	psutils	http://spdx.org/licenses/psutils.html		t
242	Python License 2.0	Python-2.0	http://spdx.org/licenses/Python-2.0.html		t
243	Q Public License 1.0	QPL-1.0	http://spdx.org/licenses/QPL-1.0.html		t
244	Qhull License	Qhull	http://spdx.org/licenses/Qhull.html		t
245	Rdisc License	Rdisc	http://spdx.org/licenses/Rdisc.html		t
246	RealNetworks Public Source License v1.0	RPSL-1.0	http://spdx.org/licenses/RPSL-1.0.html		t
247	Reciprocal Public License 1.1	RPL-1.1	http://spdx.org/licenses/RPL-1.1.html		t
248	Reciprocal Public License 1.5	RPL-1.5	http://spdx.org/licenses/RPL-1.5.html		t
249	Red Hat eCos Public License v1.1	RHeCos-1.1	http://spdx.org/licenses/RHeCos-1.1.html		t
250	Ricoh Source Code Public License	RSCPL	http://spdx.org/licenses/RSCPL.html		t
251	RSA Message-Digest License 	RSA-MD	http://spdx.org/licenses/RSA-MD.html		t
252	Ruby License	Ruby	http://spdx.org/licenses/Ruby.html		t
253	Sax Public Domain Notice	SAX-PD	http://spdx.org/licenses/SAX-PD.html		t
254	Saxpath License	Saxpath	http://spdx.org/licenses/Saxpath.html		t
255	SCEA Shared Source License	SCEA	http://spdx.org/licenses/SCEA.html		t
256	Scheme Widget Library (SWL) Software License Agreement	SWL	http://spdx.org/licenses/SWL.html		t
257	Sendmail License	Sendmail	http://spdx.org/licenses/Sendmail.html		t
258	SGI Free Software License B v1.0	SGI-B-1.0	http://spdx.org/licenses/SGI-B-1.0.html		t
259	SGI Free Software License B v1.1	SGI-B-1.1	http://spdx.org/licenses/SGI-B-1.1.html		t
260	SGI Free Software License B v2.0	SGI-B-2.0	http://spdx.org/licenses/SGI-B-2.0.html		t
261	SIL Open Font License 1.0	OFL-1.0	http://spdx.org/licenses/OFL-1.0.html		t
262	SIL Open Font License 1.1	OFL-1.1	http://spdx.org/licenses/OFL-1.1.html		t
263	Simple Public License 2.0	SimPL-2.0	http://spdx.org/licenses/SimPL-2.0.html		t
264	Sleepycat License	Sleepycat	http://spdx.org/licenses/Sleepycat.html		t
265	SNIA Public License 1.1	SNIA	http://spdx.org/licenses/SNIA.html		t
266	Spencer License 86	Spencer-86	http://spdx.org/licenses/Spencer-86.html		t
267	Spencer License 94	Spencer-94	http://spdx.org/licenses/Spencer-94.html		t
268	Spencer License 99	Spencer-99	http://spdx.org/licenses/Spencer-99.html		t
269	Standard ML of New Jersey License	SMLNJ	http://spdx.org/licenses/SMLNJ.html		t
270	SugarCRM Public License v1.1.3	SugarCRM-1.1.3	http://spdx.org/licenses/SugarCRM-1.1.3.html		t
271	Sun Industry Standards Source License v1.1	SISSL	http://spdx.org/licenses/SISSL.html		t
272	Sun Industry Standards Source License v1.2	SISSL-1.2	http://spdx.org/licenses/SISSL-1.2.html		t
273	Sun Public License v1.0	SPL-1.0	http://spdx.org/licenses/SPL-1.0.html		t
274	Sybase Open Watcom Public License 1.0	Watcom-1.0	http://spdx.org/licenses/Watcom-1.0.html		t
275	TCL/TK License	TCL	http://spdx.org/licenses/TCL.html		t
276	The Unlicense	Unlicense	http://spdx.org/licenses/Unlicense.html		t
277	TMate Open Source License	TMate	http://spdx.org/licenses/TMate.html		t
278	TORQUE v2.5+ Software License v1.1	TORQUE-1.1	http://spdx.org/licenses/TORQUE-1.1.html		t
279	Trusster Open Source License	TOSL	http://spdx.org/licenses/TOSL.html		t
280	Unicode Terms of Use	Unicode-TOU	http://spdx.org/licenses/Unicode-TOU.html		t
281	Universal Permissive License v1.0	UPL-1.0	http://spdx.org/licenses/UPL-1.0.html		t
282	University of Illinois/NCSA Open Source License	NCSA	http://spdx.org/licenses/NCSA.html		t
283	Vim License	Vim	http://spdx.org/licenses/Vim.html		t
284	VOSTROM Public License for Open Source	VOSTROM	http://spdx.org/licenses/VOSTROM.html		t
285	Vovida Software License v1.0	VSL-1.0	http://spdx.org/licenses/VSL-1.0.html		t
286	W3C Software Notice and License (1998-07-20)	W3C-19980720	http://spdx.org/licenses/W3C-19980720.html		t
287	W3C Software Notice and License (2002-12-31)	W3C	http://spdx.org/licenses/W3C.html		t
288	Wsuipa License	Wsuipa	http://spdx.org/licenses/Wsuipa.html		t
289	X.Net License	Xnet	http://spdx.org/licenses/Xnet.html		t
290	X11 License	X11	http://spdx.org/licenses/X11.html		t
291	Xerox License	Xerox	http://spdx.org/licenses/Xerox.html		t
292	XFree86 License 1.1	XFree86-1.1	http://spdx.org/licenses/XFree86-1.1.html		t
293	xinetd License	xinetd	http://spdx.org/licenses/xinetd.html		t
294	XPP License	xpp	http://spdx.org/licenses/xpp.html		t
295	XSkat License	XSkat	http://spdx.org/licenses/XSkat.html		t
296	Yahoo! Public License v1.0	YPL-1.0	http://spdx.org/licenses/YPL-1.0.html		t
297	Yahoo! Public License v1.1	YPL-1.1	http://spdx.org/licenses/YPL-1.1.html		t
298	Zed License	Zed	http://spdx.org/licenses/Zed.html		t
299	Zend License v2.0	Zend-2.0	http://spdx.org/licenses/Zend-2.0.html		t
300	Zimbra Public License v1.3	Zimbra-1.3	http://spdx.org/licenses/Zimbra-1.3.html		t
301	Zimbra Public License v1.4	Zimbra-1.4	http://spdx.org/licenses/Zimbra-1.4.html		t
302	zlib License	Zlib	http://spdx.org/licenses/Zlib.html		t
303	zlib/libpng License with Acknowledgement	zlib-acknowledgement	http://spdx.org/licenses/zlib-acknowledgement.html		t
304	Zope Public License 1.1	ZPL-1.1	http://spdx.org/licenses/ZPL-1.1.html		t
305	Zope Public License 2.0	ZPL-2.0	http://spdx.org/licenses/ZPL-2.0.html		t
306	Zope Public License 2.1	ZPL-2.1	http://spdx.org/licenses/ZPL-2.1.html		t
307	eCos license version 2.0	eCos-2.0	http://spdx.org/licenses/eCos-2.0		t
308	GNU General Public License v1.0 or later	GPL-1.0+	http://spdx.org/licenses/GPL-1.0+		t
309	GNU General Public License v2.0 or later	GPL-2.0+	http://spdx.org/licenses/GPL-2.0+		t
310	GNU General Public License v2.0 w/Autoconf exception	GPL-2.0-with-autoconf-exception	http://spdx.org/licenses/GPL-2.0-with-autoconf-exception		t
311	GNU General Public License v2.0 w/Bison exception	GPL-2.0-with-bison-exception	http://spdx.org/licenses/GPL-2.0-with-bison-exception		t
312	GNU General Public License v2.0 w/Classpath exception	GPL-2.0-with-classpath-exception	http://spdx.org/licenses/GPL-2.0-with-classpath-exception		t
313	GNU General Public License v2.0 w/Font exception	GPL-2.0-with-font-exception	http://spdx.org/licenses/GPL-2.0-with-font-exception		t
314	GNU General Public License v2.0 w/GCC Runtime Library exception	GPL-2.0-with-GCC-exception	http://spdx.org/licenses/GPL-2.0-with-GCC-exception		t
315	GNU General Public License v3.0 or later	GPL-3.0+	http://spdx.org/licenses/GPL-3.0+		t
316	GNU General Public License v3.0 w/Autoconf exception	GPL-3.0-with-autoconf-exception	http://spdx.org/licenses/GPL-3.0-with-autoconf-exception		t
317	GNU General Public License v3.0 w/GCC Runtime Library exception	GPL-3.0-with-GCC-exception	http://spdx.org/licenses/GPL-3.0-with-GCC-exception		t
318	GNU Lesser General Public License v2.1 or later	LGPL-2.1+	http://spdx.org/licenses/LGPL-2.1+		t
319	GNU Lesser General Public License v3.0 or later	LGPL-3.0+	http://spdx.org/licenses/LGPL-3.0+		t
320	GNU Library General Public License v2 or later	LGPL-2.0+	http://spdx.org/licenses/LGPL-2.0+		t
321	Standard ML of New Jersey License	StandardML-NJ	http://spdx.org/licenses/StandardML-NJ		t
322	wxWindows Library License	WXwindows	http://spdx.org/licenses/WXwindows		t
\.


--
-- Data for Name: packages; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.packages (package_id, name, version, file_name, supplier_id, originator_id, download_location, verification_code, ver_code_excluded_file_id, sha256, home_page, source_info, concluded_license_id, declared_license_id, license_comment, copyright_text, summary, description, comment, dosocs2_dir_code) FROM stdin;
\.


--
-- Data for Name: packages_files; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.packages_files (package_file_id, package_id, file_id, concluded_license_id, license_comment, file_name) FROM stdin;
\.


--
-- Data for Name: packages_scans; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.packages_scans (package_scan_id, package_id, scanner_id) FROM stdin;
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.projects (package_id, name, homepage, uri) FROM stdin;
\.


--
-- Data for Name: relationship_types; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.relationship_types (relationship_type_id, name) FROM stdin;
1	DESCRIBES
2	DESCRIBED_BY
3	CONTAINS
4	CONTAINED_BY
5	GENERATES
6	GENERATED_FROM
7	ANCESTOR_OF
8	DESCENDANT_OF
9	VARIANT_OF
10	DISTRIBUTION_ARTIFACT
11	PATCH_FOR
12	PATCH_APPLIED
13	COPY_OF
14	FILE_ADDED
15	FILE_DELETED
16	FILE_MODIFIED
17	EXPANDED_FROM_ARCHIVE
18	DYNAMIC_LINK
19	STATIC_LINK
20	DATA_FILE_OF
21	TEST_CASE_OF
22	BUILD_TOOL_OF
23	DOCUMENTATION_OF
24	OPTIONAL_COMPONENT_OF
25	METAFILE_OF
26	PACKAGE_OF
27	AMENDS
28	PREREQUISITE_FOR
29	HAS_PREREQUISITE
30	OTHER
\.


--
-- Data for Name: relationships; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.relationships (relationship_id, left_identifier_id, right_identifier_id, relationship_type_id, relationship_comment) FROM stdin;
\.


--
-- Data for Name: sbom_scans; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.sbom_scans (repo_id, sbom_scan) FROM stdin;
\.


--
-- Data for Name: scanners; Type: TABLE DATA; Schema: spdx; Owner: augur
--

COPY spdx.scanners (scanner_id, name) FROM stdin;
\.


--
-- Name: augur_data.repo_insights_ri_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data."augur_data.repo_insights_ri_id_seq"', 25430, false);


--
-- Name: chaoss_metric_status_cms_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.chaoss_metric_status_cms_id_seq', 1, false);


--
-- Name: chaoss_user_chaoss_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.chaoss_user_chaoss_id_seq', 1, false);


--
-- Name: commit_comment_ref_cmt_comment_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.commit_comment_ref_cmt_comment_id_seq', 25430, false);


--
-- Name: commit_parents_parent_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.commit_parents_parent_id_seq', 25430, false);


--
-- Name: commits_cmt_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.commits_cmt_id_seq', 25430, false);


--
-- Name: contributor_affiliations_ca_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.contributor_affiliations_ca_id_seq', 25430, false);


--
-- Name: contributor_repo_cntrb_repo_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.contributor_repo_cntrb_repo_id_seq', 1, false);


--
-- Name: contributors_aliases_cntrb_a_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.contributors_aliases_cntrb_a_id_seq', 25430, false);


--
-- Name: contributors_aliases_cntrb_alias_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.contributors_aliases_cntrb_alias_id_seq', 1, false);


--
-- Name: contributors_cntrb_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.contributors_cntrb_id_seq', 25430, false);


--
-- Name: contributors_history_cntrb_history_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.contributors_history_cntrb_history_id_seq', 25430, false);


--
-- Name: discourse_insights_msg_discourse_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.discourse_insights_msg_discourse_id_seq', 1, false);


--
-- Name: discourse_insights_msg_discourse_id_seq1; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.discourse_insights_msg_discourse_id_seq1', 1, false);


--
-- Name: issue_assignees_issue_assignee_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.issue_assignees_issue_assignee_id_seq', 1, false);


--
-- Name: issue_events_event_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.issue_events_event_id_seq', 25430, false);


--
-- Name: issue_labels_issue_label_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.issue_labels_issue_label_id_seq', 25430, false);


--
-- Name: issue_message_ref_issue_msg_ref_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.issue_message_ref_issue_msg_ref_id_seq', 25430, false);


--
-- Name: issue_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.issue_seq', 31000, false);


--
-- Name: libraries_library_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.libraries_library_id_seq', 25430, false);


--
-- Name: library_dependencies_lib_dependency_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.library_dependencies_lib_dependency_id_seq', 25430, false);


--
-- Name: library_version_library_version_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.library_version_library_version_id_seq', 25430, false);


--
-- Name: lstm_anomaly_models_model_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.lstm_anomaly_models_model_id_seq', 1, false);


--
-- Name: lstm_anomaly_results_result_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.lstm_anomaly_results_result_id_seq', 1, false);


--
-- Name: message_analysis_msg_analysis_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.message_analysis_msg_analysis_id_seq', 1, false);


--
-- Name: message_analysis_summary_msg_summary_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.message_analysis_summary_msg_summary_id_seq', 1, false);


--
-- Name: message_msg_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.message_msg_id_seq', 25430, false);


--
-- Name: message_sentiment_msg_analysis_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.message_sentiment_msg_analysis_id_seq', 1, false);


--
-- Name: message_sentiment_summary_msg_summary_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.message_sentiment_summary_msg_summary_id_seq', 1, false);


--
-- Name: platform_pltfrm_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.platform_pltfrm_id_seq', 25430, false);


--
-- Name: pull_request_analysis_pull_request_analysis_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_analysis_pull_request_analysis_id_seq', 1, false);


--
-- Name: pull_request_assignees_pr_assignee_map_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_assignees_pr_assignee_map_id_seq', 25430, false);


--
-- Name: pull_request_commits_pr_cmt_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_commits_pr_cmt_id_seq', 1, false);


--
-- Name: pull_request_events_pr_event_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_events_pr_event_id_seq', 25430, false);


--
-- Name: pull_request_files_pr_file_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_files_pr_file_id_seq', 25150, false);


--
-- Name: pull_request_labels_pr_label_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_labels_pr_label_id_seq', 25430, false);


--
-- Name: pull_request_message_ref_pr_msg_ref_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_message_ref_pr_msg_ref_id_seq', 25430, false);


--
-- Name: pull_request_meta_pr_repo_meta_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_meta_pr_repo_meta_id_seq', 25430, false);


--
-- Name: pull_request_repo_pr_repo_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_repo_pr_repo_id_seq', 25430, false);


--
-- Name: pull_request_review_message_ref_pr_review_msg_ref_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_review_message_ref_pr_review_msg_ref_id_seq', 1, false);


--
-- Name: pull_request_reviewers_pr_reviewer_map_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_reviewers_pr_reviewer_map_id_seq', 25430, false);


--
-- Name: pull_request_reviews_pr_review_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_reviews_pr_review_id_seq', 1, false);


--
-- Name: pull_request_teams_pr_team_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_request_teams_pr_team_id_seq', 25430, false);


--
-- Name: pull_requests_pull_request_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.pull_requests_pull_request_id_seq', 25430, false);


--
-- Name: releases_release_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.releases_release_id_seq', 1, false);


--
-- Name: repo_badging_badge_collection_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_badging_badge_collection_id_seq', 25012, false);


--
-- Name: repo_clones_data_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_clones_data_id_seq', 1, false);


--
-- Name: repo_cluster_messages_msg_cluster_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_cluster_messages_msg_cluster_id_seq', 1, false);


--
-- Name: repo_dependencies_repo_dependencies_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_dependencies_repo_dependencies_id_seq', 1, false);


--
-- Name: repo_deps_libyear_repo_deps_libyear_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_deps_libyear_repo_deps_libyear_id_seq', 1, false);


--
-- Name: repo_deps_scorecard_repo_deps_scorecard_id_seq1; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_deps_scorecard_repo_deps_scorecard_id_seq1', 1, false);


--
-- Name: repo_group_insights_rgi_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_group_insights_rgi_id_seq', 25430, false);


--
-- Name: repo_groups_list_serve_rgls_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_groups_list_serve_rgls_id_seq', 25430, false);


--
-- Name: repo_groups_repo_group_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_groups_repo_group_id_seq', 25430, true);


--
-- Name: repo_info_repo_info_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_info_repo_info_id_seq', 25430, false);


--
-- Name: repo_insights_records_ri_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_insights_records_ri_id_seq', 1, false);


--
-- Name: repo_insights_ri_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_insights_ri_id_seq', 1, false);


--
-- Name: repo_labor_repo_labor_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_labor_repo_labor_id_seq', 25430, false);


--
-- Name: repo_meta_rmeta_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_meta_rmeta_id_seq', 25430, false);


--
-- Name: repo_repo_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_repo_id_seq', 25480, false);


--
-- Name: repo_sbom_scans_rsb_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_sbom_scans_rsb_id_seq', 25430, false);


--
-- Name: repo_stats_rstat_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_stats_rstat_id_seq', 25430, false);


--
-- Name: repo_test_coverage_repo_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_test_coverage_repo_id_seq', 1, false);


--
-- Name: repo_topic_repo_topic_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.repo_topic_repo_topic_id_seq', 1, false);


--
-- Name: topic_words_topic_words_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.topic_words_topic_words_id_seq', 1, false);


--
-- Name: unresolved_commit_emails_email_unresolved_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.unresolved_commit_emails_email_unresolved_id_seq', 1, false);


--
-- Name: utility_log_id_seq; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.utility_log_id_seq', 1, false);


--
-- Name: utility_log_id_seq1; Type: SEQUENCE SET; Schema: augur_data; Owner: augur
--

SELECT pg_catalog.setval('augur_data.utility_log_id_seq1', 1, false);


--
-- Name: affiliations_corp_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.affiliations_corp_id_seq', 620000, false);


--
-- Name: augur_settings_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.augur_settings_id_seq', 1, false);


--
-- Name: config_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.config_id_seq', 50, true);


--
-- Name: gh_worker_history_history_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.gh_worker_history_history_id_seq', 15000, false);


--
-- Name: subscription_types_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.subscription_types_id_seq', 1, false);


--
-- Name: user_groups_group_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.user_groups_group_id_seq', 2, false);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.users_user_id_seq', 2, false);


--
-- Name: worker_oauth_oauth_id_seq; Type: SEQUENCE SET; Schema: augur_operations; Owner: augur
--

SELECT pg_catalog.setval('augur_operations.worker_oauth_oauth_id_seq', 1000, false);


--
-- Name: annotation_types_annotation_type_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.annotation_types_annotation_type_id_seq', 1, false);


--
-- Name: annotations_annotation_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.annotations_annotation_id_seq', 1, false);


--
-- Name: augur_repo_map_map_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.augur_repo_map_map_id_seq', 1, false);


--
-- Name: creator_types_creator_type_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.creator_types_creator_type_id_seq', 1, false);


--
-- Name: creators_creator_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.creators_creator_id_seq', 1, false);


--
-- Name: document_namespaces_document_namespace_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.document_namespaces_document_namespace_id_seq', 1, false);


--
-- Name: documents_creators_document_creator_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.documents_creators_document_creator_id_seq', 1, false);


--
-- Name: documents_document_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.documents_document_id_seq', 1, false);


--
-- Name: external_refs_external_ref_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.external_refs_external_ref_id_seq', 1, false);


--
-- Name: file_contributors_file_contributor_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.file_contributors_file_contributor_id_seq', 1, false);


--
-- Name: file_types_file_type_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.file_types_file_type_id_seq', 1, false);


--
-- Name: files_file_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.files_file_id_seq', 1, false);


--
-- Name: files_licenses_file_license_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.files_licenses_file_license_id_seq', 1, false);


--
-- Name: files_scans_file_scan_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.files_scans_file_scan_id_seq', 1, false);


--
-- Name: identifiers_identifier_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.identifiers_identifier_id_seq', 1, false);


--
-- Name: licenses_license_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.licenses_license_id_seq', 1, false);


--
-- Name: packages_files_package_file_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.packages_files_package_file_id_seq', 1, false);


--
-- Name: packages_package_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.packages_package_id_seq', 1, false);


--
-- Name: packages_scans_package_scan_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.packages_scans_package_scan_id_seq', 1, false);


--
-- Name: projects_package_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.projects_package_id_seq', 1, false);


--
-- Name: relationship_types_relationship_type_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.relationship_types_relationship_type_id_seq', 1, false);


--
-- Name: relationships_relationship_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.relationships_relationship_id_seq', 1, false);


--
-- Name: scanners_scanner_id_seq; Type: SEQUENCE SET; Schema: spdx; Owner: augur
--

SELECT pg_catalog.setval('spdx.scanners_scanner_id_seq', 1, false);


--
-- Name: contributors GL-UNIQUE-B; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributors
    ADD CONSTRAINT "GL-UNIQUE-B" UNIQUE (gl_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: contributors GL-UNIQUE-C; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributors
    ADD CONSTRAINT "GL-UNIQUE-C" UNIQUE (gl_username) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_assignees assigniees-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_assignees
    ADD CONSTRAINT "assigniees-unique" UNIQUE (pull_request_id, pr_assignee_src_id);


--
-- Name: chaoss_metric_status chaoss_metric_status_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.chaoss_metric_status
    ADD CONSTRAINT chaoss_metric_status_pkey PRIMARY KEY (cms_id);


--
-- Name: chaoss_user chaoss_unique_email_key; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.chaoss_user
    ADD CONSTRAINT chaoss_unique_email_key UNIQUE (chaoss_email);


--
-- Name: chaoss_user chaoss_user_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.chaoss_user
    ADD CONSTRAINT chaoss_user_pkey PRIMARY KEY (chaoss_id);


--
-- Name: contributor_repo cntrb_repo_id_key; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributor_repo
    ADD CONSTRAINT cntrb_repo_id_key PRIMARY KEY (cntrb_repo_id);


--
-- Name: commit_comment_ref commit_comment_ref_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commit_comment_ref
    ADD CONSTRAINT commit_comment_ref_pkey PRIMARY KEY (cmt_comment_id);


--
-- Name: commit_parents commit_parents_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commit_parents
    ADD CONSTRAINT commit_parents_pkey PRIMARY KEY (cmt_id, parent_id);


--
-- Name: commit_comment_ref commitcomment; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commit_comment_ref
    ADD CONSTRAINT commitcomment UNIQUE (cmt_comment_src_id);


--
-- Name: commits commits_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commits
    ADD CONSTRAINT commits_pkey PRIMARY KEY (cmt_id);


--
-- Name: contributors_aliases contributor-alias-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributors_aliases
    ADD CONSTRAINT "contributor-alias-unique" UNIQUE (alias_email);


--
-- Name: contributor_affiliations contributor_affiliations_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributor_affiliations
    ADD CONSTRAINT contributor_affiliations_pkey PRIMARY KEY (ca_id);


--
-- Name: contributors contributors-pk; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributors
    ADD CONSTRAINT "contributors-pk" PRIMARY KEY (cntrb_id);


--
-- Name: contributors_aliases contributors_aliases_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributors_aliases
    ADD CONSTRAINT contributors_aliases_pkey PRIMARY KEY (cntrb_alias_id);


--
-- Name: repo_dependencies deps-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_dependencies
    ADD CONSTRAINT "deps-insert-unique" UNIQUE (repo_id, dep_name, data_collection_date);


--
-- Name: repo_deps_libyear deps-libyear-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_deps_libyear
    ADD CONSTRAINT "deps-libyear-insert-unique" UNIQUE (repo_id, name, data_collection_date);


--
-- Name: repo_deps_scorecard deps-scorecard-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_deps_scorecard
    ADD CONSTRAINT "deps-scorecard-insert-unique" UNIQUE (repo_id, name);


--
-- Name: discourse_insights discourse_insights_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.discourse_insights
    ADD CONSTRAINT discourse_insights_pkey PRIMARY KEY (msg_discourse_id);


--
-- Name: contributor_repo eventer; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributor_repo
    ADD CONSTRAINT eventer UNIQUE (event_id, tool_version);


--
-- Name: exclude exclude_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.exclude
    ADD CONSTRAINT exclude_pkey PRIMARY KEY (id);


--
-- Name: issue_assignees issue-assignee-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_assignees
    ADD CONSTRAINT "issue-assignee-insert-unique" UNIQUE (issue_assignee_src_id, issue_id);


--
-- Name: issues issue-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issues
    ADD CONSTRAINT "issue-insert-unique" UNIQUE (issue_url);


--
-- Name: issue_message_ref issue-message-ref-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_message_ref
    ADD CONSTRAINT "issue-message-ref-insert-unique" UNIQUE (issue_msg_ref_src_comment_id, issue_id);


--
-- Name: issue_assignees issue_assignees_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_assignees
    ADD CONSTRAINT issue_assignees_pkey PRIMARY KEY (issue_assignee_id);


--
-- Name: issue_events issue_events_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_events
    ADD CONSTRAINT issue_events_pkey PRIMARY KEY (event_id);


--
-- Name: issue_labels issue_labels_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_labels
    ADD CONSTRAINT issue_labels_pkey PRIMARY KEY (issue_label_id);


--
-- Name: issue_message_ref issue_message_ref_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_message_ref
    ADD CONSTRAINT issue_message_ref_pkey PRIMARY KEY (issue_msg_ref_id);


--
-- Name: issues issues_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issues
    ADD CONSTRAINT issues_pkey PRIMARY KEY (issue_id);


--
-- Name: libraries libraries_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.libraries
    ADD CONSTRAINT libraries_pkey PRIMARY KEY (library_id);


--
-- Name: library_dependencies library_dependencies_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.library_dependencies
    ADD CONSTRAINT library_dependencies_pkey PRIMARY KEY (lib_dependency_id);


--
-- Name: library_version library_version_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.library_version
    ADD CONSTRAINT library_version_pkey PRIMARY KEY (library_version_id);


--
-- Name: lstm_anomaly_models lstm_anomaly_models_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.lstm_anomaly_models
    ADD CONSTRAINT lstm_anomaly_models_pkey PRIMARY KEY (model_id);


--
-- Name: lstm_anomaly_results lstm_anomaly_results_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.lstm_anomaly_results
    ADD CONSTRAINT lstm_anomaly_results_pkey PRIMARY KEY (result_id);


--
-- Name: message message-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message
    ADD CONSTRAINT "message-insert-unique" UNIQUE (platform_msg_id, pltfrm_id);


--
-- Name: message_analysis message_analysis_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_analysis
    ADD CONSTRAINT message_analysis_pkey PRIMARY KEY (msg_analysis_id);


--
-- Name: message_analysis_summary message_analysis_summary_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_analysis_summary
    ADD CONSTRAINT message_analysis_summary_pkey PRIMARY KEY (msg_summary_id);


--
-- Name: message message_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message
    ADD CONSTRAINT message_pkey PRIMARY KEY (msg_id);


--
-- Name: message_sentiment message_sentiment_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_sentiment
    ADD CONSTRAINT message_sentiment_pkey PRIMARY KEY (msg_analysis_id);


--
-- Name: message_sentiment_summary message_sentiment_summary_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_sentiment_summary
    ADD CONSTRAINT message_sentiment_summary_pkey PRIMARY KEY (msg_summary_id);


--
-- Name: pull_request_events pr-unqiue-event; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_events
    ADD CONSTRAINT "pr-unqiue-event" UNIQUE (node_id);


--
-- Name: pull_request_commits pr_commit_nk; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_commits
    ADD CONSTRAINT pr_commit_nk UNIQUE (pull_request_id, repo_id, pr_cmt_sha);


--
-- Name: pull_request_events pr_events_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_events
    ADD CONSTRAINT pr_events_pkey PRIMARY KEY (pr_event_id);


--
-- Name: pull_request_review_message_ref pr_review_msg_ref_id; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_review_message_ref
    ADD CONSTRAINT pr_review_msg_ref_id PRIMARY KEY (pr_review_msg_ref_id);


--
-- Name: pull_request_reviews pr_review_unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviews
    ADD CONSTRAINT pr_review_unique UNIQUE (pr_review_src_id);


--
-- Name: pull_request_files prfiles_unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_files
    ADD CONSTRAINT prfiles_unique UNIQUE (pull_request_id, repo_id, pr_file_path);


--
-- Name: pull_requests pull-request-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_requests
    ADD CONSTRAINT "pull-request-insert-unique" UNIQUE (pr_url);


--
-- Name: pull_request_message_ref pull-request-message-ref-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_message_ref
    ADD CONSTRAINT "pull-request-message-ref-insert-unique" UNIQUE (pr_message_ref_src_comment_id, pull_request_id);


--
-- Name: pull_request_meta pull-request-meta-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_meta
    ADD CONSTRAINT "pull-request-meta-insert-unique" UNIQUE (pull_request_id, pr_head_or_base, pr_sha);


--
-- Name: pull_request_review_message_ref pull-request-review-message-ref-insert-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_review_message_ref
    ADD CONSTRAINT "pull-request-review-message-ref-insert-unique" UNIQUE (pr_review_msg_src_id);


--
-- Name: pull_request_analysis pull_request_analysis_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_analysis
    ADD CONSTRAINT pull_request_analysis_pkey PRIMARY KEY (pull_request_analysis_id);


--
-- Name: pull_request_assignees pull_request_assignees_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_assignees
    ADD CONSTRAINT pull_request_assignees_pkey PRIMARY KEY (pr_assignee_map_id);


--
-- Name: pull_request_commits pull_request_commits_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_commits
    ADD CONSTRAINT pull_request_commits_pkey PRIMARY KEY (pr_cmt_id);


--
-- Name: pull_request_files pull_request_files_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_files
    ADD CONSTRAINT pull_request_files_pkey PRIMARY KEY (pr_file_id);


--
-- Name: pull_request_labels pull_request_labels_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_labels
    ADD CONSTRAINT pull_request_labels_pkey PRIMARY KEY (pr_label_id);


--
-- Name: pull_request_message_ref pull_request_message_ref_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_message_ref
    ADD CONSTRAINT pull_request_message_ref_pkey PRIMARY KEY (pr_msg_ref_id);


--
-- Name: pull_request_meta pull_request_meta_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_meta
    ADD CONSTRAINT pull_request_meta_pkey PRIMARY KEY (pr_repo_meta_id);


--
-- Name: pull_request_repo pull_request_repo_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_repo
    ADD CONSTRAINT pull_request_repo_pkey PRIMARY KEY (pr_repo_id);


--
-- Name: pull_request_reviews pull_request_review_id; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviews
    ADD CONSTRAINT pull_request_review_id PRIMARY KEY (pr_review_id);


--
-- Name: pull_request_reviewers pull_request_reviewers_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviewers
    ADD CONSTRAINT pull_request_reviewers_pkey PRIMARY KEY (pr_reviewer_map_id);


--
-- Name: pull_request_teams pull_request_teams_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_teams
    ADD CONSTRAINT pull_request_teams_pkey PRIMARY KEY (pr_team_id);


--
-- Name: pull_requests pull_requests_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_requests
    ADD CONSTRAINT pull_requests_pkey PRIMARY KEY (pull_request_id);


--
-- Name: releases releases_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.releases
    ADD CONSTRAINT releases_pkey PRIMARY KEY (release_id);


--
-- Name: repo_badging repo_badging_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_badging
    ADD CONSTRAINT repo_badging_pkey PRIMARY KEY (badge_collection_id);


--
-- Name: repo_clones_data repo_clones_data_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_clones_data
    ADD CONSTRAINT repo_clones_data_pkey PRIMARY KEY (repo_clone_data_id);


--
-- Name: repo_cluster_messages repo_cluster_messages_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_cluster_messages
    ADD CONSTRAINT repo_cluster_messages_pkey PRIMARY KEY (msg_cluster_id);


--
-- Name: repo_dependencies repo_dependencies_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_dependencies
    ADD CONSTRAINT repo_dependencies_pkey PRIMARY KEY (repo_dependencies_id);


--
-- Name: repo_deps_libyear repo_deps_libyear_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_deps_libyear
    ADD CONSTRAINT repo_deps_libyear_pkey PRIMARY KEY (repo_deps_libyear_id);


--
-- Name: repo_deps_scorecard repo_deps_scorecard_pkey1; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_deps_scorecard
    ADD CONSTRAINT repo_deps_scorecard_pkey1 PRIMARY KEY (repo_deps_scorecard_id);


--
-- Name: repo repo_git-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo
    ADD CONSTRAINT "repo_git-unique" UNIQUE (repo_git);


--
-- Name: repo_group_insights repo_group_insights_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_group_insights
    ADD CONSTRAINT repo_group_insights_pkey PRIMARY KEY (rgi_id);


--
-- Name: repo_groups_list_serve repo_groups_list_serve_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_groups_list_serve
    ADD CONSTRAINT repo_groups_list_serve_pkey PRIMARY KEY (rgls_id);


--
-- Name: repo_info repo_info_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_info
    ADD CONSTRAINT repo_info_pkey PRIMARY KEY (repo_info_id);


--
-- Name: repo_insights repo_insights_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_insights
    ADD CONSTRAINT repo_insights_pkey PRIMARY KEY (ri_id);


--
-- Name: repo_insights_records repo_insights_records_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_insights_records
    ADD CONSTRAINT repo_insights_records_pkey PRIMARY KEY (ri_id);


--
-- Name: repo_labor repo_labor_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_labor
    ADD CONSTRAINT repo_labor_pkey PRIMARY KEY (repo_labor_id);


--
-- Name: repo_meta repo_meta_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_meta
    ADD CONSTRAINT repo_meta_pkey PRIMARY KEY (rmeta_id, repo_id);


--
-- Name: repo_sbom_scans repo_sbom_scans_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_sbom_scans
    ADD CONSTRAINT repo_sbom_scans_pkey PRIMARY KEY (rsb_id);


--
-- Name: repo_stats repo_stats_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_stats
    ADD CONSTRAINT repo_stats_pkey PRIMARY KEY (rstat_id, repo_id);


--
-- Name: repo_test_coverage repo_test_coverage_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_test_coverage
    ADD CONSTRAINT repo_test_coverage_pkey PRIMARY KEY (repo_id);


--
-- Name: repo_topic repo_topic_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_topic
    ADD CONSTRAINT repo_topic_pkey PRIMARY KEY (repo_topic_id);


--
-- Name: repo repounique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo
    ADD CONSTRAINT repounique PRIMARY KEY (repo_id);


--
-- Name: repo_groups rgid; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_groups
    ADD CONSTRAINT rgid PRIMARY KEY (repo_group_id);


--
-- Name: repo_groups_list_serve rglistserve; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_groups_list_serve
    ADD CONSTRAINT rglistserve UNIQUE (rgls_id, repo_group_id);


--
-- Name: repo_labor rl-unique; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_labor
    ADD CONSTRAINT "rl-unique" UNIQUE (repo_id, rl_analysis_date, file_path, file_name);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: platform theplat; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.platform
    ADD CONSTRAINT theplat PRIMARY KEY (pltfrm_id);


--
-- Name: topic_words topic_words_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.topic_words
    ADD CONSTRAINT topic_words_pkey PRIMARY KEY (topic_words_id);


--
-- Name: issues unique-issue; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issues
    ADD CONSTRAINT "unique-issue" UNIQUE (repo_id, gh_issue_id);


--
-- Name: pull_requests unique-pr; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_requests
    ADD CONSTRAINT "unique-pr" UNIQUE (repo_id, pr_src_id);


--
-- Name: pull_request_events unique-pr-event-id; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_events
    ADD CONSTRAINT "unique-pr-event-id" UNIQUE (platform_id, node_id);


--
-- Name: pull_request_labels unique-pr-src-label-id; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_labels
    ADD CONSTRAINT "unique-pr-src-label-id" UNIQUE (pr_src_id, pull_request_id);


--
-- Name: pull_requests unique-prx; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_requests
    ADD CONSTRAINT "unique-prx" UNIQUE (repo_id, pr_src_id);


--
-- Name: contributor_affiliations unique_domain; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributor_affiliations
    ADD CONSTRAINT unique_domain UNIQUE (ca_domain);


--
-- Name: CONSTRAINT unique_domain ON contributor_affiliations; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON CONSTRAINT unique_domain ON augur_data.contributor_affiliations IS 'Only one row should exist for any given top level domain or subdomain. ';


--
-- Name: issue_events unique_event_id_key; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_events
    ADD CONSTRAINT unique_event_id_key UNIQUE (issue_id, issue_event_src_id);


--
-- Name: CONSTRAINT unique_event_id_key ON issue_events; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON CONSTRAINT unique_event_id_key ON augur_data.issue_events IS 'Natural key for issue events. ';


--
-- Name: issue_labels unique_issue_label; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_labels
    ADD CONSTRAINT unique_issue_label UNIQUE (label_src_id, issue_id);


--
-- Name: pull_request_reviewers unique_pr_src_reviewer_key; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviewers
    ADD CONSTRAINT unique_pr_src_reviewer_key UNIQUE (pull_request_id, pr_reviewer_src_id);


--
-- Name: unresolved_commit_emails unresolved_commit_emails_email_key; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.unresolved_commit_emails
    ADD CONSTRAINT unresolved_commit_emails_email_key UNIQUE (email);


--
-- Name: unresolved_commit_emails unresolved_commit_emails_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.unresolved_commit_emails
    ADD CONSTRAINT unresolved_commit_emails_pkey PRIMARY KEY (email_unresolved_id);


--
-- Name: utility_log utility_log_pkey; Type: CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.utility_log
    ADD CONSTRAINT utility_log_pkey PRIMARY KEY (id);


--
-- Name: augur_settings augur_settings_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.augur_settings
    ADD CONSTRAINT augur_settings_pkey PRIMARY KEY (id);


--
-- Name: client_applications client_applications_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.client_applications
    ADD CONSTRAINT client_applications_pkey PRIMARY KEY (id);


--
-- Name: collection_status collection_status_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.collection_status
    ADD CONSTRAINT collection_status_pkey PRIMARY KEY (repo_id);


--
-- Name: config config_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.config
    ADD CONSTRAINT config_pkey PRIMARY KEY (id);


--
-- Name: worker_history history_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.worker_history
    ADD CONSTRAINT history_pkey PRIMARY KEY (history_id);


--
-- Name: worker_job job_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.worker_job
    ADD CONSTRAINT job_pkey PRIMARY KEY (job_model);


--
-- Name: refresh_tokens refresh_token_user_session_token_id_unique; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.refresh_tokens
    ADD CONSTRAINT refresh_token_user_session_token_id_unique UNIQUE (user_session_token);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: worker_settings_facade settings_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.worker_settings_facade
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: subscription_types subscription_type_title_unique; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.subscription_types
    ADD CONSTRAINT subscription_type_title_unique UNIQUE (name);


--
-- Name: subscription_types subscription_types_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.subscription_types
    ADD CONSTRAINT subscription_types_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (application_id, type_id);


--
-- Name: config unique-config-setting; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.config
    ADD CONSTRAINT "unique-config-setting" UNIQUE (section_name, setting_name);


--
-- Name: users user-unique-email; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.users
    ADD CONSTRAINT "user-unique-email" UNIQUE (email);


--
-- Name: users user-unique-name; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.users
    ADD CONSTRAINT "user-unique-name" UNIQUE (login_name);


--
-- Name: users user-unique-phone; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.users
    ADD CONSTRAINT "user-unique-phone" UNIQUE (text_phone);


--
-- Name: user_groups user_groups_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_groups
    ADD CONSTRAINT user_groups_pkey PRIMARY KEY (group_id);


--
-- Name: user_groups user_groups_user_id_name_key; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_groups
    ADD CONSTRAINT user_groups_user_id_name_key UNIQUE (user_id, name);


--
-- Name: user_repos user_repos_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_repos
    ADD CONSTRAINT user_repos_pkey PRIMARY KEY (group_id, repo_id);


--
-- Name: user_session_tokens user_session_tokens_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_session_tokens
    ADD CONSTRAINT user_session_tokens_pkey PRIMARY KEY (token);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: worker_oauth worker_oauth_pkey; Type: CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.worker_oauth
    ADD CONSTRAINT worker_oauth_pkey PRIMARY KEY (oauth_id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: augur
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: annotation_types annotation_types_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.annotation_types
    ADD CONSTRAINT annotation_types_pkey PRIMARY KEY (annotation_type_id);


--
-- Name: annotations annotations_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.annotations
    ADD CONSTRAINT annotations_pkey PRIMARY KEY (annotation_id);


--
-- Name: augur_repo_map augur_repo_map_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.augur_repo_map
    ADD CONSTRAINT augur_repo_map_pkey PRIMARY KEY (map_id);


--
-- Name: creator_types creator_types_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.creator_types
    ADD CONSTRAINT creator_types_pkey PRIMARY KEY (creator_type_id);


--
-- Name: creators creators_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.creators
    ADD CONSTRAINT creators_pkey PRIMARY KEY (creator_id);


--
-- Name: document_namespaces document_namespaces_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.document_namespaces
    ADD CONSTRAINT document_namespaces_pkey PRIMARY KEY (document_namespace_id);


--
-- Name: documents_creators documents_creators_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents_creators
    ADD CONSTRAINT documents_creators_pkey PRIMARY KEY (document_creator_id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (document_id);


--
-- Name: external_refs external_refs_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.external_refs
    ADD CONSTRAINT external_refs_pkey PRIMARY KEY (external_ref_id);


--
-- Name: file_contributors file_contributors_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.file_contributors
    ADD CONSTRAINT file_contributors_pkey PRIMARY KEY (file_contributor_id);


--
-- Name: files_licenses files_licenses_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_licenses
    ADD CONSTRAINT files_licenses_pkey PRIMARY KEY (file_license_id);


--
-- Name: files files_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (file_id);


--
-- Name: files_scans files_scans_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_scans
    ADD CONSTRAINT files_scans_pkey PRIMARY KEY (file_scan_id);


--
-- Name: identifiers identifiers_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT identifiers_pkey PRIMARY KEY (identifier_id);


--
-- Name: licenses licenses_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.licenses
    ADD CONSTRAINT licenses_pkey PRIMARY KEY (license_id);


--
-- Name: packages_files packages_files_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_files
    ADD CONSTRAINT packages_files_pkey PRIMARY KEY (package_file_id);


--
-- Name: packages packages_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT packages_pkey PRIMARY KEY (package_id);


--
-- Name: packages_scans packages_scans_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_scans
    ADD CONSTRAINT packages_scans_pkey PRIMARY KEY (package_scan_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (package_id);


--
-- Name: relationship_types relationship_types_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.relationship_types
    ADD CONSTRAINT relationship_types_pkey PRIMARY KEY (relationship_type_id);


--
-- Name: relationships relationships_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.relationships
    ADD CONSTRAINT relationships_pkey PRIMARY KEY (relationship_id);


--
-- Name: scanners scanners_pkey; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.scanners
    ADD CONSTRAINT scanners_pkey PRIMARY KEY (scanner_id);


--
-- Name: annotation_types uc_annotation_type_name; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.annotation_types
    ADD CONSTRAINT uc_annotation_type_name UNIQUE (name);


--
-- Name: packages uc_dir_code_ver_code; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT uc_dir_code_ver_code UNIQUE (verification_code, dosocs2_dir_code);


--
-- Name: documents uc_document_document_namespace_id; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents
    ADD CONSTRAINT uc_document_document_namespace_id UNIQUE (document_namespace_id);


--
-- Name: document_namespaces uc_document_namespace_uri; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.document_namespaces
    ADD CONSTRAINT uc_document_namespace_uri UNIQUE (uri);


--
-- Name: external_refs uc_external_ref_document_id_string; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.external_refs
    ADD CONSTRAINT uc_external_ref_document_id_string UNIQUE (document_id, id_string);


--
-- Name: files_licenses uc_file_license; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_licenses
    ADD CONSTRAINT uc_file_license UNIQUE (file_id, license_id);


--
-- Name: files_scans uc_file_scanner_id; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_scans
    ADD CONSTRAINT uc_file_scanner_id UNIQUE (file_id, scanner_id);


--
-- Name: files uc_file_sha256; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files
    ADD CONSTRAINT uc_file_sha256 UNIQUE (sha256);


--
-- Name: file_types uc_file_type_name; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.file_types
    ADD CONSTRAINT uc_file_type_name PRIMARY KEY (name);


--
-- Name: identifiers uc_identifier_document_namespace_id; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT uc_identifier_document_namespace_id UNIQUE (document_namespace_id, id_string);


--
-- Name: identifiers uc_identifier_namespace_document_id; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT uc_identifier_namespace_document_id UNIQUE (document_namespace_id, document_id);


--
-- Name: identifiers uc_identifier_namespace_package_file_id; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT uc_identifier_namespace_package_file_id UNIQUE (document_namespace_id, package_file_id);


--
-- Name: identifiers uc_identifier_namespace_package_id; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT uc_identifier_namespace_package_id UNIQUE (document_namespace_id, package_id);


--
-- Name: relationships uc_left_right_relationship_type; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.relationships
    ADD CONSTRAINT uc_left_right_relationship_type UNIQUE (left_identifier_id, right_identifier_id, relationship_type_id);


--
-- Name: licenses uc_license_short_name; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.licenses
    ADD CONSTRAINT uc_license_short_name UNIQUE (short_name);


--
-- Name: packages_files uc_package_id_file_name; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_files
    ADD CONSTRAINT uc_package_id_file_name UNIQUE (package_id, file_name);


--
-- Name: packages_scans uc_package_scanner_id; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_scans
    ADD CONSTRAINT uc_package_scanner_id UNIQUE (package_id, scanner_id);


--
-- Name: packages uc_package_sha256; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT uc_package_sha256 UNIQUE (sha256);


--
-- Name: relationship_types uc_relationship_type_name; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.relationship_types
    ADD CONSTRAINT uc_relationship_type_name UNIQUE (name);


--
-- Name: scanners uc_scanner_name; Type: CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.scanners
    ADD CONSTRAINT uc_scanner_name UNIQUE (name);


--
-- Name: REPO_DEP; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "REPO_DEP" ON augur_data.library_dependencies USING btree (library_id);


--
-- Name: api_get_all_repo_prs_repo_id_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX api_get_all_repo_prs_repo_id_idx ON augur_data.api_get_all_repo_prs USING btree (repo_id);


--
-- Name: api_get_all_repos_commits_repo_id_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX api_get_all_repos_commits_repo_id_idx ON augur_data.api_get_all_repos_commits USING btree (repo_id);


--
-- Name: api_get_all_repos_issues_repo_id_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX api_get_all_repos_issues_repo_id_idx ON augur_data.api_get_all_repos_issues USING btree (repo_id);


--
-- Name: augur_new_contributors_cntrb_id_created_at_repo_id_repo_nam_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX augur_new_contributors_cntrb_id_created_at_repo_id_repo_nam_idx ON augur_data.augur_new_contributors USING btree (cntrb_id, created_at, repo_id, repo_name, login, rank);


--
-- Name: author_affiliation; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX author_affiliation ON augur_data.commits USING btree (cmt_author_affiliation);


--
-- Name: author_cntrb_id; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX author_cntrb_id ON augur_data.commits USING btree (cmt_ght_author_id);


--
-- Name: author_email,author_affiliation,author_date; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "author_email,author_affiliation,author_date" ON augur_data.commits USING btree (cmt_author_email, cmt_author_affiliation, cmt_author_date);


--
-- Name: author_raw_email; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX author_raw_email ON augur_data.commits USING btree (cmt_author_raw_email);


--
-- Name: cnt-fullname; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "cnt-fullname" ON augur_data.contributors USING hash (cntrb_full_name);


--
-- Name: cntrb-theemail; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "cntrb-theemail" ON augur_data.contributors USING hash (cntrb_email);


--
-- Name: cntrb_canonica-idx11; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "cntrb_canonica-idx11" ON augur_data.contributors USING btree (cntrb_canonical);


--
-- Name: cntrb_login_platform_index; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX cntrb_login_platform_index ON augur_data.contributors USING btree (cntrb_login);


--
-- Name: comment_id; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX comment_id ON augur_data.commit_comment_ref USING btree (cmt_comment_src_id, cmt_comment_id, msg_id);


--
-- Name: commit_parents_ibfk_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX commit_parents_ibfk_1 ON augur_data.commit_parents USING btree (cmt_id);


--
-- Name: commit_parents_ibfk_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX commit_parents_ibfk_2 ON augur_data.commit_parents USING btree (parent_id);


--
-- Name: commited; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX commited ON augur_data.commits USING btree (cmt_id);


--
-- Name: commits_idx_cmt_email_cmt_date_cmt_name; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX commits_idx_cmt_email_cmt_date_cmt_name ON augur_data.commits USING btree (cmt_author_email, cmt_author_date, cmt_author_name);


--
-- Name: committer_affiliation; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX committer_affiliation ON augur_data.commits USING btree (cmt_committer_affiliation);


--
-- Name: committer_raw_email; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX committer_raw_email ON augur_data.commits USING btree (cmt_committer_raw_email);


--
-- Name: contributor_worker_email_finder; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX contributor_worker_email_finder ON augur_data.contributors USING brin (cntrb_email);


--
-- Name: contributor_worker_fullname_finder; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX contributor_worker_fullname_finder ON augur_data.contributors USING brin (cntrb_full_name);


--
-- Name: contributors_idx_cntrb_email3; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX contributors_idx_cntrb_email3 ON augur_data.contributors USING btree (cntrb_email);


--
-- Name: dater; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX dater ON augur_data.repo_insights_records USING btree (ri_date);


--
-- Name: explorer_commits_and_committers__repo_id_cmt_committer_date_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_commits_and_committers__repo_id_cmt_committer_date_idx ON augur_data.explorer_commits_and_committers_daily_count USING btree (repo_id, cmt_committer_date);


--
-- Name: explorer_contributor_actions_cntrb_id_created_at_repo_id_ac_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_contributor_actions_cntrb_id_created_at_repo_id_ac_idx ON augur_data.explorer_contributor_actions USING btree (cntrb_id, created_at, repo_id, action, repo_name, login, rank);


--
-- Name: explorer_entry_list_repo_id_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_entry_list_repo_id_idx ON augur_data.explorer_entry_list USING btree (repo_id);


--
-- Name: explorer_issue_assignments_issue_id_id_node_id_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_issue_assignments_issue_id_id_node_id_idx ON augur_data.explorer_issue_assignments USING btree (issue_id, id, node_id);


--
-- Name: explorer_new_contributors_cntrb_id_created_at_month_year_re_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_new_contributors_cntrb_id_created_at_month_year_re_idx ON augur_data.explorer_new_contributors USING btree (cntrb_id, created_at, month, year, repo_id, full_name, repo_name, login, rank);


--
-- Name: explorer_pr_assignments_pull_request_id_id_node_id_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_pr_assignments_pull_request_id_id_node_id_idx ON augur_data.explorer_pr_assignments USING btree (pull_request_id, id, node_id);


--
-- Name: explorer_pr_response_pull_request_id_id_cntrb_id_msg_cntrb__idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_pr_response_pull_request_id_id_cntrb_id_msg_cntrb__idx ON augur_data.explorer_pr_response USING btree (pull_request_id, id, cntrb_id, msg_cntrb_id, msg_timestamp);


--
-- Name: explorer_pr_response_times_repo_id_pr_src_id_pr_src_meta_la_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_pr_response_times_repo_id_pr_src_id_pr_src_meta_la_idx ON augur_data.explorer_pr_response_times USING btree (repo_id, pr_src_id, pr_src_meta_label);


--
-- Name: explorer_repo_languages_repo_id_programming_language_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_repo_languages_repo_id_programming_language_idx ON augur_data.explorer_repo_languages USING btree (repo_id, programming_language);


--
-- Name: explorer_user_repos_login_name_user_id_group_id_repo_id_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX explorer_user_repos_login_name_user_id_group_id_repo_id_idx ON augur_data.explorer_user_repos USING btree (login_name, user_id, group_id, repo_id);


--
-- Name: forked; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX forked ON augur_data.repo USING btree (forked_from);


--
-- Name: gh_login; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX gh_login ON augur_data.contributors USING btree (gh_login NULLS FIRST);


--
-- Name: id_node; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX id_node ON augur_data.pull_requests USING btree (pr_src_id DESC, pr_src_node_id DESC NULLS LAST);


--
-- Name: issue-cntrb-assign-idx-1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "issue-cntrb-assign-idx-1" ON augur_data.issue_assignees USING btree (cntrb_id);


--
-- Name: issue-cntrb-dix2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "issue-cntrb-dix2" ON augur_data.issues USING btree (cntrb_id);


--
-- Name: issue-cntrb-idx2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "issue-cntrb-idx2" ON augur_data.issue_events USING btree (issue_event_src_id);


--
-- Name: issue_events_ibfk_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX issue_events_ibfk_1 ON augur_data.issue_events USING btree (issue_id);


--
-- Name: issue_events_ibfk_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX issue_events_ibfk_2 ON augur_data.issue_events USING btree (cntrb_id);


--
-- Name: issues_ibfk_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX issues_ibfk_1 ON augur_data.issues USING btree (repo_id);


--
-- Name: issues_ibfk_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX issues_ibfk_2 ON augur_data.issues USING btree (reporter_id);


--
-- Name: issues_ibfk_4; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX issues_ibfk_4 ON augur_data.issues USING btree (pull_request_id);


--
-- Name: lister; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX lister ON augur_data.repo_groups_list_serve USING btree (rgls_id, repo_group_id);


--
-- Name: login; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX login ON augur_data.contributors USING btree (cntrb_login);


--
-- Name: login-contributor-idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "login-contributor-idx" ON augur_data.contributors USING btree (cntrb_login);


--
-- Name: messagegrouper; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX messagegrouper ON augur_data.message USING btree (msg_id, rgls_id);


--
-- Name: msg-cntrb-id-idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "msg-cntrb-id-idx" ON augur_data.message USING btree (cntrb_id);


--
-- Name: plat; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX plat ON augur_data.platform USING btree (pltfrm_id);


--
-- Name: platformgrouper; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX platformgrouper ON augur_data.message USING btree (msg_id, pltfrm_id);


--
-- Name: pr-cntrb-idx-repo; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "pr-cntrb-idx-repo" ON augur_data.pull_request_repo USING btree (pr_cntrb_id);


--
-- Name: pr-reviewers-cntrb-idx1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "pr-reviewers-cntrb-idx1" ON augur_data.pull_request_reviewers USING btree (cntrb_id);


--
-- Name: pr_ID_prs_table; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "pr_ID_prs_table" ON augur_data.pull_requests USING btree (pull_request_id);


--
-- Name: pr_anal_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX pr_anal_idx ON augur_data.pull_request_analysis USING btree (pull_request_id);


--
-- Name: pr_events_ibfk_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX pr_events_ibfk_1 ON augur_data.pull_request_events USING btree (pull_request_id);


--
-- Name: pr_events_ibfk_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX pr_events_ibfk_2 ON augur_data.pull_request_events USING btree (cntrb_id);


--
-- Name: pr_id_pr_files; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX pr_id_pr_files ON augur_data.pull_request_files USING btree (pull_request_id);


--
-- Name: pr_id_pr_reviews; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX pr_id_pr_reviews ON augur_data.pull_request_reviews USING btree (pull_request_id);


--
-- Name: pr_meta-cntrbid-idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "pr_meta-cntrbid-idx" ON augur_data.pull_request_meta USING btree (cntrb_id);


--
-- Name: pr_meta_cntrb-idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "pr_meta_cntrb-idx" ON augur_data.pull_request_assignees USING btree (contrib_id);


--
-- Name: probability_idx; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX probability_idx ON augur_data.pull_request_analysis USING btree (merge_probability DESC NULLS LAST);


--
-- Name: projects_id,affiliation; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,affiliation" ON augur_data.dm_repo_group_weekly USING btree (repo_group_id, affiliation);


--
-- Name: projects_id,affiliation_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,affiliation_copy_1" ON augur_data.dm_repo_group_annual USING btree (repo_group_id, affiliation);


--
-- Name: projects_id,affiliation_copy_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,affiliation_copy_2" ON augur_data.dm_repo_group_monthly USING btree (repo_group_id, affiliation);


--
-- Name: projects_id,email; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,email" ON augur_data.dm_repo_group_weekly USING btree (repo_group_id, email);


--
-- Name: projects_id,email_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,email_copy_1" ON augur_data.dm_repo_group_annual USING btree (repo_group_id, email);


--
-- Name: projects_id,email_copy_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,email_copy_2" ON augur_data.dm_repo_group_monthly USING btree (repo_group_id, email);


--
-- Name: projects_id,year,affiliation; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,year,affiliation" ON augur_data.dm_repo_group_weekly USING btree (repo_group_id, year, affiliation);


--
-- Name: projects_id,year,affiliation_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,year,affiliation_copy_1" ON augur_data.dm_repo_group_monthly USING btree (repo_group_id, year, affiliation);


--
-- Name: projects_id,year,email; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,year,email" ON augur_data.dm_repo_group_weekly USING btree (repo_group_id, year, email);


--
-- Name: projects_id,year,email_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "projects_id,year,email_copy_1" ON augur_data.dm_repo_group_monthly USING btree (repo_group_id, year, email);


--
-- Name: pull_requests_idx_repo_id_data_datex; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX pull_requests_idx_repo_id_data_datex ON augur_data.pull_requests USING btree (repo_id, data_collection_date);


--
-- Name: repo_id,affiliation; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,affiliation" ON augur_data.dm_repo_weekly USING btree (repo_id, affiliation);


--
-- Name: repo_id,affiliation_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,affiliation_copy_1" ON augur_data.dm_repo_annual USING btree (repo_id, affiliation);


--
-- Name: repo_id,affiliation_copy_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,affiliation_copy_2" ON augur_data.dm_repo_monthly USING btree (repo_id, affiliation);


--
-- Name: repo_id,commit; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,commit" ON augur_data.commits USING btree (repo_id, cmt_commit_hash);


--
-- Name: repo_id,email; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,email" ON augur_data.dm_repo_weekly USING btree (repo_id, email);


--
-- Name: repo_id,email_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,email_copy_1" ON augur_data.dm_repo_annual USING btree (repo_id, email);


--
-- Name: repo_id,email_copy_2; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,email_copy_2" ON augur_data.dm_repo_monthly USING btree (repo_id, email);


--
-- Name: repo_id,year,affiliation; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,year,affiliation" ON augur_data.dm_repo_weekly USING btree (repo_id, year, affiliation);


--
-- Name: repo_id,year,affiliation_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,year,affiliation_copy_1" ON augur_data.dm_repo_monthly USING btree (repo_id, year, affiliation);


--
-- Name: repo_id,year,email; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,year,email" ON augur_data.dm_repo_weekly USING btree (repo_id, year, email);


--
-- Name: repo_id,year,email_copy_1; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repo_id,year,email_copy_1" ON augur_data.dm_repo_monthly USING btree (repo_id, year, email);


--
-- Name: repo_idx_repo_id_repo_namex; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX repo_idx_repo_id_repo_namex ON augur_data.repo USING btree (repo_id, repo_name);


--
-- Name: repo_info_idx_repo_id_data_date_1x; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX repo_info_idx_repo_id_data_date_1x ON augur_data.repo_info USING btree (repo_id, data_collection_date);


--
-- Name: repo_info_idx_repo_id_data_datex; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX repo_info_idx_repo_id_data_datex ON augur_data.repo_info USING btree (repo_id, data_collection_date);


--
-- Name: repogitindexrep; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX repogitindexrep ON augur_data.repo USING btree (repo_git);


--
-- Name: reponameindex; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX reponameindex ON augur_data.repo USING hash (repo_name);


--
-- Name: reponameindexbtree; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX reponameindexbtree ON augur_data.repo USING btree (repo_name);


--
-- Name: repos_id; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX repos_id ON augur_data.analysis_log USING btree (repos_id);


--
-- Name: repos_id,status; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repos_id,status" ON augur_data.repos_fetch_log USING btree (repos_id, status);


--
-- Name: repos_id,statusops; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "repos_id,statusops" ON augur_data.repos_fetch_log USING btree (repos_id, status);


--
-- Name: rggrouponrepoindex; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX rggrouponrepoindex ON augur_data.repo USING btree (repo_group_id);


--
-- Name: rgidm; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX rgidm ON augur_data.repo_groups USING btree (repo_group_id);


--
-- Name: rgnameindex; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX rgnameindex ON augur_data.repo_groups USING btree (rg_name);


--
-- Name: therepo; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE UNIQUE INDEX therepo ON augur_data.repo USING btree (repo_id);


--
-- Name: type,projects_id; Type: INDEX; Schema: augur_data; Owner: augur
--

CREATE INDEX "type,projects_id" ON augur_data.unknown_cache USING btree (type, repo_group_id);


--
-- Name: repos_id,statusops; Type: INDEX; Schema: augur_operations; Owner: augur
--

CREATE INDEX "repos_id,statusops" ON augur_operations.repos_fetch_log USING btree (repos_id, status);


--
-- Name: commits cmt_ght_author_cntrb_id_fk; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commits
    ADD CONSTRAINT cmt_ght_author_cntrb_id_fk FOREIGN KEY (cmt_ght_author_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: contributor_repo contributor_repo_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributor_repo
    ADD CONSTRAINT contributor_repo_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: contributors_aliases contributors_aliases_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.contributors_aliases
    ADD CONSTRAINT contributors_aliases_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_reviews fk-review-platform; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviews
    ADD CONSTRAINT "fk-review-platform" FOREIGN KEY (platform_id) REFERENCES augur_data.platform(pltfrm_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: commit_comment_ref fk_commit_comment_ref_commits_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commit_comment_ref
    ADD CONSTRAINT fk_commit_comment_ref_commits_1 FOREIGN KEY (cmt_id) REFERENCES augur_data.commits(cmt_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: commit_comment_ref fk_commit_comment_ref_message_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commit_comment_ref
    ADD CONSTRAINT fk_commit_comment_ref_message_1 FOREIGN KEY (msg_id) REFERENCES augur_data.message(msg_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: commit_parents fk_commit_parents_commits_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commit_parents
    ADD CONSTRAINT fk_commit_parents_commits_1 FOREIGN KEY (cmt_id) REFERENCES augur_data.commits(cmt_id);


--
-- Name: commit_parents fk_commit_parents_commits_2; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commit_parents
    ADD CONSTRAINT fk_commit_parents_commits_2 FOREIGN KEY (parent_id) REFERENCES augur_data.commits(cmt_id);


--
-- Name: commits fk_commits_repo_2; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.commits
    ADD CONSTRAINT fk_commits_repo_2 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: discourse_insights fk_discourse_insights_message_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.discourse_insights
    ADD CONSTRAINT fk_discourse_insights_message_1 FOREIGN KEY (msg_id) REFERENCES augur_data.message(msg_id);


--
-- Name: issue_assignees fk_issue_assignee_repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_assignees
    ADD CONSTRAINT fk_issue_assignee_repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: issue_assignees fk_issue_assignees_issues_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_assignees
    ADD CONSTRAINT fk_issue_assignees_issues_1 FOREIGN KEY (issue_id) REFERENCES augur_data.issues(issue_id);


--
-- Name: issue_events fk_issue_event_platform_ide; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_events
    ADD CONSTRAINT fk_issue_event_platform_ide FOREIGN KEY (platform_id) REFERENCES augur_data.platform(pltfrm_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: issue_events fk_issue_events_issues_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_events
    ADD CONSTRAINT fk_issue_events_issues_1 FOREIGN KEY (issue_id) REFERENCES augur_data.issues(issue_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: issue_events fk_issue_events_repo; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_events
    ADD CONSTRAINT fk_issue_events_repo FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: issue_labels fk_issue_labels_issues_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_labels
    ADD CONSTRAINT fk_issue_labels_issues_1 FOREIGN KEY (issue_id) REFERENCES augur_data.issues(issue_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: issue_labels fk_issue_labels_repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_labels
    ADD CONSTRAINT fk_issue_labels_repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: issue_message_ref fk_issue_message_ref_issues_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_message_ref
    ADD CONSTRAINT fk_issue_message_ref_issues_1 FOREIGN KEY (issue_id) REFERENCES augur_data.issues(issue_id) ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;


--
-- Name: issue_message_ref fk_issue_message_ref_message_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_message_ref
    ADD CONSTRAINT fk_issue_message_ref_message_1 FOREIGN KEY (msg_id) REFERENCES augur_data.message(msg_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: issues fk_issues_repo; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issues
    ADD CONSTRAINT fk_issues_repo FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: libraries fk_libraries_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.libraries
    ADD CONSTRAINT fk_libraries_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: library_dependencies fk_library_dependencies_libraries_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.library_dependencies
    ADD CONSTRAINT fk_library_dependencies_libraries_1 FOREIGN KEY (library_id) REFERENCES augur_data.libraries(library_id);


--
-- Name: library_version fk_library_version_libraries_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.library_version
    ADD CONSTRAINT fk_library_version_libraries_1 FOREIGN KEY (library_id) REFERENCES augur_data.libraries(library_id);


--
-- Name: lstm_anomaly_results fk_lstm_anomaly_results_lstm_anomaly_models_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.lstm_anomaly_results
    ADD CONSTRAINT fk_lstm_anomaly_results_lstm_anomaly_models_1 FOREIGN KEY (model_id) REFERENCES augur_data.lstm_anomaly_models(model_id);


--
-- Name: lstm_anomaly_results fk_lstm_anomaly_results_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.lstm_anomaly_results
    ADD CONSTRAINT fk_lstm_anomaly_results_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: message_analysis fk_message_analysis_message_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_analysis
    ADD CONSTRAINT fk_message_analysis_message_1 FOREIGN KEY (msg_id) REFERENCES augur_data.message(msg_id);


--
-- Name: message_analysis_summary fk_message_analysis_summary_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_analysis_summary
    ADD CONSTRAINT fk_message_analysis_summary_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: message fk_message_platform_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message
    ADD CONSTRAINT fk_message_platform_1 FOREIGN KEY (pltfrm_id) REFERENCES augur_data.platform(pltfrm_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: message fk_message_repo_groups_list_serve_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message
    ADD CONSTRAINT fk_message_repo_groups_list_serve_1 FOREIGN KEY (rgls_id) REFERENCES augur_data.repo_groups_list_serve(rgls_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: message fk_message_repoid; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message
    ADD CONSTRAINT fk_message_repoid FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;


--
-- Name: message_sentiment fk_message_sentiment_message_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_sentiment
    ADD CONSTRAINT fk_message_sentiment_message_1 FOREIGN KEY (msg_id) REFERENCES augur_data.message(msg_id);


--
-- Name: message_sentiment_summary fk_message_sentiment_summary_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message_sentiment_summary
    ADD CONSTRAINT fk_message_sentiment_summary_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: pull_request_message_ref fk_pr_repo; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_message_ref
    ADD CONSTRAINT fk_pr_repo FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: pull_request_analysis fk_pull_request_analysis_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_analysis
    ADD CONSTRAINT fk_pull_request_analysis_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_assignees fk_pull_request_assignees_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_assignees
    ADD CONSTRAINT fk_pull_request_assignees_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_assignees fk_pull_request_assignees_repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_assignees
    ADD CONSTRAINT fk_pull_request_assignees_repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_commits fk_pull_request_commits_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_commits
    ADD CONSTRAINT fk_pull_request_commits_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_files fk_pull_request_commits_pull_requests_1_copy_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_files
    ADD CONSTRAINT fk_pull_request_commits_pull_requests_1_copy_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_commits fk_pull_request_commits_repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_commits
    ADD CONSTRAINT fk_pull_request_commits_repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: pull_request_events fk_pull_request_events_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_events
    ADD CONSTRAINT fk_pull_request_events_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_files fk_pull_request_files_repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_files
    ADD CONSTRAINT fk_pull_request_files_repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_labels fk_pull_request_labels_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_labels
    ADD CONSTRAINT fk_pull_request_labels_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_labels fk_pull_request_labels_repo; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_labels
    ADD CONSTRAINT fk_pull_request_labels_repo FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: pull_request_message_ref fk_pull_request_message_ref_message_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_message_ref
    ADD CONSTRAINT fk_pull_request_message_ref_message_1 FOREIGN KEY (msg_id) REFERENCES augur_data.message(msg_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_message_ref fk_pull_request_message_ref_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_message_ref
    ADD CONSTRAINT fk_pull_request_message_ref_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_meta fk_pull_request_meta_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_meta
    ADD CONSTRAINT fk_pull_request_meta_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_meta fk_pull_request_repo_meta_repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_meta
    ADD CONSTRAINT fk_pull_request_repo_meta_repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_repo fk_pull_request_repo_pull_request_meta_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_repo
    ADD CONSTRAINT fk_pull_request_repo_pull_request_meta_1 FOREIGN KEY (pr_repo_meta_id) REFERENCES augur_data.pull_request_meta(pr_repo_meta_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_review_message_ref fk_pull_request_review_message_ref_message_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_review_message_ref
    ADD CONSTRAINT fk_pull_request_review_message_ref_message_1 FOREIGN KEY (msg_id) REFERENCES augur_data.message(msg_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_review_message_ref fk_pull_request_review_message_ref_pull_request_reviews_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_review_message_ref
    ADD CONSTRAINT fk_pull_request_review_message_ref_pull_request_reviews_1 FOREIGN KEY (pr_review_id) REFERENCES augur_data.pull_request_reviews(pr_review_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_reviewers fk_pull_request_reviewers_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviewers
    ADD CONSTRAINT fk_pull_request_reviewers_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_reviews fk_pull_request_reviews_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviews
    ADD CONSTRAINT fk_pull_request_reviews_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_teams fk_pull_request_teams_pull_requests_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_teams
    ADD CONSTRAINT fk_pull_request_teams_pull_requests_1 FOREIGN KEY (pull_request_id) REFERENCES augur_data.pull_requests(pull_request_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_requests fk_pull_requests_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_requests
    ADD CONSTRAINT fk_pull_requests_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: releases fk_releases_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.releases
    ADD CONSTRAINT fk_releases_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_badging fk_repo_badging_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_badging
    ADD CONSTRAINT fk_repo_badging_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_cluster_messages fk_repo_cluster_messages_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_cluster_messages
    ADD CONSTRAINT fk_repo_cluster_messages_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_group_insights fk_repo_group_insights_repo_groups_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_group_insights
    ADD CONSTRAINT fk_repo_group_insights_repo_groups_1 FOREIGN KEY (repo_group_id) REFERENCES augur_data.repo_groups(repo_group_id);


--
-- Name: repo_groups_list_serve fk_repo_groups_list_serve_repo_groups_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_groups_list_serve
    ADD CONSTRAINT fk_repo_groups_list_serve_repo_groups_1 FOREIGN KEY (repo_group_id) REFERENCES augur_data.repo_groups(repo_group_id);


--
-- Name: issue_message_ref fk_repo_id_fk1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_message_ref
    ADD CONSTRAINT fk_repo_id_fk1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: repo_info fk_repo_info_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_info
    ADD CONSTRAINT fk_repo_info_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_insights fk_repo_insights_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_insights
    ADD CONSTRAINT fk_repo_insights_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_labor fk_repo_labor_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_labor
    ADD CONSTRAINT fk_repo_labor_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_meta fk_repo_meta_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_meta
    ADD CONSTRAINT fk_repo_meta_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo fk_repo_repo_groups_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo
    ADD CONSTRAINT fk_repo_repo_groups_1 FOREIGN KEY (repo_group_id) REFERENCES augur_data.repo_groups(repo_group_id);


--
-- Name: CONSTRAINT fk_repo_repo_groups_1 ON repo; Type: COMMENT; Schema: augur_data; Owner: augur
--

COMMENT ON CONSTRAINT fk_repo_repo_groups_1 ON augur_data.repo IS 'Repo_groups cardinality set to one and only one because, although in theory there could be more than one repo group for a repo, this might create dependencies in hosted situation that we do not want to live with. ';


--
-- Name: pull_request_reviews fk_repo_review; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviews
    ADD CONSTRAINT fk_repo_review FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: repo_stats fk_repo_stats_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_stats
    ADD CONSTRAINT fk_repo_stats_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_test_coverage fk_repo_test_coverage_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_test_coverage
    ADD CONSTRAINT fk_repo_test_coverage_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_topic fk_repo_topic_repo_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_topic
    ADD CONSTRAINT fk_repo_topic_repo_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: pull_request_review_message_ref fk_review_repo; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_review_message_ref
    ADD CONSTRAINT fk_review_repo FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_events fkpr_platform; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_events
    ADD CONSTRAINT fkpr_platform FOREIGN KEY (platform_id) REFERENCES augur_data.platform(pltfrm_id) ON UPDATE RESTRICT ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: pull_request_events fkprevent_repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_events
    ADD CONSTRAINT fkprevent_repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE RESTRICT ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: issue_assignees issue_assignees_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_assignees
    ADD CONSTRAINT issue_assignees_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id);


--
-- Name: issue_events issue_events_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issue_events
    ADD CONSTRAINT issue_events_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: issues issues_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issues
    ADD CONSTRAINT issues_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id);


--
-- Name: issues issues_reporter_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.issues
    ADD CONSTRAINT issues_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES augur_data.contributors(cntrb_id);


--
-- Name: message message_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.message
    ADD CONSTRAINT message_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_assignees pull_request_assignees_contrib_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_assignees
    ADD CONSTRAINT pull_request_assignees_contrib_id_fkey FOREIGN KEY (contrib_id) REFERENCES augur_data.contributors(cntrb_id);


--
-- Name: pull_request_commits pull_request_commits_pr_cmt_author_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_commits
    ADD CONSTRAINT pull_request_commits_pr_cmt_author_cntrb_id_fkey FOREIGN KEY (pr_cmt_author_cntrb_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_events pull_request_events_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_events
    ADD CONSTRAINT pull_request_events_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id);


--
-- Name: pull_request_meta pull_request_meta_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_meta
    ADD CONSTRAINT pull_request_meta_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id);


--
-- Name: pull_request_repo pull_request_repo_pr_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_repo
    ADD CONSTRAINT pull_request_repo_pr_cntrb_id_fkey FOREIGN KEY (pr_cntrb_id) REFERENCES augur_data.contributors(cntrb_id);


--
-- Name: pull_request_reviewers pull_request_reviewers_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviewers
    ADD CONSTRAINT pull_request_reviewers_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pull_request_reviews pull_request_reviews_cntrb_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_request_reviews
    ADD CONSTRAINT pull_request_reviews_cntrb_id_fkey FOREIGN KEY (cntrb_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: pull_requests pull_requests_pr_augur_contributor_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.pull_requests
    ADD CONSTRAINT pull_requests_pr_augur_contributor_id_fkey FOREIGN KEY (pr_augur_contributor_id) REFERENCES augur_data.contributors(cntrb_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: repo_clones_data repo_clones_data_repo_id_fkey; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_clones_data
    ADD CONSTRAINT repo_clones_data_repo_id_fkey FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;


--
-- Name: repo_dependencies repo_id; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_dependencies
    ADD CONSTRAINT repo_id FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_deps_scorecard repo_id_copy_1; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_deps_scorecard
    ADD CONSTRAINT repo_id_copy_1 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_deps_libyear repo_id_copy_2; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_deps_libyear
    ADD CONSTRAINT repo_id_copy_2 FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: repo_insights_records repo_id_ref; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_insights_records
    ADD CONSTRAINT repo_id_ref FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: repo_sbom_scans repo_linker_sbom; Type: FK CONSTRAINT; Schema: augur_data; Owner: augur
--

ALTER TABLE ONLY augur_data.repo_sbom_scans
    ADD CONSTRAINT repo_linker_sbom FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: client_applications client_application_user_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.client_applications
    ADD CONSTRAINT client_application_user_id_fkey FOREIGN KEY (user_id) REFERENCES augur_operations.users(user_id);


--
-- Name: collection_status collection_status_repo_id_fk; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.collection_status
    ADD CONSTRAINT collection_status_repo_id_fk FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: refresh_tokens refresh_token_session_token_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.refresh_tokens
    ADD CONSTRAINT refresh_token_session_token_id_fkey FOREIGN KEY (user_session_token) REFERENCES augur_operations.user_session_tokens(token);


--
-- Name: subscriptions subscriptions_application_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.subscriptions
    ADD CONSTRAINT subscriptions_application_id_fkey FOREIGN KEY (application_id) REFERENCES augur_operations.client_applications(id);


--
-- Name: subscriptions subscriptions_type_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.subscriptions
    ADD CONSTRAINT subscriptions_type_id_fkey FOREIGN KEY (type_id) REFERENCES augur_operations.subscription_types(id);


--
-- Name: user_groups user_groups_user_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_groups
    ADD CONSTRAINT user_groups_user_id_fkey FOREIGN KEY (user_id) REFERENCES augur_operations.users(user_id);


--
-- Name: user_repos user_repos_group_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_repos
    ADD CONSTRAINT user_repos_group_id_fkey FOREIGN KEY (group_id) REFERENCES augur_operations.user_groups(group_id);


--
-- Name: user_repos user_repos_repo_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_repos
    ADD CONSTRAINT user_repos_repo_id_fkey FOREIGN KEY (repo_id) REFERENCES augur_data.repo(repo_id);


--
-- Name: user_session_tokens user_session_token_application_id_fkey; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_session_tokens
    ADD CONSTRAINT user_session_token_application_id_fkey FOREIGN KEY (application_id) REFERENCES augur_operations.client_applications(id);


--
-- Name: user_session_tokens user_session_token_user_fk; Type: FK CONSTRAINT; Schema: augur_operations; Owner: augur
--

ALTER TABLE ONLY augur_operations.user_session_tokens
    ADD CONSTRAINT user_session_token_user_fk FOREIGN KEY (user_id) REFERENCES augur_operations.users(user_id);


--
-- Name: annotations annotations_annotation_type_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.annotations
    ADD CONSTRAINT annotations_annotation_type_id_fkey FOREIGN KEY (annotation_type_id) REFERENCES spdx.annotation_types(annotation_type_id);


--
-- Name: annotations annotations_creator_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.annotations
    ADD CONSTRAINT annotations_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES spdx.creators(creator_id);


--
-- Name: annotations annotations_document_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.annotations
    ADD CONSTRAINT annotations_document_id_fkey FOREIGN KEY (document_id) REFERENCES spdx.documents(document_id);


--
-- Name: annotations annotations_identifier_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.annotations
    ADD CONSTRAINT annotations_identifier_id_fkey FOREIGN KEY (identifier_id) REFERENCES spdx.identifiers(identifier_id);


--
-- Name: creators creators_creator_type_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.creators
    ADD CONSTRAINT creators_creator_type_id_fkey FOREIGN KEY (creator_type_id) REFERENCES spdx.creator_types(creator_type_id);


--
-- Name: documents_creators documents_creators_creator_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents_creators
    ADD CONSTRAINT documents_creators_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES spdx.creators(creator_id);


--
-- Name: documents_creators documents_creators_document_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents_creators
    ADD CONSTRAINT documents_creators_document_id_fkey FOREIGN KEY (document_id) REFERENCES spdx.documents(document_id);


--
-- Name: documents documents_data_license_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents
    ADD CONSTRAINT documents_data_license_id_fkey FOREIGN KEY (data_license_id) REFERENCES spdx.licenses(license_id);


--
-- Name: documents documents_document_namespace_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents
    ADD CONSTRAINT documents_document_namespace_id_fkey FOREIGN KEY (document_namespace_id) REFERENCES spdx.document_namespaces(document_namespace_id);


--
-- Name: documents documents_package_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.documents
    ADD CONSTRAINT documents_package_id_fkey FOREIGN KEY (package_id) REFERENCES spdx.packages(package_id);


--
-- Name: external_refs external_refs_document_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.external_refs
    ADD CONSTRAINT external_refs_document_id_fkey FOREIGN KEY (document_id) REFERENCES spdx.documents(document_id);


--
-- Name: external_refs external_refs_document_namespace_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.external_refs
    ADD CONSTRAINT external_refs_document_namespace_id_fkey FOREIGN KEY (document_namespace_id) REFERENCES spdx.document_namespaces(document_namespace_id);


--
-- Name: file_contributors file_contributors_file_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.file_contributors
    ADD CONSTRAINT file_contributors_file_id_fkey FOREIGN KEY (file_id) REFERENCES spdx.files(file_id);


--
-- Name: files_licenses files_licenses_file_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_licenses
    ADD CONSTRAINT files_licenses_file_id_fkey FOREIGN KEY (file_id) REFERENCES spdx.files(file_id);


--
-- Name: files_licenses files_licenses_license_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_licenses
    ADD CONSTRAINT files_licenses_license_id_fkey FOREIGN KEY (license_id) REFERENCES spdx.licenses(license_id);


--
-- Name: files_scans files_scans_file_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_scans
    ADD CONSTRAINT files_scans_file_id_fkey FOREIGN KEY (file_id) REFERENCES spdx.files(file_id);


--
-- Name: files_scans files_scans_scanner_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.files_scans
    ADD CONSTRAINT files_scans_scanner_id_fkey FOREIGN KEY (scanner_id) REFERENCES spdx.scanners(scanner_id);


--
-- Name: packages_files fk_package_files_packages; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_files
    ADD CONSTRAINT fk_package_files_packages FOREIGN KEY (package_id) REFERENCES spdx.packages(package_id);


--
-- Name: packages fk_package_packages_files; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT fk_package_packages_files FOREIGN KEY (ver_code_excluded_file_id) REFERENCES spdx.packages_files(package_file_id);


--
-- Name: identifiers identifiers_document_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT identifiers_document_id_fkey FOREIGN KEY (document_id) REFERENCES spdx.documents(document_id);


--
-- Name: identifiers identifiers_document_namespace_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT identifiers_document_namespace_id_fkey FOREIGN KEY (document_namespace_id) REFERENCES spdx.document_namespaces(document_namespace_id);


--
-- Name: identifiers identifiers_package_file_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT identifiers_package_file_id_fkey FOREIGN KEY (package_file_id) REFERENCES spdx.packages_files(package_file_id);


--
-- Name: identifiers identifiers_package_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.identifiers
    ADD CONSTRAINT identifiers_package_id_fkey FOREIGN KEY (package_id) REFERENCES spdx.packages(package_id);


--
-- Name: packages packages_concluded_license_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT packages_concluded_license_id_fkey FOREIGN KEY (concluded_license_id) REFERENCES spdx.licenses(license_id);


--
-- Name: packages packages_declared_license_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT packages_declared_license_id_fkey FOREIGN KEY (declared_license_id) REFERENCES spdx.licenses(license_id);


--
-- Name: packages_files packages_files_concluded_license_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_files
    ADD CONSTRAINT packages_files_concluded_license_id_fkey FOREIGN KEY (concluded_license_id) REFERENCES spdx.licenses(license_id);


--
-- Name: packages_files packages_files_file_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_files
    ADD CONSTRAINT packages_files_file_id_fkey FOREIGN KEY (file_id) REFERENCES spdx.files(file_id);


--
-- Name: packages packages_originator_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT packages_originator_id_fkey FOREIGN KEY (originator_id) REFERENCES spdx.creators(creator_id);


--
-- Name: packages_scans packages_scans_package_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_scans
    ADD CONSTRAINT packages_scans_package_id_fkey FOREIGN KEY (package_id) REFERENCES spdx.packages(package_id);


--
-- Name: packages_scans packages_scans_scanner_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages_scans
    ADD CONSTRAINT packages_scans_scanner_id_fkey FOREIGN KEY (scanner_id) REFERENCES spdx.scanners(scanner_id);


--
-- Name: packages packages_supplier_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.packages
    ADD CONSTRAINT packages_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES spdx.creators(creator_id);


--
-- Name: relationships relationships_left_identifier_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.relationships
    ADD CONSTRAINT relationships_left_identifier_id_fkey FOREIGN KEY (left_identifier_id) REFERENCES spdx.identifiers(identifier_id);


--
-- Name: relationships relationships_relationship_type_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.relationships
    ADD CONSTRAINT relationships_relationship_type_id_fkey FOREIGN KEY (relationship_type_id) REFERENCES spdx.relationship_types(relationship_type_id);


--
-- Name: relationships relationships_right_identifier_id_fkey; Type: FK CONSTRAINT; Schema: spdx; Owner: augur
--

ALTER TABLE ONLY spdx.relationships
    ADD CONSTRAINT relationships_right_identifier_id_fkey FOREIGN KEY (right_identifier_id) REFERENCES spdx.identifiers(identifier_id);


--
-- Name: api_get_all_repo_prs; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.api_get_all_repo_prs;


--
-- Name: api_get_all_repos_commits; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.api_get_all_repos_commits;


--
-- Name: api_get_all_repos_issues; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.api_get_all_repos_issues;


--
-- Name: augur_new_contributors; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.augur_new_contributors;


--
-- Name: explorer_commits_and_committers_daily_count; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_commits_and_committers_daily_count;


--
-- Name: explorer_contributor_actions; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_contributor_actions;


--
-- Name: explorer_entry_list; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_entry_list;


--
-- Name: explorer_issue_assignments; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_issue_assignments;


--
-- Name: explorer_new_contributors; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_new_contributors;


--
-- Name: explorer_pr_assignments; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_pr_assignments;


--
-- Name: explorer_pr_response; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_pr_response;


--
-- Name: explorer_pr_response_times; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_pr_response_times;


--
-- Name: explorer_repo_languages; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_repo_languages;


--
-- Name: explorer_user_repos; Type: MATERIALIZED VIEW DATA; Schema: augur_data; Owner: augur
--

REFRESH MATERIALIZED VIEW augur_data.explorer_user_repos;


--
-- PostgreSQL database dump complete
--

