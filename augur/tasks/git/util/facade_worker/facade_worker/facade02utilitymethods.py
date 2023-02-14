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
import sys
import platform
import imp
import time
import datetime
import html.parser
import subprocess
import os
import getopt
import xlsxwriter
import configparser
import sqlalchemy as s
from .facade01config import get_database_args_from_env
from augur.application.db.models.augur_data import *
#from augur.tasks.git.util.facade_worker.facade

def update_repo_log(augur_db_engine, util, repos_id,status):

# Log a repo's fetch status
	util.log_activity("Info",f"{status} {repos_id}")
	#log_message = ("INSERT INTO repos_fetch_log (repos_id,status) "
	#	"VALUES (%s,%s)")
	try:
		log_message = s.sql.text("""INSERT INTO repos_fetch_log (repos_id,status) 
            VALUES (:repo_id,:repo_status)""").bindparams(repo_id=repos_id,repo_status=status)

		#session.insert_data(data,t_repos_fetch_log,['repos_id','status'])
		augur_db_engine.execute_sql(log_message)
	except Exception as e:
		util.logger.error(f"Ran into error in update_repo_log: {e}")
		pass

def trim_commit(augur_db_engine, util, repo_id,commit):

# Quickly remove a given commit

	remove_commit = s.sql.text("""DELETE FROM commits
		WHERE repo_id=:repo_id
		AND cmt_commit_hash=:hash""").bindparams(repo_id=repo_id,hash=commit)

	 
	 
	augur_db_engine.execute_sql(remove_commit)

	util.log_activity('Debug',f"Trimmed commit: {commit}")

def store_working_author(augur_db_engine, util, email):

# Store the working author during affiliation discovery, in case it is
# interrupted and needs to be trimmed.

	store = s.sql.text("""UPDATE settings
		SET value = :email
		WHERE setting = 'working_author'
		""").bindparams(email=email)

	augur_db_engine.execute_sql(store)

	util.log_activity('Debug',f"Stored working author: {email}")

def trim_author(augur_db_engine, util, email):

# Remove the affiliations associated with an email. Used when an analysis is
# interrupted during affiliation layering, and the data will be corrupt.

	trim = s.sql.text("""UPDATE commits 
		SET cmt_author_affiliation = NULL 
		WHERE cmt_author_email = :email
		""").bindparams(email=email)

	 
	 
	augur_db_engine.execute_sql(trim)

	trim = s.sql.text("""UPDATE commits
		SET cmt_committer_affiliation = NULL
		WHERE cmt_committer_email = :email
		""").bindparams(email=email)

	augur_db_engine.execute_sql(trim)

	store_working_author(augur_db_engine, 'done')

	util.log_activity('Debug',f"Trimmed working author: {email}")

