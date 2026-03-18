# SPDX-License-Identifier: MIT
import logging
import click
import sqlalchemy as s

from augur.application.cli import (
    test_connection,
    test_db_connection,
    with_database,
    DatabaseContext,
)

# from augur.application.db.session import DatabaseSession
from datetime import datetime
from augur.application.db.models import Repo

from ._cli_util import get_db_version


logger = logging.getLogger(__name__)


@click.group("selftest", short_help="Augur self-testing utilities")
@click.pass_context
def cli(ctx):
    ctx.obj = DatabaseContext()

