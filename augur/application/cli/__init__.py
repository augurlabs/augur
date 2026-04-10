#SPDX-License-Identifier: MIT
import click
from functools import update_wrapper
import os
import sys
import re
import json
import httpx
import traceback

from augur.application.db.engine import DatabaseEngine
from augur.application.db import get_engine, dispose_database_engine
from sqlalchemy.exc import OperationalError 


def test_connection(function_internet_connection):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        usage = re.search(r"Usage:\s(.*)\s\[OPTIONS\]", str(ctx.get_usage())).groups()[0]
        success = False
        with httpx.Client() as client:
            try:
                _ = client.request(
                    method="GET", url="http://chaoss.community", timeout=10, follow_redirects=True)
                success = True
            except (TimeoutError, httpx.TimeoutException):
                print("Request timed out.")
            except httpx.NetworkError as e:
                print(f"Network Error: {httpx.NetworkError}")
                print(traceback.format_exc())
            except httpx.ProtocolError as e:
                print(f"Protocol Error: {httpx.ProtocolError}")
                print(traceback.format_exc())

            if not success:
                raise click.ClickException(
                    f"""
                    {usage} command setup failed.
                    There was an error while testing for network connectivity
                    Please check your connection to the internet to run Augur
                    Consider setting http_proxy variables for limited access installations."""
                )
                
        
        return ctx.invoke(function_internet_connection, *args, **kwargs)
        
    return update_wrapper(new_func, function_internet_connection)

def test_db_connection(function_db_connection):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        engine = DatabaseEngine().engine
        usage = re.search(r"Usage:\s(.*)\s\[OPTIONS\]", str(ctx.get_usage())).groups()[0]
        try:
            engine.connect()
            engine.dispose()
            return ctx.invoke(function_db_connection, *args, **kwargs)
        except OperationalError as e:

            augur_db_environment_var = os.getenv("AUGUR_DB")

            # determine the location to print in error string
            if augur_db_environment_var:
                location = f"the AUGUR_DB environment variable\nAUGUR_DB={os.getenv('AUGUR_DB')}"
            else:
                with open("db.config.json", 'r') as f:
                    db_config = json.load(f)
                    location = f"db.config.json\nYour db.config.json is: {db_config}"
            
            incorrect_values = "host name is" 
            #  determine which value in the database string is causing the error
            if "could not translate host name" in str(e):
                incorrect_values = "host name is" 

            elif "Connection refused" in str(e):
                incorrect_values = "port is"

            elif "password authentication failed for user" in str(e):
                incorrect_values = "username or password are"
                
            elif "database" in str(e) and "does not exist" in str(e):
                incorrect_values = "database name is" 

            else:
                print(f"Database connection error: {e}")

            if incorrect_values:
                print(f"\n\n{usage} command setup failed\nERROR: connecting to database\nHINT: The {incorrect_values} may be incorrectly specified in {location}\n")
                
            engine.dispose()
            sys.exit(-2)
        
    return update_wrapper(new_func, function_db_connection)


class DatabaseContext():
    def __init__(self):
        self.engine = None

def with_database(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        ctx.obj.engine = get_engine()
        try:
            return ctx.invoke(f, *args, **kwargs)
        finally:
            dispose_database_engine()
    return new_func


# def pass_application(f):
#     @click.pass_context
#     def new_func(ctx, *args, **kwargs):
#         ctx.obj = Application()
#         return ctx.invoke(f, ctx.obj, *args, **kwargs)
#     return update_wrapper(new_func, f)

# def pass_config(f):
#     @click.pass_context
#     def new_func(ctx, *args, **kwargs):
#         ctx.obj = Application(offline_mode=True).config
#         return ctx.invoke(f, ctx.obj, *args, **kwargs)
#     return update_wrapper(new_func, f)

# def pass_logs_dir(f):
#     @click.pass_context
#     def new_func(ctx, *args, **kwargs):
#         config = AugurConfig(ROOT_AUGUR_DIRECTORY)
#         ctx.obj = AugurLogging.get_log_directories(config, reset_logfiles=False)
#         return ctx.invoke(f, ctx.obj, *args, **kwargs)
#     return update_wrapper(new_func, f)

# def initialize_logging(f):
#     def new_func(*args, **kwargs):
#         AugurLogging(reset_logfiles=False)
#         return f(*args, **kwargs)
#     return update_wrapper(new_func, f)