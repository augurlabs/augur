from logging.config import fileConfig


from alembic import context
from augur.application.db.models.base import Base
from augur.application.db.engine import get_database_string
from sqlalchemy import create_engine
from dotenv import load_dotenv
import re
from pathlib import Path

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

sqlalchemy_url = get_database_string()

VERSIONS_DIR = Path(__file__).parent / "versions"

def _next_int_rev() -> str:
    max_rev = 0
    for p in VERSIONS_DIR.glob("*.py"):
        pathname = Path(p).name
        m = re.search(r"^([\d]+)_[a-zA-Z0-9_]+.py", pathname, re.M)
        if m and m.group(1).isdigit():
            max_rev = max(max_rev, int(m.group(1)))
    return str(max_rev + 1)

def process_revision_directives(context, revision, directives):
    if not directives:
        return
    script = directives[0]
    # If user passed --rev-id, honor it; otherwise override Alembic's default
    opts = getattr(context.config, "cmd_opts", None)
    user_rev_id = getattr(opts, "rev_id", None)
    if user_rev_id:
        script.rev_id = str(user_rev_id)
    else:
        script.rev_id = _next_int_rev()


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=sqlalchemy_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = sqlalchemy_url
    engine = create_engine(url)



    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
