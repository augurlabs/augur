#SPDX-License-Identifier: MIT
"""
Augur library script for generating a config file
"""
import os
import click
import json
import logging

from augur.application.db.models import Config
from augur.application.db.session import DatabaseSession
from augur.application.config import AugurConfig, redact_setting_value
from augur.application.cli import DatabaseContext, test_connection, test_db_connection, with_database
from augur.util.inspect_without_import import get_phase_names_without_import
ROOT_AUGUR_DIRECTORY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

logger = logging.getLogger(__name__)

ENVVAR_PREFIX = "AUGUR_"

@click.group('config', short_help='Generate an augur.config.json')
@click.pass_context
def cli(ctx):
    ctx.obj = DatabaseContext()

@cli.command('init')
@click.option('--github-api-key', help="GitHub API key for data collection from the GitHub API", envvar=ENVVAR_PREFIX + 'GITHUB_API_KEY')
@click.option('--facade-repo-directory', help="Directory on the database server where Facade should clone repos", envvar=ENVVAR_PREFIX + 'FACADE_REPO_DIRECTORY')
@click.option('--gitlab-api-key', help="GitLab API key for data collection from the GitLab API", envvar=ENVVAR_PREFIX + 'GITLAB_API_KEY')
@click.option('--redis-conn-string', help="String to connect to redis cache", envvar=ENVVAR_PREFIX + 'REDIS_CONN_STRING')
@click.option('--rabbitmq-conn-string', help="String to connect to rabbitmq broker", envvar=ENVVAR_PREFIX + 'RABBITMQ_CONN_STRING')
@click.option('--logs-directory', help="Directory to store logs", envvar=ENVVAR_PREFIX + 'LOGS_DIRECTORY')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def init_config(ctx, github_api_key, facade_repo_directory, gitlab_api_key, redis_conn_string, rabbitmq_conn_string, logs_directory):

    if not github_api_key:

        github_api_key = str(input("Please enter a valid github api key: "))

    if not gitlab_api_key:

        gitlab_api_key = str(input("Please enter a valid gitlab api key: "))

    if not facade_repo_directory:

        while True:

            facade_repo_directory = str(input("Please enter an existing facade repo directory: ")).strip()

            if os.path.isdir(facade_repo_directory):
                break
            else:
                print("Invalid directory")

    if facade_repo_directory[-1] != "/":
        facade_repo_directory += "/"
            

    keys = {}

    keys["github_api_key"] = github_api_key
    keys["gitlab_api_key"] = gitlab_api_key

    with DatabaseSession(logger, engine=ctx.obj.engine) as session:

        config = AugurConfig(logger, session)

        augmented_config = config.base_config

        phase_names = get_phase_names_without_import()

        #Add all phases as enabled by default
        for name in phase_names:

            if name not in augmented_config['Task_Routine']:
                augmented_config['Task_Routine'].update({name : 1})

        #print(default_config)
        if redis_conn_string:

            try:
                redis_string_array = redis_conn_string.split("/")
                cache_number = int(redis_string_array[-1])
                digits = len(str(cache_number))

                redis_conn_string = redis_conn_string[:-digits]
            
            except ValueError:
                pass

            augmented_config["Redis"]["connection_string"] = redis_conn_string

        if rabbitmq_conn_string:
            augmented_config["RabbitMQ"]["connection_string"] = rabbitmq_conn_string

        augmented_config["Keys"] = keys

        augmented_config["Facade"]["repo_directory"] = facade_repo_directory

        augmented_config["Logging"]["logs_directory"] = logs_directory or (ROOT_AUGUR_DIRECTORY + "/logs/")

        config.load_config_from_dict(augmented_config)


@cli.command('load')
@click.option('--file', required=True)
@test_connection
@test_db_connection
@with_database
@click.pass_context
def load_config(ctx, file):

    with DatabaseSession(logger, engine=ctx.obj.engine) as session:
        config = AugurConfig(logger, session)

        print("WARNING: This will override your current config")
        response = str(input("Would you like to continue: [y/N]: ")).lower()

        if response not in ("y", "yes"):
            print("Did not recieve yes or y exiting...")
            return

        file_data = config.load_config_file(file)

        config.clear()
        
        config.load_config_from_dict(file_data)
    
@cli.command('add-section')
@click.option('--section-name', required=True)
@click.option('--file', required=True)
@test_connection
@test_db_connection
@with_database
@click.pass_context
def add_section(ctx, section_name, file):

    with DatabaseSession(logger, engine=ctx.obj.engine) as session:
        config = AugurConfig(logger, session)

        if config.is_section_in_config(section_name):

            print(f"Warning there is already a {section_name} section in the config and it will be replaced")
            response = str(input("Would you like to continue: [y/N]: ")).lower()

            if response not in ("y", "yes"):
                print("Did not recieve yes or y exiting...")
                return

        config.remove_section(section_name)
                
        with open(file, 'r') as f:
            section_data = json.load(f)

        config.add_section_from_json(section_name, section_data)


@cli.command('set')
@click.option('--section', required=True)
@click.option('--setting', required=True)
@click.option('--value', required=True)
@test_connection
@test_db_connection
@with_database
@click.pass_context
def config_set(ctx, section, setting, value):

    with DatabaseSession(logger, engine=ctx.obj.engine) as session:
        config = AugurConfig(logger, session)

        config.add_value(section, setting, value)
        print(f"{setting} in {section} section set to {redact_setting_value(section, setting, value)}")

@cli.command('get')
@click.option('--section', required=True)
@click.option('--setting')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def config_get(ctx, section, setting):

    with DatabaseSession(logger, engine=ctx.obj.engine) as session:
        config = AugurConfig(logger, session)

        if setting:
            config_value = config.get_value(section_name=section, setting_name=setting)

            if config_value is not None:
                print(f"======================\n{setting}: {config_value}\n======================")
            else:
                print(f"Error unable to find '{setting}' in the '{section}' section of the config")
                
        else:
            section_data = config.get_section(section_name=section)
            
            if section_data:
                print(f"======================\n{section}\n====")
                section_data_keys = list(section_data.keys())
                for key in section_data_keys:
                    print(f"{key}: {section_data[key]}")

                print("======================")

            else:
                print(f"Error: {section} section not found in config")

@cli.command('get_all_json')
def config_get_all_json():
    data = {}
    try:
        with DatabaseSession(logger) as session:
            sections = session.query(Config.section_name).distinct().all()
            for section in sections:
                data[section[0]] = {}

            for row in session.query(Config).all():
                data[row.section_name][row.setting_name] = row.value
    except Exception:
        pass
    
    print(json.dumps(data, indent=4))

@cli.command('clear')
@test_connection
@test_db_connection
@with_database
@click.pass_context
def clear_config(ctx):

    with DatabaseSession(logger, ctx.obj.engine) as session:
        config = AugurConfig(logger, session)

        if not config.empty():

            print("Warning this delete the current config")
            response = str(input("Would you like to continue: [y/N]: ")).lower()

            if response not in ("y", "yes"):
                print("Did not recieve yes or y exiting...")
                return

        config.clear()

        print("Config cleared")
