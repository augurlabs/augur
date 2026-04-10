import os
from pathlib import Path


class ConfigPaths:
    """Centralized config path utilities."""

    @classmethod
    def config_dir(cls) -> Path:
        """Get config directory from CONFIG_DATADIR env var, or current directory."""
        return Path(os.getenv("CONFIG_DATADIR", "."))

    @classmethod
    def _read_json(cls, file_name: str) -> dict:
        """Helper to read and parse a JSON configuration file."""
        import json
        file_path = cls.config_dir() / file_name
        with open(file_path, 'r') as f:
            return json.load(f)

    @classmethod
    def _read_yaml(cls, file_name: str) -> dict:
        """Helper to read and parse a YAML configuration file."""
        import yaml
        file_path = cls.config_dir() / file_name
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    @classmethod
    def db_config(cls) -> Path:
        """Get path to db.config.json."""
        return cls.config_dir() / "db.config.json"

    @classmethod
    def read_db_config(cls) -> dict:
        """Read and parse db.config.json."""
        return cls._read_json("db.config.json")

    @classmethod
    def augur_config(cls) -> Path:
        """Get path to augur.json."""
        return cls.config_dir() / "augur.json"

    @classmethod
    def read_augur_config(cls) -> dict:
        """Read and parse augur.json."""
        return cls._read_json("augur.json")

    @classmethod
    def view_config(cls) -> Path:
        """Get path to config.yml."""
        return cls.config_dir() / "config.yml"

    @classmethod
    def read_view_config(cls) -> dict:
        """Read and parse config.yml."""
        return cls._read_yaml("config.yml")


import sqlalchemy as s
from sqlalchemy import and_, update
import json
import copy
from typing import List, Any, Optional
from augur.application.db.models import Config 
from augur.application.db.util import execute_session_query, convert_type_of_value
import logging

def get_development_flag_from_config():
    
    from logging import getLogger
    from augur.application.db.session import DatabaseSession

    logger = getLogger(__name__)
    with DatabaseSession(logger) as session:

        config = AugurConfig(logger, session)

        section = "Augur"
        setting = "developer"

        flag = config.get_value(section, setting)

    return flag

def get_development_flag():
    return os.getenv("AUGUR_DEV") or get_development_flag_from_config() or False

def redact_setting_value(section_name, setting_name, value):
    value_redacted = value if section_name != "Keys" else "REDACTED"
    return value_redacted

default_config = {
            "Augur": {
                "developer": 0,
                "version": 1
            },
            "Keys": {
                "github": "<gh_api_key>",
                "gitlab": "<gl_api_key>"
            },
            "Facade": {
                "check_updates": 1,
                "create_xlsx_summary_files": 1,
                "delete_marked_repos": 0,
                "fix_affiliations": 1,
                "force_invalidate_caches": 1,
                "limited_run": 0,
                "multithreaded": 1,
                "nuke_stored_affiliations": 0,
                "pull_repos": 1,
                "rebuild_caches": 1,
                "run_analysis": 1,
                "run_facade_contributors": 1,
                "facade_contributor_full_recollect": 0,
                "commit_messages": 1,
            },
            "Server": {
                "cache_expire": "3600",
                "host": "0.0.0.0",
                "port": 5000,
                "workers": 6,
                "timeout": 6000,
                "ssl": False,
                "ssl_cert_file": None, 
                "ssl_key_file": None 
            },
            "Logging": {
                "logs_directory": "",
                "log_level": "INFO",
            },
            "Celery": {
                "core_worker_count": 5,
                "secondary_worker_count": 5,
                "facade_worker_count": 5,
                "refresh_materialized_views_interval_in_days": 1
            },
            "Redis": {
                "cache_group": 0, 
                "connection_string": "redis://127.0.0.1:6379/"
            },
            "RabbitMQ": {
                "connection_string": "amqp://augur:password123@localhost:5672/augur_vhost"
            },
            "Tasks": {
                "collection_interval": 30,
                "core_collection_interval_days": 15,
                "secondary_collection_interval_days": 10,
                "facade_collection_interval_days": 10,
                "ml_collection_interval_days": 40,
                "default_batch_size": 1000,
                "github_event_batch_size": 500,
                "github_message_batch_size": 20
            },
            "Message_Insights": {
                    "insight_days": 30,
                    "models_dir": "message_models"
            },
            "Clustering_Task": {
                "max_df": 0.9,
                "max_features": 1000,
                "min_df": 0.1,
                "num_clusters": 4
            },
            "Insight_Task": {
                # TODO: How to store metrics in database config?
                "confidence_interval": 95,
                "contamination": 0.1,
                "switch": 1,
                "workers": 1,
                "training_days": 1000,
                "anomaly_days": 14
            },
            "Task_Routine": {
                "prelim_phase": 1,
                "primary_repo_collect_phase": 1,
                "secondary_repo_collect_phase": 1,
                "facade_phase": 1,
                "machine_learning_phase": 0
            },
            "Frontend": {
                "pagination_offset": 25
            }
        }


