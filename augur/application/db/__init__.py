from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from augur.application.db.engine import create_database_engine, get_database_string

from metadata import __version__

engine = None
Session = None

def get_engine():
    global engine, Session

    if engine is None:
        url = get_database_string()
        engine = create_database_engine(url=url, poolclass=StaticPool, connect_args={"application_name": f"augur v{__version__}"})  
        Session = sessionmaker(bind=engine)
    
    return engine


def dispose_database_engine():
    global engine
    if engine:
        engine.dispose()
        engine = None


@contextmanager
def get_session():
    global Session
    if Session is None:
        # if the session is not initialized then call get_engine to initialize it
        get_engine()
    
    session = Session()
    try:
        yield session
    finally:
        session.close()

@contextmanager
def temporary_database_engine():

    url = get_database_string()
    temporary_database_engine = create_database_engine(url=url, poolclass=StaticPool, connect_args={"application_name": f"augur v{__version__} temporary"})  

    try:
        yield temporary_database_engine
    finally:
        temporary_database_engine.dispose()