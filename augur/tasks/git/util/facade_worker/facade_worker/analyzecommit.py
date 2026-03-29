#!/usr/bin/env python3

# Copyright 2016-2018 Brian Warner
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier:	Apache-2.0

# Git repo maintenance
#
# This script is responsible for cloning new repos and keeping existing repos up
# to date. It can be run as often as you want (and will detect when it's
# already running, so as not to spawn parallel processes), but once or twice per
# day should be more than sufficient. Each time it runs, it updates the repo
# and checks for any parents of HEAD that aren't already accounted for in the
# repos. It also rebuilds analysis data, checks any changed affiliations and
# aliases, and caches data for display.
"""
This script analyzes Git commits and extracts commit metadata and file-level
statistics such as additions, deletions, and whitespace changes. The resulting
records are used to populate a database for further analysis.

Functions:
- analyze_commit: Main routine for analyzing a single commit.
- check_swapped_emails: Fixes name/email reversal in commit metadata.
- strip_extra_amp: Removes malformed multiple '@' in emails.
- discover_alias: Resolves contributor alias emails.
- generate_commit_record: Constructs a normalized commit record.
"""

import datetime
import subprocess
from subprocess import check_output, CalledProcessError
import os
import sqlalchemy as s
from typing import Optional, List, Tuple, Dict, Any

from augur.application.db.lib import execute_sql, fetchall_data_from_sql_text
from augur.tasks.init import get_rabbitmq_conn_string

def check_swapped_emails(name: str, email: str) -> Tuple[str, str]:
    if name.find('@') >= 0 and email.find('@') == -1:
        return email, name
    return name, email

def strip_extra_amp(email: str) -> str:
    if email.count('@') > 1:
        return email[:email.find('@', email.find('@') + 1)]
    return email

def discover_alias(email: str) -> str:
    try:
        fetch_canonical = s.sql.text("""
            SELECT canonical_email
            FROM contributors_aliases
            WHERE alias_email = :alias_email AND cntrb_active = 1
        """).bindparams(alias_email=email)
        canonical = fetchall_data_from_sql_text(fetch_canonical)
        return canonical[0]['canonical_email'] if canonical else email
    except Exception:
        return email

def safe_strip(value: Optional[str]) -> str:
    return value.strip() if isinstance(value, str) else ""

def generate_commit_record(
    repos_id: int,
    commit: str,
    filename: str,
    author_name: Optional[str],
    author_email: Optional[str],
    author_date: Optional[str],
    author_timestamp: Optional[str],
    committer_name: Optional[str],
    committer_email: Optional[str],
    committer_date: Optional[str],
    committer_timestamp: Optional[str],
    added: int,
    removed: int,
    whitespace: int
) -> Dict[str, Any]:
    if repos_id is None:
        raise ValueError("repo_id is required but was None")
    if commit is None:
        raise ValueError("commit is required but was None")
    if filename is None:
        raise ValueError("filename is required but was None")

    author_name, author_email = check_swapped_emails(author_name or '', author_email or '')
    committer_name, committer_email = check_swapped_emails(committer_name or '', committer_email or '')
    author_email = strip_extra_amp(author_email or '')
    committer_email = strip_extra_amp(committer_email or '')
    placeholder_date = "1970-01-01 00:00:15 -0500"
    return {
        'repo_id': repos_id,
        'cmt_commit_hash': str(commit),
        'cmt_filename': filename,
        'cmt_author_name': str(author_name),
        'cmt_author_raw_email': author_email,
        'cmt_author_email': discover_alias(author_email),
        'cmt_author_date': author_date,
        'cmt_author_timestamp': author_timestamp or placeholder_date,
        'cmt_committer_name': committer_name,
        'cmt_committer_raw_email': committer_email,
        'cmt_committer_email': discover_alias(committer_email),
        'cmt_committer_date': committer_date or placeholder_date,
        'cmt_committer_timestamp': committer_timestamp or placeholder_date,
        'cmt_added': added,
        'cmt_removed': removed,
        'cmt_whitespace': whitespace,
        'cmt_date_attempted': committer_date or placeholder_date,
        'tool_source': "Facade",
        'tool_version': "0.80",
        'data_source': "git"
    }