class AugurConfig():

    from augur.application.db.session import DatabaseSession

    session: DatabaseSession

    @property
    def base_config(self):
        """Return the "base" config - either the default config or a default config with user modifications on top
        This is used as a base upon which the Augur CLI injects values, such as API keys, connection strings, 
        and other values passed in via environment variables.
        This config is then modified and passed into `load_config_from_dict`.
        """
        read_only_sources = self._fetch_config_stores(lambda source: not source.writable)
        config = {}
        for config_source in read_only_sources:
            config.update(config_source.retrieve_dict())

        return config

    def __init__(self, logger, session: DatabaseSession, config_sources: list = None):
        """Create a new AugurConfig class

        Args:
            logger (_type_): The logger instance to use for logging
            session (DatabaseSession): a connection to the database for configuring the database source.
            config_sources (list, optional): An alternative way to pass in config sources. Used for unit testing only.
                Specifying a value here enables you to supply `None` to the `session` argument, since it will be unused. Defaults to None.
        """

        self.session = session
        self.logger = logger

        self.accepted_types = ["str", "bool", "int", "float", "NoneType"]

        if not config_sources:
            # list items in order of precedence. lowest precedence (i.e. fallback) values first 
            config_sources = [
                JsonConfig(default_config, logger)
            ]

            config_dir = Path(os.getenv("CONFIG_DATADIR", "./"))
            config_path = config_dir.joinpath("augur.json")
            if config_path.exists():
                config_sources.append(JsonConfig(json.loads(config_path.read_text(encoding="UTF-8")), logger))
            
            config_sources.append( DatabaseConfig(session, logger) )

        self.config_sources = config_sources
        

    def _get_writable_source(self) -> 'ConfigStore':
        """Returns the highest precedence source that can be written to.
        Intended to be used for operations that require changing the config updates.

        Raises:
            NotWriteableException: If no sources are available for writing, this exception is raised to tell the caller they must proceed in a read only manner

        Returns:
            ConfigStore: An instance of ConfigStore representing the config storage location that can be written to.
        """
        writeable_sources = self._fetch_config_stores(lambda source: source.writable)
        if len(writeable_sources) < 1:
            raise NotWriteableException
        
        return writeable_sources[-1]

    def _fetch_config_stores(self, filter_func: None):
        """Fetch the stack of config stores filtered by the provided function

        Args:
            filter_func (func): a function or lambda accepting a ConfigSource as its only argument and returning a boolean indicating if it should be kept in or left out by the filter
        """
        if filter_func is None:
            return self.config_sources
        return list(filter(filter_func, self.config_sources))
            
    def get_section(self, section_name) -> dict:
        """Get a section of data from the config.

        Args:
            section_name: The name of the section being retrieved

        Returns:
            The section data as a dict
        """
        if not self.is_section_in_config(section_name):
            return {}
        
        config_dict = self.load_config()
        return config_dict[section_name]

    def get_value(self, section_name: str, setting_name: str) -> Optional[Any]:
        """Get the value of a setting from the config.

        Args:
            section_name: The name of the section that the setting belongs to 
            setting_name: The name of the setting

        Returns:
            The value from config if found, and None otherwise
        """

        # TODO temporary until all uses of the lowercase version are gone
        if section_name == "frontend":
            section_name = "Frontend"

        for source in reversed(self.config_sources):
            val = source.get_value(section_name, setting_name)
            if val is not None:
                return val
        return None

    def load_config(self) -> dict:
        """Get full config as a dictionary.
        
        Returns:
            The config from all sources
        """

        def merge(a: dict, b: dict):
            """Do a deep merge of two python dictionaries (standard library update and merge dont do this)
            This is what allows updated values in higher priority config sources to take precedence.

            This function is lightly modified from https://stackoverflow.com/a/7205107

            Args:
                a (dict): The dict to merge into. Will be mutated
                b (dict): The incoming dict to merge in. Data in this dict will take precedence when there is a conflict

            Returns:
                dict: The dict passed in via parameter a, now modified with the new values
            """
            for key in b:
                if key in a:
                    if isinstance(a[key], dict) and isinstance(b[key], dict):
                        merge(a[key], b[key])
                    elif a[key] != b[key]:
                        a[key] = b[key]
                else:
                    a[key] = b[key]
            return a

        config = {}

        for config_source in self.config_sources:
            merge(config, config_source.retrieve_dict())
        
        return config


    def empty(self) -> bool:
        """Determine if a config is empty.
        
        Returns:
            True if the config is empty, and False if it is not
        """
        return all(map(lambda s: s.empty), self.config_sources)

    def is_section_in_config(self, section_name: str) -> bool:
        """Determine if a section is in the config.
        
        Args:
            section_name: section to search for in config

        Returns:
            True if section is in the config, and False if it is not
        """
        return any(map(lambda s: s.has_section(section_name), self.config_sources))
       
    def add_value(self, section_name, setting_name, value):
        """Adds or updates a config value.
        
        Args:
            section_name: The name of the section being added
            json_data: The data being added
        """
        try:
            writeable_config = self._get_writable_source()
            writeable_config.add_value(section_name, setting_name, value, ignore_existing=True)
        except NotWriteableException:
            return
        

    def add_section_from_json(self, section_name: str, json_data: dict) -> None:
        """Add a section from a dict.
        
        Args:
            section_name: The name of the section being added
            json_data: The data being added
        """
        try:
            writeable_config = self._get_writable_source()
            writeable_config.create_section(section_name, json_data, ignore_existing=True)
        except NotWriteableException:
            return


    def load_config_file(self, file_path: str) -> dict:
        """Add a section from a dict.
        
        Args:
            file_path: Path to json file being loaded

        Returns:
            data in the json file
        """
        with open(file_path, 'r') as f:
            file_data = json.load(f)

            return file_data

    def load_config_from_dict(self, dict_data: dict) -> None:
        """Create config from a dict.
        
        Args:
            dict_data: The data being loaded into the config
        """
        section_names = list(dict_data.keys())

        for section_name in section_names:
            
            value = dict_data[section_name]
            #print(f"\n{value}")
            # check for "sections" that are actually just a key value pair 
            # and not a key that has a value of type dict
            if isinstance(value, dict) is True:
                self.add_section_from_json(section_name=section_name, json_data=value)

            else:
                self.logger.error(f"Error! {section_name}: {value} will not be added because a section must have a dict as its values (all of the top level keys in the config must have a value of type dict")

    def clear(self) -> None:
        """Remove all values from the config."""
        # note, with the hierarchical nature of the new config setup, this is a pretty useless method
        # this is because the hierarhical store is designed to always be able to fall back on preconfigured defaults.
        # Clearing will only reset any changes that the writable source provided to the config.
        try:
            writeable_config = self._get_writable_source()
            writeable_config.clear()
        except NotWriteableException:
            return

    def remove_section(self, section_name: str) -> None:
        """Remove a section from the config.
        
        Args:
            section_name: The name of the section being deleted
        """
        # note, with the hierarchical nature of the new config setup, this is a pretty useless method
        # this is because the hierarhical store is designed to always be able to fall back on preconfigured defaults.
        # Removing a section will only reset any changes that the writable source contributed in that section.
        try:
            writeable_config = self._get_writable_source()
            writeable_config.remove_section(section_name)
        except NotWriteableException:
            return

