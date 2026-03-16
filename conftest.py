#SPDX-License-Identifier: MIT
import pytest
import re
import logging
import sqlalchemy as s
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import uuid
from sqlalchemy.pool import StaticPool


from augur.application.db.session import DatabaseSession
from augur.application.config import AugurConfig
from augur.application.db.engine import get_database_string, create_database_engine, parse_database_string, execute_sql_file

logger = logging.getLogger(__name__)

default_repo_id = "25430"
default_repo_group_id = "10"

def create_full_routes(routes):
    full_routes = []
    for route in routes:
        route = re.sub("<default_repo_id>", default_repo_id, route)
        route = re.sub("<default_repo_group_id>", default_repo_group_id, route)
        route = "http://localhost:5000/api/unstable/" + route
        full_routes.append(route)
    return full_routes


def create_connection(dbname='postgres'):
    """
    Creates a connection to the postgres server specified in the database string and connects to the dbname specified.
    Returns the connection and cursor objects.
    """

    db_string = get_database_string()
    user, password, host, port, _ = parse_database_string(db_string)
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn, conn.cursor()


def create_database(conn, cursor, db_name, template=None):
    """
    Creates a database with the name db_name. 
    If template is specified, the database will be created with the template specified.
    """

    if template:
        cursor.execute(sql.SQL("CREATE DATABASE {} WITH TEMPLATE {};").format(sql.Identifier(db_name), sql.Identifier(template)))
    else:
        cursor.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(db_name)))
    conn.commit()

def drop_database(cursor, db_name):
    """
    Drops the database with the name db_name.
    """

    # ensure connections are removed
    cursor.execute(sql.SQL("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{}';".format(db_name)))
    # drop temporary database
    cursor.execute(sql.SQL("DROP DATABASE {};").format(sql.Identifier(db_name)))


def generate_db_from_template(template_name):
    """
    Generator function that creates a new database from the template specified.
    Yields the engine object for the database created.
    """

    db_string = get_database_string()

    user, password, host, port, _ = parse_database_string(db_string)

    # Connect to the default 'postgres' database
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname='postgres'
    )

    # Set the isolation level to AUTOCOMMIT because CREATE DATABASE 
    # cannot be executed in a transaction block
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    test_db_name = "test_db_" + uuid.uuid4().hex

    # remove database_name and add test_db_name
    test_db_string = db_string[:db_string.rfind("/")+1] + test_db_name
    
    create_database(conn, cursor, test_db_name, template_name)

    # create engine to connect to db
    engine = create_database_engine(test_db_string, poolclass=StaticPool, connect_args={"application_name": f"augur tests"})


    yield engine

    # dispose engine
    engine.dispose()

    drop_database(cursor, test_db_name)

    # Close the cursor and the connection
    cursor.close()
    conn.close()


def generate_template_db(sql_file_path):
    """
    Generator function that creates a new database and install the sql file specified
    Yields the name of the database created.
    """

    db_string = get_database_string()

    user, password, host, port, _ = parse_database_string(db_string)

    # Connect to the default 'postgres' database
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname='postgres'
    )

    # Set the isolation level to AUTOCOMMIT because CREATE DATABASE 
    # cannot be executed in a transaction block
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()


    test_db_name = "test_db_template_" + uuid.uuid4().hex
    create_database(conn, cursor, test_db_name)

    # Install schema
    execute_sql_file(sql_file_path, test_db_name, user, password, host, port)


    # ensure connections are removed
    cursor.execute(sql.SQL("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{}';".format(test_db_name)))

    # drop temporary database

    yield test_db_name

    drop_database(cursor, test_db_name)

    # Close the cursor and the connection
    cursor.close()
    conn.close()



@pytest.fixture(scope='session')
def empty_db_template():
    """ 
    This fixture creates a template database with the entire schema installed.
    Returns the name of the database created.
    """

    yield from generate_template_db("tests/entire_db.sql")


@pytest.fixture(scope='session')
def empty_db(empty_db_template):
    """
    This fixture creates a database from the empty_db_template
    """

    yield from generate_db_from_template(empty_db_template)


# TODO: Add populated db template and populated db fixtures so this fixture is more useful
@pytest.fixture(scope='session')
def read_only_db(empty_db):
    """
    This fixtture creates a read-only database from the populated_db_template.
    Yields a read-only engine object for the populated_db.
    """

    database_name = empty_db.url.database
    test_username = "testuser"
    test_password = "testpass"
    schemas = ["public", "augur_data", "augur_operations"]

    # create read-only user
    empty_db.execute(s.text(f"CREATE USER testuser WITH PASSWORD '{test_password}';"))
    empty_db.execute(s.text(f"GRANT CONNECT ON DATABASE {database_name} TO {test_username};"))
    for schema in schemas:
        empty_db.execute(s.text(f"GRANT USAGE ON SCHEMA {schema} TO {test_username};"))
        empty_db.execute(s.text(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {test_username};"))

    # create engine for read-only user
    db_string = get_database_string()
    _, _, host, port, _ = parse_database_string(db_string)
    read_only_engine = s.create_engine(f'postgresql+psycopg2://{test_username}:{test_password}@{host}:{port}/{database_name}')
        
    yield read_only_engine

    read_only_engine.dispose()

    # remove read-only user
    empty_db.execute(s.text(f'REVOKE CONNECT ON DATABASE {database_name} FROM {test_username};'))
    for schema in schemas:
        empty_db.execute(s.text(f'REVOKE USAGE ON SCHEMA {schema} FROM {test_username};'))
        empty_db.execute(s.text(f'REVOKE SELECT ON ALL TABLES IN SCHEMA {schema} FROM {test_username};'))
    empty_db.execute(s.text(f'DROP USER {test_username};'))
    

@pytest.fixture
def test_db_engine():

    # creates database engine the normal way and then gets the database string
    db_string = get_database_string()

    db_string_without_db_name = re.search(r"(.+:\/\/.+\/).+", db_string).groups()[0]

    testing_db_string = db_string_without_db_name + "augur-test"

    yield s.create_engine(testing_db_string)

@pytest.fixture
def test_db_session(test_db_engine):
    session = DatabaseSession(logger, test_db_engine)

    yield session

    session.close()

@pytest.fixture
def test_db_config(test_db_session):
    return AugurConfig(logger, test_db_session)


# @pytest.fixture(scope="session")
# def augur_app():
#     augur_app = Application(disable_logs=True)
#     return augur_app

# @pytest.fixture(scope="session")
# def metrics(augur_app):
#     return augur_app.metrics

# @pytest.fixture(scope="session")
# def client(augur_app):
#     flask_client = initialize_components(augur_app, disable_housekeeper=True).load()
#     return flask_client.test_client()