def analyze_commit(
    logger,
    repo_id: int,
    repo_loc: str,
    commit: str
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    assert repo_id is not None, f"repo_id must not be None for commit {commit}"
    logger.debug(f"Analyzing commit {commit} for repo_id={repo_id}")

    author_name = None
    author_email = None
    author_date = None
    author_timestamp = None
    committer_name = None
    committer_email = None
    committer_date = None
    committer_timestamp = None
    header = True
    filename = ''
    added = 0
    removed = 0
    whitespace = 0
    recordsToInsert: List[Dict[str, Any]] = []

    try:
        pretty_format = (
            "author_name: %an%n"
            "author_email: %ae%n"
            "author_date:%ai%n"
            "committer_name: %cn%n"
            "committer_email: %ce%n"
            "committer_date: %ci%n"
            "parents: %p%n"
            "EndPatch"
        )
        git_log = check_output(
            [f"git", "--git-dir", repo_loc, "log", "-p", "-M", commit, "-n1",
             f"--pretty=format:{pretty_format}"]
        )
    except Exception as e:
        logger.error(f"Failed to run git log for commit {commit}: {e}")
        return [], {}

    try:
        execute_sql(s.sql.text("""
            INSERT INTO working_commits (repos_id, working_commit)
            VALUES (:repo_id, :commit)
        """).bindparams(repo_id=repo_id, commit=commit))
    except Exception as e:
        logger.error(f"Failed to insert working commit {commit} into DB: {e}")

    try:
        commit_message = check_output(
            f"git --git-dir {repo_loc} log --format=%B -n 1 {commit}".split()
        ).decode('utf-8', errors="backslashreplace").strip()
    except CalledProcessError as e:
        logger.error(f"Git failed to retrieve commit message for {commit}: {e}")
        commit_message = "<invalid commit message>"

    msg_record = {
        'repo_id': repo_id,
        'cmt_msg': commit_message,
        'cmt_hash': commit,
        'tool_source': 'Facade',
        'tool_version': '0.80',
        'data_source': 'git',
        'data_collection_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    try:
        log_output = git_log.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Failed to read stdout from git process for commit {commit}: {e}")
        return [], msg_record

    whitespaceCheck = []
    resetRemovals = True

    for line in log_output.split(os.linesep):
        if len(line) == 0:
            continue

        if line.startswith('author_name:'):
            author_name = line[13:]
            continue
        if line.startswith('author_email:'):
            author_email = line[14:]
            continue
        if line.startswith('author_date:'):
            author_date = line[12:22]
            author_timestamp = line[12:]
            continue
        if line.startswith('committer_name:'):
            committer_name = line[16:]
            continue
        if line.startswith('committer_email:'):
            committer_email = line[17:]
            continue
        if line.startswith('committer_date:'):
            committer_date = line[16:26]
            committer_timestamp = line[16:]
            continue
        if line.startswith('parents:'):
            if len(line[9:].split(' ')) == 2:
                filename = '(Merge commit)'
                added = removed = whitespace = 0
            continue
        if line.startswith('--- a/'):
            if filename == '(Deleted) ':
                filename += line[6:]
            continue
        if line.startswith('+++ b/'):
            if not filename.startswith('(Deleted) '):
                filename = line[6:]
            continue
        if line.startswith('rename to '):
            filename = line[10:]
            continue
        if line.startswith('deleted file '):
            filename = '(Deleted) '
            continue
        if line.startswith('diff --git'):
            if not header:
                try:
                    record = generate_commit_record(
                        repo_id, commit, filename,
                        author_name, author_email, author_date, author_timestamp,
                        committer_name, committer_email, committer_date, committer_timestamp,
                        added, removed, whitespace
                    )
                    recordsToInsert.append(record)
                except Exception as e:
                    logger.error(f"Failed to generate commit record for {commit}: {e}")
            header = False
            whitespaceCheck = []
            resetRemovals = True
            filename = ''
            added = removed = whitespace = 0
            continue

        if not header:
            if line[0] == '+':
                if len(line.strip()) == 1:
                    whitespace += 1
                else:
                    whitespaceChange = False
                    for check in whitespaceCheck:
                        if line[1:].strip() == check and len(line[1:].strip()) > 8:
                            whitespaceChange = True
                            break
                    if whitespaceChange:
                        removed -= 1
                        whitespace += 1
                        whitespaceCheck.remove(line[1:].strip())
                    else:
                        added += 1
                resetRemovals = True
            elif line[0] == '-':
                removed += 1
                if resetRemovals:
                    whitespaceCheck = []
                    resetRemovals = False
                whitespaceCheck.append(line[1:].strip())

    try:
        record = generate_commit_record(
            repo_id, commit, filename,
            author_name, author_email, author_date, author_timestamp,
            committer_name, committer_email, committer_date, committer_timestamp,
            added, removed, whitespace
        )
        recordsToInsert.append(record)
    except Exception as e:
        logger.error(f"Final record creation failed for commit {commit}: {e}")

    return recordsToInsert, msg_record
