# SPDX-License-Identifier: MIT
import logging
import click
import sqlalchemy as s
from sqlalchemy import select, func

from augur.application.cli import (
    test_connection,
    test_db_connection,
    with_database,
    DatabaseContext,
)
from augur.application.db.models.augur_data import Commit

# from augur.application.db.session import DatabaseSession
from datetime import datetime
from augur.application.db.models import Repo

from ._cli_util import get_db_version


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