class NotWriteableException(Exception):
    """Custom Augur exception class to be used when trying to modify a config that is not writeable
    """
    pass

class ConfigStore():
    """A class representing the interface for various possible config backends.
    This should not contain implementations unless they apply to all possible config backends
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @property
    def writable(self):
        """Determine if this config store is writable.
        
        Returns:
            True if the config store is writable, and False if it is not
        """
        raise NotImplementedError()
    
    @property
    def empty(self):
        """Determine if this config store is empty.
        
        Returns:
            True if the config store is empty, and False if it is not
        """
        raise NotImplementedError()

    def load_dict(self, data: dict, ignore_existing=False):
        """Load config into this store from dict values

        Args:
            data (dict): the data to load
            ignore_existing (bool, optional): whether to ignore any values or sections that exist already. Defaults to False.
        
        Raises:
            NotWriteableException: When attempting to modify a config that is not writeable.
        """
        raise NotImplementedError()

    def retrieve_dict(self):
        """Get the full config from this store as a dictionary.
        
        Returns:
            dict: The dict representation of the config from this config store
        """
        raise NotImplementedError()

    def clear(self):
        """Remove all values from this config store.
    
        Raises:
            NotWriteableException: When attempting to modify a config that is not writeable.
        """
        raise NotImplementedError()

    def remove_section(self, section_name: str) -> None:
        """Remove a section from the config.
        
        Args:
            section_name: The name of the section being deleted
        
        Raises:
            NotWriteableException: When attempting to modify a config that is not writeable.
        """
        raise NotImplementedError()

    def has_section(self, section_name: str) -> bool:
        """Determine if a section exists in this config.
        
        Args:
            section_name: The name of the section to check for

        Returns:
            True if the config store contains this section, and False if it is not
        """
        raise NotImplementedError()

    def create_section(self, section_name: str, values: Optional[dict] = None, ignore_existing=False) -> None:
        """Create a section in this config.
        
        Args:
            section_name: The name of the section being deleted
            values (Optional[dict], optional): Optional keys and values to populate in this section. Defaults to None.
            ignore_existing (bool, optional): whether to ignore and overwrite an existing section or value with this name. Defaults to False.

        Raises:
            NotWriteableException: When attempting to modify a config that is not writeable.
        """
        raise NotImplementedError()

    def get_section(self, section_name: str) -> dict:
        """Return a section from this config store.
        
        Args:
            section_name: The name of the section to check for

        Returns:
            The section data as a dict
        """
        raise NotImplementedError()

    def remove_value(self, section_name: str, value_key: str) -> None:
        """Remove a value from the config.
        
        Args:
            section_name: The name of the section the value is in
            value_name: The key of the value being deleted
        
        Raises:
            NotWriteableException: When attempting to modify a config that is not writeable.
        """
        raise NotImplementedError()

    def has_value(self, section_name: str, value_key: str) -> bool:
        """Determine if a section exists in this config.
        
        Args:
            section_name: The name of the section the value is in
            value_key: The key at which to look for a value

        Returns:
            True if the config store contains this value, and False if not
        """
        raise NotImplementedError()

    def add_value(self, section_name: str, value_key: str, value, ignore_existing=False) -> None:
        """Create a section in this config.
        
        Args:
            section_name: The name of the section being deleted
            value_key (str): The key at which to store this value
            value (any): the value to store at this key
            ignore_existing (bool, optional): whether to ignore and overwrite an existing value if encountered. Defaults to False.

        Raises:
            NotWriteableException: When attempting to modify a config that is not writeable.
        """
        raise NotImplementedError()

    def get_value(self, section_name: str, value_key: str):
        """Return a single value from this config store.
        
        Args:
            section_name: The name of the section to check for
            value_key (str): The key at which to look for a value

        Returns:
            The section data as a dict
        """
        raise NotImplementedError()

        


class JsonConfig(ConfigStore):
    """A ConfigStore for handling JSON data
    """

    def __init__(self, json_data, logger: logging.Logger):
        super().__init__(logger)
        if not self.writable:
            json_data = copy.deepcopy(json_data)
        self.json_data = json_data

    @property
    def writable(self):
        return False
    
    @property
    def empty(self):
        return self.json_data == {}

    def load_dict(self, data: dict, ignore_existing=False):
        if not self.writable:
            raise NotWriteableException()

        if ignore_existing:
            self.json_data = data
        else: 
            self.json_data.update(data)

    def retrieve_dict(self):
        # if this dict isnt supposed to be mutable, we need to make a copy
        # this prevents being able to change data in this object by reference
        
        if not self.writable:
            return copy.deepcopy(self.json_data)
        return self.json_data

    def clear(self):
        if not self.writable:
            raise NotWriteableException()
        
        self.json_data = {}

    def remove_section(self, section_name: str) -> None:
        if not self.writable:
            raise NotWriteableException()

        del self.json_data[section_name]


    def has_section(self, section_name: str) -> bool:
        return section_name in self.json_data

    def create_section(self, section_name: str, values: Optional[dict] = None, ignore_existing=False) -> None:
        if not self.writable:
            raise NotWriteableException()

        if values is None:
            values = {}

        if ignore_existing:
            self.json_data[section_name] = values
        else:
            self.json_data[section_name].update(values)

    def get_section(self, section_name: str) -> dict:
        if self.has_section(section_name):
            return self.json_data[section_name]

    def remove_value(self, section_name: str, value_key: str) -> None:
        if not self.writable:
            raise NotWriteableException()

        if self.has_section(section_name):
            del self.json_data[section_name][value_key]
    

    def has_value(self, section_name: str, value_key: str) -> bool:
        return self.has_section(section_name) and self.json_data[section_name].get(value_key, None) is not None

    def add_value(self, section_name: str, value_key: str, value, ignore_existing=False) -> None:
        if not self.writable:
            raise NotWriteableException()

        if not self.has_section(section_name):
            self.create_section(section_name, {[value_key]: value}, ignore_existing=ignore_existing)
            return
        
        if ignore_existing:
            self.json_data[section_name][value_key] = value
        else:
            self.json_data[section_name][value_key].update(value)


    def get_value(self, section_name: str, value_key: str):
        if not self.has_section(section_name):
            return None
        
        return self.json_data[section_name].get(value_key, None)

    def __repr__(self):
        return f"JsonSource({self.json_data})"



class DatabaseConfig(ConfigStore):
    """A ConfigStore for handling JSON data
    """
    from augur.application.db.session import DatabaseSession

    def __init__(self, session: DatabaseSession, logger: logging.Logger):
        super().__init__(logger)
        self.session = session

    @property
    def writable(self):
        return True
    
    @property
    def empty(self):
        query = self.session.query(Config)
        return execute_session_query(query, 'first') is None

    @staticmethod
    def _dict_to_config_table(json_data:dict):
        """Convert an augur settings dict into a mapping from table columns to values for insertion in bulk

        Args:
            json_data (dict): The settings to convert, in the same format as the default_dict at the top of this file
        """
        
        config_values = []
        for section_name, settings in json_data.items():
            for key, value in settings.items():

                if isinstance(value, dict) is True:
                    # TODO: Uncomment out when insights worker config stuff is resolved
                    # self.logger.error(f"Values cannot be of type dict: {value}")
                    return

                setting = {
                    "section_name": section_name,
                    "setting_name": key,
                    "value": value,
                }

                if "type" not in setting:
                    setting["type"] = setting["value"].__class__.__name__

                if setting["type"] == "NoneType":
                    setting["type"] = None

                config_values.append(setting)

        return config_values
    

    def load_dict(self, data: dict, ignore_existing=False):
        if not self.writable:
            raise NotWriteableException()

        for section, config_values in data.items():
            self.create_section(section, config_values, ignore_existing=ignore_existing)

    def retrieve_dict(self):
        # get all the sections in the config table
        query = self.session.query(Config.section_name).order_by(Config.section_name.asc())
        section_names = execute_session_query(query, 'all')

        config = {}
        # loop through and get the data for each section
        for section_name in section_names:

            section_data = self.get_section(section_name[0])

            # rows with a section of None are on the top level, 
            # so we are adding these values to the top level rather 
            # than creating a section for them
            if section_name[0] is None:
                for key in list(section_data.keys()):
                    config[key] = section_data[key]
                continue

            # add section data to config object
            config[section_name[0]] = section_data

        return config

    def clear(self):
        if not self.writable:
            raise NotWriteableException()
        
        self.session.query(Config).delete()
        self.session.commit()

    def remove_section(self, section_name: str) -> None:
        if not self.writable:
            raise NotWriteableException()

        self.session.query(Config).filter(Config.section_name == section_name).delete()
        self.session.commit()


    def has_section(self, section_name: str) -> bool:
        query = self.session.query(Config).filter(Config.section_name == section_name)
        return execute_session_query(query, 'first') is not None

    def create_section(self, section_name: str, values: Optional[dict] = None, ignore_existing=False) -> None:
        if not self.writable:
            raise NotWriteableException()

        if values is None:
            values = {}

        for key, value in values.items():
            self.add_value(section_name, key, value, ignore_existing=ignore_existing)

    def get_section(self, section_name: str) -> dict:
        query = self.session.query(Config).filter_by(section_name=section_name).order_by(Config.setting_name.asc())
        section_data = execute_session_query(query, 'all')
        
        section_dict = {}
        for setting in section_data:
            setting_dict = setting.__dict__

            setting_dict = convert_type_of_value(setting_dict, self.logger)

            setting_name = setting_dict["setting_name"]
            setting_value = setting_dict["value"]

            section_dict[setting_name] = setting_value

        return section_dict

    def remove_value(self, section_name: str, value_key: str) -> None:
        raise NotImplementedError()

    def has_value(self, section_name: str, value_key: str) -> bool:
        query = self.session.query(Config).filter(and_(Config.section_name == section_name,Config.setting_name == value_key) )
        return execute_session_query(query, 'first') is not None

    def add_value(self, section_name: str, value_key: str, value, ignore_existing=False) -> None:

        converted_settings = self._dict_to_config_table({section_name: { value_key: value}})

        if len(converted_settings) >= 1:
            setting = converted_settings[0]
        
        if not self.has_value(section_name, value_key):
            self.session.insert_data(setting,Config, ["section_name", "setting_name"])
        else:
            if not ignore_existing:
                self.logger.error(f"Could not insert config value '{redact_setting_value(section_name, value_key, value)}' into section '{section_name}' for key '{value_key}' database because a value already exists there and caller did not specify override")
                return
            #If setting exists. use raw update to not increase autoincrement
            update_query = (
                update(Config)
                .where(Config.section_name == setting["section_name"])
                .where(Config.setting_name == setting["setting_name"])
                .values(value=setting["value"])
            )

            self.session.execute(update_query)
            self.session.commit()

    def get_value(self, section_name: str, value_key: str):
        try:
            query = self.session.query(Config).filter(Config.section_name == section_name, Config.setting_name == value_key)
            config_setting = execute_session_query(query, 'one')
        except s.orm.exc.NoResultFound:
            return None

        setting_dict = config_setting.__dict__

        setting_dict = convert_type_of_value(setting_dict, self.logger)

        return setting_dict["value"]
