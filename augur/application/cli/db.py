# SPDX-License-Identifier: MIT
import os
from os import environ, chmod, path, getenv
import logging
from sys import exit
from subprocess import check_call
import random
import string
import click
import sqlalchemy as s
import pandas as pd
import json
import re
import stat as stat_module

from augur.application.cli import (
    test_connection,
    test_db_connection,
    with_database,
    DatabaseContext,
)

from augur.application.db.session import DatabaseSession
from augur.application.config import ConfigPaths
from sqlalchemy import update
from datetime import datetime
from augur.application.db.models import Repo
from augur.application.cli._csv_utils import (
    process_repo_csv,
    process_repo_group_csv,
)

logger = logging.getLogger(__name__)


@click.group("db", short_help="Database utilities")
@click.pass_context
def cli(ctx):
    ctx.obj = DatabaseContext()


@cli.command("add-repos")
@click.argument("filename", type=click.Path(exists=True))
@test_connection
@test_db_connection
@with_database
@click.pass_context
def add_repos(ctx: click.Context, filename: str) -> None:
    """Add repositories to Augur's database from a CSV file.

    The CSV file can have headers (recommended):
        repo_url,repo_group_id
        https://github.com/chaoss/augur.git,10

    Or no headers (backward compatible - column order will be auto-detected):
        https://github.com/chaoss/augur.git,10

    NOTE: The Group ID must already exist in the REPO_Groups Table.

    Args:
        ctx: Click context object containing the database engine
        filename: Path to the CSV file containing repository data

    Raises:
        ValueError: If CSV file is malformed or exceeds size limit
        Exception: For database connection or other unexpected errors

    Note:
        If you want to add an entire GitHub organization, refer to the
        command: augur db add-github-org
    """
    from augur.tasks.github.util.github_task_session import GithubTaskSession
    from augur.util.repo_load_controller import RepoLoadController

    with GithubTaskSession(logger, engine=ctx.obj.engine) as session:
        controller = RepoLoadController(session)

        try:
            # Parse CSV (handles headers and column detection)
            rows = process_repo_csv(filename)

            if not rows:
                logger.error("No valid rows found in CSV file")
                return

            logger.info(f"Processing {len(rows)} repositories...")

            # Process each row using EXISTING logic
            successful = 0
            rejections = []

            for idx, row in enumerate(rows, start=1):
                try:
                    repo_data = {
                        "url": row["repo_url"],
                        "repo_group_id": int(row["repo_group_id"]),
                    }
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid data format: {row}, error: {e}")
                    rejections.append((row, f"Invalid format: {e}"))
                    continue

                print(
                    f"Inserting repo {idx}/{len(rows)} with Git URL `{repo_data['url']}` into repo group {repo_data['repo_group_id']}"
                )

                succeeded, message = controller.add_cli_repo(repo_data)
                if succeeded:
                    successful += 1
                    logger.info(f"Repo added: {repo_data}")
                    print("Success")
                else:
                    logger.error(f"insert repo failed with error: {message['status']}")
                    rejections.append((row, f"Failed to add repo: {message['status']}"))

            logger.info(f"Successfully added {successful} repositories")

            if rejections:
                logger.warning(f"{len(rejections)} repositories failed:")
                for row_data, reason in rejections:
                    logger.warning(f"  - {row_data}: {reason}")

        except ValueError as e:
            logger.error(f"CSV processing error: {e}")
            return
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


@cli.command("get-repo-groups")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def get_repo_groups(ctx: click.Context) -> pd.DataFrame:
    """
    List all repo groups and their associated IDs
    """

    with ctx.obj.engine.connect() as connection:
        df = pd.read_sql(
            s.sql.text(
                "SELECT repo_group_id, rg_name, rg_description FROM augur_data.repo_groups"
            ),
            connection,
        )
    print(df)

    return df


