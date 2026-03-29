====================
Database Commands
====================

``augur db``
=============

The collection of ``augur db`` commands is for interacting with the database.

``add-repo-groups``
--------------------
The ``add-repo-groups`` command is used to create new repo groups. When given a path to a correctly formatted ``.csv`` file, it will create each repo group specified in the file with the corresponding ID and name.

The ``.csv`` file must have the following format::

  <repo_group_id>,<repo_group_name>
  ...

Where ``<repo_group_id>`` is the desired ID of the new repo group, and ``<repo_group_name>`` is the desired name of the new repo group.

Each pair of values should be on its own line (indicated by the ...), without quotes, and there should be no column headers.

Example usage\:

.. code-block:: bash

  # to add new repos to the database
  $ uv run augur db add-repo-groups repo_groups.csv

  # contents of repo_groups.csv
  10,Repo Group 1
  20,Repo Group 2

  # successful output looks like:
  > CLI: [db.add_repo_groups] [INFO] Inserting repo group with name Repo Group 1 and ID 10...
  > CLI: [db.add_repo_groups] [INFO] Inserting repo group with name Repo Group 2 and ID 20...


``get-repo-groups``
--------------------
The ``get-repo-groups`` command will return the ID, name, and description of all repo groups in the database.

Example usage\:

.. code-block:: bash

  # to retrieve the repo groups
  $ uv run augur db get-repo-groups

  # successful output looks like:
  >    repo_group_id             rg_name                                     rg_description
  > 0              1  Default Repo Group  The default repo group created by the schema g...
  > 1             10        Repo Group 1
  > 2             20        Repo Group 2



``add-repos``
--------------
The ``add-repos`` command is used to load new repos. When given a path to a correctly formatted ``.csv`` file, it will insert each repo specified in the file into its corresponding repo group in the database specified in the config file.

The ``.csv`` file must have the following format:

.. code::

  <git_repo_url>,<repo_group_id>,
  ...

where ``<repo_group_id>`` is an **existing** repository group ID, and ``<git_repo_url>`` is the url to the repository's Git repository, e.g. ``https://github.com/chaoss/augur.git``.
Each pair of values should be on its own line (indicated by the ...), without quotes, and there should be no column headers.

.. note::

  If you don't know what ``repo_group_id`` to use, run the ``augur db get-repo-groups`` command to view the repo groups that are currently in your DB; unless you've deleted it, there should be a default one that you can use.

Example usage\:

.. code-block:: bash

  # contents of repos.csv
  https://github.com/chaoss/augur.git,10
  https://github.com/chaoss/grimoirelab.git,10
  https://github.com/chaoss/wg-evolution.git,20
  https://github.com/chaoss/wg-risk.git,20
  https://github.com/chaoss/wg-common.git,20
  https://github.com/chaoss/wg-value.git,20
  https://github.com/chaoss/wg-diversity-inclusion.git,20
  https://github.com/chaoss/wg-app-ecosystem.git,20

  # to add repos to the database
  $ augur db add-repos repos.csv

  # successful output looks like
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/augur.git` into repo group 10
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/grimoirelab.git` into repo group 10
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/wg-evolution.git` into repo group 20
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/wg-risk.git` into repo group 20
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/wg-common.git` into repo group 20
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/wg-value.git` into repo group 20
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/wg-diversity-inclusion.git` into repo group 20
  > CLI: [db.add_repos] [INFO] Inserting repo with Git URL `https://github.com/chaoss/wg-app-ecosystem.git` into repo group 20


``generate-api-key``
-------------------------
The ``generate-api-key`` command will generate a new Augur API key and update the database with the new key. Output is the generated key.

Example usage\:

.. code-block:: bash

  # to generate a key
  $ uv run augur db generate-api-key

  # successful output looks like (this will be an actual key):
  > CLI: [db.update_api_key] [INFO] Updated Augur API key to: new_key_abc_123
  > new_key_abc_123


``get-api-key``
-------------------------
The ``get-api-key`` command will return the API key of the currently configured database. Output is the API key.

Example usage\:

.. code-block:: bash

  # to retrieve the key
  $ uv run augur db get-api-key

  # successful output looks like (this will be an actual key):
  > existing_key_def_456


``print-db-version``
-------------------------
The ``print-db-version`` command will give user the current version of the configured database on their system.

Example usage\:

.. code-block:: bash

  # to return the current database version
  $ uv run augur db print-db-version

  # successful output looks like:
  > 1


``upgrade-db-version``
-------------------------
The ``upgrade-db-version`` command will upgrade the user's current database to the latest version.

Example usage\:

.. code-block:: bash

  # to upgrade the user's database to the current version
  $ uv run augur db upgrade-db-version

  # successful output if your DB is already up to date
  > CLI: [db.check_pgpass_credentials] [INFO] Credentials found in $HOME/.pgpass
  > CLI: [db.upgrade_db_version] [INFO] Your database is already up to date.

  # successful output if your DB needs to be upgraded
  > [INFO] Attempting to load config file
  > [INFO] Config file loaded successfully
  > CLI: [db.check_pgpass_credentials] [INFO] Credentials found in $HOME/.pgpass
  > CLI: [db.upgrade_db_version] [INFO] Upgrading from 16 to 17
  > ALTER TABLE "augur_data"."repo"
  >   ALTER COLUMN "forked_from" TYPE varchar USING "forked_from"::varchar;
  > ALTER TABLE
  > ALTER TABLE "augur_data"."repo"
  >   ADD COLUMN "repo_archived" int4,
  >   ADD COLUMN "repo_archived_date_collected" timestamptz(0),
  >   ALTER COLUMN "forked_from" TYPE varchar USING "forked_from"::varchar;
  > ALTER TABLE
  > update "augur_operations"."augur_settings" set value = 17 where setting = 'augur_data_version';
  > UPDATE 1
  > CLI: [db.upgrade_db_version] [INFO] Upgrading from 17 to 18
  > etc...


``create-schema``
------------------
The ``create-schema`` command will attempt to create the Augur schema in the database defined in your config file.

Example usage\:

.. code-block:: bash

  # to create the schema
  $ uv run augur db create-schema

.. note::
  If this runs successfully, you should see a bunch of schema creation commands fly by pretty fast. If everything worked you should see: ``update "augur_operations"."augur_settings" set value = xx where setting = 'augur_data_version';`` at the end.
