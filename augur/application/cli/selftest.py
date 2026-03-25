# SPDX-License-Identifier: MIT
import logging
import click
import sqlalchemy as s
import csv
from sqlalchemy import select, func
from augur.application.db.lib import get_repo_by_repo_id
from augur.application.db.session import DatabaseSession

from augur.application.config import AugurConfig
from augur.tasks.git.util.facade_worker.facade_worker.utilitymethods import get_absolute_repo_path

from augur.application.cli import (
    test_connection,
    test_db_connection,
    with_database,
    DatabaseContext,
)
from augur.application.db.models.augur_data import Commit
from pathlib import Path

# from augur.application.db.session import DatabaseSession
from datetime import datetime
from augur.application.db.models import Repo

from ._cli_util import get_db_version

from pygit2 import Repository

from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)


@click.group("selftest", short_help="Augur self-testing utilities")
@click.pass_context
def cli(ctx):
    ctx.obj = DatabaseContext()


@cli.command("report")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def run_selftest_report(ctx):
    """
    Run queries to evaluate various aspects of the augur system's functioning and produce a report
    """
    click.echo('Generating Augur selftest report....')

    cmt_author_name_issue_3740_query = (
        select(func.count())
        .select_from(Commit)
        .where(Commit.cmt_author_name == '')
    )
    cmt_author_name_issue_3740_count = None

    with ctx.obj.engine.begin() as connection:
        cmt_author_name_issue_3740_count = connection.execute(cmt_author_name_issue_3740_query).scalar_one()
        click.echo(f'Issue 3740 count: {cmt_author_name_issue_3740_count} commit files in the `commits` table contain authors with an empty string as their name')


def append_log_file(file:Path, values):
    mode = "w" if not file.exists() else "a"
    with file.open(mode, encoding="utf-8") as f:
        if isinstance(values[0], Commit):
            values_transformed = []
            for c in values:
                v = dict(c.__dict__) 
                del v['_sa_instance_state']
                values_transformed.append(v)

            values = values_transformed
            
        
        if isinstance(values[0], dict):
            
            writer = csv.DictWriter(f, fieldnames=values[0].keys())
            if mode == "w":
                writer.writeheader()
            for row in values:

                writer.writerow(row)
        else:
            f.writelines([str(r)+'\n' for r in values])


@cli.command("repair")
@click.option("--batch-size", default=1000, help="Set the number of records to repair in each repair operation (to avoid queries taking forever)")
@click.option("--dry-run", is_flag=True, default=False, help="Skip the final updating of values to demonstrate what work would be done without doing it")
@click.option("--output-dir", default=".", help="A path to the directory where output files should be written")
@click.option("--facade-dir", default=None, help="The path to the directory where facade git clones are stored")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def run_selftest_repair(ctx, batch_size, dry_run, output_dir, facade_dir):

    tool_source = "Augur Selftest Repair"
    tool_version = "0.1"

    output_dir = Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir()

    click.echo("Checking for data corrections to perform")
    
    click.echo("Checking for missing commit author names (#3740)...")

    # This checker for missing commit author names is a necessary fixup for https://github.com/chaoss/augur/issues/3740
    # it is written as a series of queries to read data esssentially field-by-field to narrow the results down because
    # the commits table actually stores commit files (https://github.com/chaoss/augur/issues/3682)
    # the structure of this tool is also intended to output a list of confirmed affected records first,
    # so that detailed records can be kept by the augur admin if desired.


    affected_commits_file = output_dir.joinpath("3740_affected_commit_hashes.csv")
    affected_repos_file = output_dir.joinpath("3740_affected_repos.csv")
    all_affected_rows_file = output_dir.joinpath("3740_all_affected_rows.csv")

    repo_base_directory = facade_dir

    if repo_base_directory is None:

        with DatabaseSession(logger, ctx.obj.engine) as session:
            config = AugurConfig(logger, session)
            
            repo_base_directory = config.get_value("Facade", "repo_directory")

    if repo_base_directory is None:
        raise ValueError("Augur should have a facade repo base directory set in the config. It is unsafe to continue without one")

    if not repo_base_directory.endswith("/"):
        repo_base_directory += "/"

    with DatabaseSession(logger, ctx.obj.engine) as session:

        click.echo("\tcounting total affected rows...", nl=False)

        total_count_query = s.select(func.count()).where(Commit.cmt_author_name == '')
        total_count = session.execute(total_count_query).scalar_one()

        click.echo(f"found {total_count} rows.")

        limit = 20
        click.echo(f"\tFetching the first {limit} affected repos...")

        # any queries that attempt to get one row per commit are incredibly slow
        query = s.select(func.distinct(Commit.repo_id)).where(Commit.cmt_author_name == '').limit(limit)
        repos = session.execute(query).scalars().all()
    
        # click.echo("\tProcessing empty commit authors")

        append_log_file(affected_repos_file, repos)


        for repo_id in repos:

            repo = get_repo_by_repo_id(repo_id)
         
            #Get the huge list of commits to process.
            absolute_path = get_absolute_repo_path(repo_base_directory, repo.repo_id, repo.repo_path, repo.repo_name)
            repo_loc = (f"{absolute_path}/.git")

            click.echo(f"\tFetching affected commits in repo id {repo_id}, path {absolute_path}...", nl=False)
            query = s.select(func.distinct(Commit.cmt_commit_hash)).where(Commit.cmt_author_name == '', Commit.repo_id == repo_id)
            unique_commit_hashes = session.execute(query).scalars().all()
            append_log_file(affected_commits_file, unique_commit_hashes)
            click.echo(len(unique_commit_hashes))

            for commithash in unique_commit_hashes:
                commit = lg2_repo[commithash]
                
                # any queries that attempt to get one row per commit are incredibly slow
                query = s.select(Commit).where(Commit.cmt_author_name == '', Commit.repo_id == repo.repo_id, Commit.cmt_commit_hash == commithash)
                commit_changes = session.execute(query).scalars().all()

                # fetch all records with this commit hash
                click.echo(f"\t{len(commit_changes)} commit change records match this hash")
                
                append_log_file(all_affected_rows_file, commit_changes)

                sample = commit_changes[0]

                conditions = [all((
                    s.cmt_author_email == commit.author.email,
                    s.cmt_committer_name == commit.committer.name,
                    s.cmt_committer_email == commit.committer.email,
                    s.cmt_committer_email == commit.committer.email,
                    s.cmt_commit_hash == commithash
                )) for s in commit_changes]
                click.echo(f"sanity check: {all(conditions)}")
                if all(conditions) == False:
                    # click.echo(repr(sample))
                    click.echo(repo.repo_git)
                    click.echo(commithash)
                    click.echo(f"{sample.cmt_author_email} ({sample.cmt_author_raw_email})")
                    click.echo(commit.author.email)
                    click.echo(sample.cmt_committer_name)
                    click.echo(commit.committer.name)
                    click.echo(f"{sample.cmt_committer_email} ({sample.cmt_committer_raw_email})")
                    click.echo(commit.committer.email)
                    click.echo(commit.message)
                    click.echo(commit.parent_ids)
                    click.prompt("enter any value and press enter to continue")
                else:
                    if not dry_run:
                        for chng in commit_changes:
                            chng.cmt_author_name = commit.author.name
                            chng.tool_source = tool_source
                            chng.tool_version = tool_version