@cli.command("add-repo-groups")
@click.argument("filename", type=click.Path(exists=True))
@test_connection
@test_db_connection
@with_database
@click.pass_context
def add_repo_groups(ctx: click.Context, filename: str) -> None:
    """Create new repo groups in Augur's database from a CSV file.

    Args:
        ctx: Click context object containing the database engine
        filename: Path to the CSV file containing repository group data

    Raises:
        ValueError: If CSV file is malformed or exceeds size limit
        Exception: For database connection or other unexpected errors
    """
    try:
        # Parse CSV (handles headers and column detection)
        rows = process_repo_group_csv(filename)

        if not rows:
            logger.error("No valid rows found in CSV file")
            return

        logger.info(f"Processing {len(rows)} repository groups...")

        with ctx.obj.engine.begin() as connection:
            # Get existing repo group IDs
            df = pd.read_sql(
                s.sql.text("SELECT repo_group_id FROM augur_data.repo_groups"),
                connection,
            )
            repo_group_IDs = df["repo_group_id"].values.tolist()

            insert_repo_group_sql = s.sql.text(
                """
            INSERT INTO "augur_data"."repo_groups"("repo_group_id", "rg_name", "rg_description", "rg_website", "rg_recache", "rg_last_modified", "rg_type", "tool_source", "tool_version", "data_source", "data_collection_date") VALUES (:repo_group_id, :repo_group_name, '', '', 0, CURRENT_TIMESTAMP, 'Unknown', 'Loaded by user', '1.0', 'Git', CURRENT_TIMESTAMP);
            """
            )

            # Process each row
            successful = 0
            rejections = []

            for row in rows:
                try:
                    group_id = int(row["repo_group_id"])
                    group_name = row["repo_group_name"]
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid data format: {row}, error: {e}")
                    rejections.append((row, f"Invalid format: {e}"))
                    continue

                # Check if already exists
                if group_id in repo_group_IDs:
                    logger.info(f"Repo group {group_id} already exists, skipping")
                    continue

                try:
                    logger.info(
                        f"Inserting repo group: ID={group_id}, Name={group_name}"
                    )
                    connection.execute(
                        insert_repo_group_sql.bindparams(
                            repo_group_id=group_id,
                            repo_group_name=group_name,
                        )
                    )
                    successful += 1
                    repo_group_IDs.append(group_id)
                except Exception as e:
                    logger.error(f"Failed to insert repo group {group_id}: {e}")
                    rejections.append((row, f"Database error: {e}"))

            logger.info(f"Successfully added {successful} repository groups")

            if rejections:
                logger.warning(f"{len(rejections)} repository groups failed:")
                for row_data, reason in rejections:
                    logger.warning(f"  - {row_data}: {reason}")

    except ValueError as e:
        logger.error(f"CSV processing error: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


@cli.command("add-github-org")
@click.argument("organization_name")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def add_github_org(ctx, organization_name):
    """
    Create new repo groups in Augur's database
    """
    from augur.tasks.github.util.github_task_session import GithubTaskSession
    from augur.util.repo_load_controller import RepoLoadController

    with GithubTaskSession(logger, engine=ctx.obj.engine) as session:
        controller = RepoLoadController(session)

        controller.add_cli_org(organization_name)


# get_db_version is a helper function to print_db_version and upgrade_db_version
def get_db_version(engine):
    db_version_sql = s.sql.text(
        """
        SELECT * FROM augur_operations.augur_settings WHERE setting = 'augur_data_version'
        """
    )

    with engine.connect() as connection:
        result = int(connection.execute(db_version_sql).fetchone()[2])

    engine.dispose()
    return result


@cli.command("print-db-version")
@test_connection
@test_db_connection
def print_db_version():
    """
    Get the version of the configured database
    """
    check_call(["alembic", "current"])


@cli.command("upgrade-db-version")
@test_connection
@test_db_connection
def upgrade_db_version():
    """
    Upgrade the configured database to the latest version
    """
    check_call(["alembic", "upgrade", "head"])


@cli.command("check-for-upgrade")
@test_connection
@test_db_connection
def check_for_upgrade():
    """
    Show available database migration history
    """
    check_call(["alembic", "history", "-i"])


@cli.command("create-schema")
@test_connection
@test_db_connection
def create_schema():
    """
    Create schema in the configured database
    """
    check_call(["alembic", "upgrade", "head"])


def generate_key(length):
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


@cli.command("generate-api-key")
@click.pass_context
def generate_api_key(ctx):
    """
    Generate and set a new Augur API key
    """
    key = generate_key(32)
    ctx.invoke(update_api_key, api_key=key)
    print(key)


@cli.command("update-api-key")
@click.argument("api_key")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def update_api_key(ctx, api_key):
    """
    Update the API key in the database to the given key
    """
    update_api_key_sql = s.sql.text(
        """
        INSERT INTO augur_operations.augur_settings (setting,VALUE) VALUES ('augur_api_key','HudMhTyPW7wiaWopUKgRoGCxlIUulw4g') ON CONFLICT (setting)
        DO
        UPDATE
        SET VALUE='HudMhTyPW7wiaWopUKgRoGCxlIUulw4g';
        --UPDATE augur_operations.augur_settings SET VALUE = :api_key WHERE setting='augur_api_key';
    """
    )

    with ctx.obj.engine.begin() as connection:
        connection.execute(update_api_key_sql, api_key=api_key)
        logger.info(f"Updated Augur API key to: {api_key}")


@cli.command("get-api-key")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def get_api_key(ctx):
    get_api_key_sql = s.sql.text(
        """
        SELECT value FROM augur_operations.augur_settings WHERE setting='augur_api_key';
    """
    )

    try:
        with ctx.obj.engine.connect() as connection:
            print(connection.execute(get_api_key_sql).fetchone()[0])
    except TypeError:
        print("No Augur API key found.")


@cli.command(
    "check-pgpass",
    short_help="Check the ~/.pgpass file for Augur's database credentials",
)
def check_pgpass():
    augur_db_env_var = getenv("AUGUR_DB")
    if augur_db_env_var:
        # gets the user, passowrd, host, port, and database_name out of environment variable
        # assumes database string of structure <beginning_of_db_string>//<user>:<password>@<host>:<port>/<database_name>
        # it returns a tuple like (<user>, <password>, <host>, <port>, <database_name)
        db_string_parsed = re.search(
            r"^.+:\/\/([a-zA-Z0-9_]+):(.+)@([a-zA-Z0-9-_~\.]+):(\d{1,5})\/([a-zA-Z0-9_-]+)",
            augur_db_env_var,
        ).groups()

        if db_string_parsed:
            db_config = {
                "user": db_string_parsed[0],
                "password": db_string_parsed[1],
                "host": db_string_parsed[2],
                "port": db_string_parsed[3],
                "database_name": db_string_parsed[4],
            }

            check_pgpass_credentials(db_config)

        else:
            print("Database string is invalid and cannot be used")

    else:
        config = ConfigPaths.read_db_config()
        print(f"Config from {ConfigPaths.db_config()}: {config}")
        check_pgpass_credentials(config)


@cli.command("init-database")
@click.option("--default-db-name", default="postgres")
@click.option("--default-user", default="postgres")
@click.option("--default-password", default="postgres")
@click.option("--target-db-name", default="augur")
@click.option("--target-user", default="augur")
@click.option("--target-password", default="augur")
@click.option("--host", default="localhost")
@click.option("--port", default="5432")
@test_connection
def init_database(
    default_db_name,
    default_user,
    default_password,
    target_db_name,
    target_user,
    target_password,
    host,
    port,
):
    """
    Create database with the given credentials using the given maintenance database
    """
    config = {
        "Database": {
            "name": default_db_name,
            "user": default_user,
            "password": default_password,
            "host": host,
            "port": port,
        }
    }
    check_pgpass_credentials(config)
    run_db_creation_psql_command(
        host, port, default_user, default_db_name, f"CREATE DATABASE {target_db_name};"
    )
    run_db_creation_psql_command(
        host,
        port,
        default_user,
        default_db_name,
        f"CREATE USER {target_user} WITH ENCRYPTED PASSWORD '{target_password}';",
    )
    run_db_creation_psql_command(
        host,
        port,
        default_user,
        default_db_name,
        f"ALTER DATABASE {target_db_name} OWNER TO {target_user};",
    )
    run_db_creation_psql_command(
        host,
        port,
        default_user,
        default_db_name,
        f"GRANT ALL PRIVILEGES ON DATABASE {target_db_name} TO {target_user};",
    )


@cli.command("reset-repo-age")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def reset_repo_age(ctx):
    with DatabaseSession(logger, engine=ctx.obj.engine) as session:
        update_query = update(Repo).values(repo_added=datetime.now())

        session.execute(update_query)
        session.commit()


@cli.command("test-connection")
@test_connection
@test_db_connection
def test_db_connection():
    print("Successful db connection")


# TODO: Fix this function
def run_psql_command_in_database(target_type, target):
    if target_type not in ["-f", "-c"]:
        logger.error("Invalid target type. Exiting...")
        exit(1)

    augur_db_environment_var = getenv("AUGUR_DB")

    # db_json_file_location = os.getcwd() + "/db.config.json"
    # db_json_exists = os.path.exists(db_json_file_location)

    if augur_db_environment_var:
        pass
        # TODO: Add functionality for environment variable
    else:
        db_config = ConfigPaths.read_db_config()

        host = db_config["host"]
        database_name = db_config["database_name"]

        db_conn_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database_name']}"
        engine = s.create_engine(db_conn_string)

    check_call(
        [
            "psql",
            "-h",
            host,
            "-d",
            database_name,
            "-U",
            user,
            "-p",
            port,
            "-a",
            "-w",
            target_type,
            target,
        ]
    )


def check_pgpass_credentials(config):
    pgpass_file_path = environ["HOME"] + "/.pgpass"

    if not path.isfile(pgpass_file_path):
        print("~/.pgpass does not exist, creating.")
        with open(pgpass_file_path, "w+", encoding="utf-8") as _:
            chmod(pgpass_file_path, stat_module.S_IWRITE | stat_module.S_IREAD)

    pgpass_file_mask = oct(os.stat(pgpass_file_path).st_mode & 0o777)

    if pgpass_file_mask != "0o600":
        print("Updating ~/.pgpass file permissions.")
        chmod(pgpass_file_path, stat_module.S_IWRITE | stat_module.S_IREAD)

    with open(pgpass_file_path, "a+", encoding="utf-8") as pgpass_file:
        end = pgpass_file.tell()
        pgpass_file.seek(0)

        credentials_string = (
            str(config["host"])
            + ":"
            + str(config["port"])
            + ":"
            + str(config["database_name"])
            + ":"
            + str(config["user"])
            + ":"
            + str(config["password"])
        )

        if credentials_string.lower() not in [
            "".join(line.split()).lower() for line in pgpass_file.readlines()
        ]:
            print("Adding credentials to $HOME/.pgpass")
            pgpass_file.seek(end)
            pgpass_file.write(credentials_string + "\n")
        else:
            print("Credentials found in $HOME/.pgpass")
