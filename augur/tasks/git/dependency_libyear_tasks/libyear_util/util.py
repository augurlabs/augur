import dateutil.parser
import os
from augur.tasks.git.dependency_libyear_tasks.libyear_util.pypi_parser import parse_conda, parse_pipfile,parse_pipfile_lock,parse_poetry,parse_poetry_lock,parse_requirement_txt,parse_setup_py
from augur.tasks.git.dependency_libyear_tasks.libyear_util.npm_parser import parse_package_json
from augur.tasks.git.dependency_libyear_tasks.libyear_util.pypi_libyear_util import sort_dependency_requirement,get_pypi_data,get_latest_version,get_release_date
from augur.tasks.git.dependency_libyear_tasks.libyear_util.npm_libyear_utils import get_NPM_data, get_npm_release_date, get_npm_latest_version,get_npm_current_version
import logging
logger=logging.getLogger(__name__)
#Files That would be parsed should be added here
file_list = [
    'Requirement.txt',
    'requirements.txt',
    'setup.py',
    'Pipfile',
    'Pipfile.lock',
    'pyproject.toml',
    'poetry.lock',
    'environment.yml',
    'environment.yaml',
    'environment.yml.lock',
    'environment.yaml.lock',
    'package.json'
]


def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def get_parsed_deps(path, logger):
    import traceback
    dependency_list = []

    for f in file_list:
        deps_file = find(f, path)
        if not deps_file:
            continue

        short_file_name = os.path.split(deps_file)[-1]
        logger.info(f"Found dependency file: {deps_file}")

        try:
            if short_file_name == 'setup.py':
                with open(deps_file, "r", encoding="utf-8", errors="ignore") as text_file:
                    dependency_list.extend(parse_setup_py(text_file))

            else:
                with open(deps_file, "rb") as file_handle:
                    if short_file_name in ['Requirement.txt', 'requirements.txt']:
                        dependency_list.extend(parse_requirement_txt(file_handle))

                    elif short_file_name == 'Pipfile':
                        dependency_list.extend(parse_pipfile(file_handle))

                    elif short_file_name == 'Pipfile.lock':
                        dependency_list.extend(parse_pipfile_lock(file_handle))

                    elif short_file_name == 'pyproject.toml':
                        try:
                            dependency_list.extend(parse_poetry(file_handle, path=path))
                        except Exception as e:
                            logger.warning(f"Failed to parse poetry file {file_handle.name if hasattr(file_handle, 'name') else 'unknown'}: {e}")

                    elif short_file_name == 'poetry.lock':
                        dependency_list.extend(parse_poetry_lock(file_handle))

                    elif short_file_name in ['environment.yml', 'environment.yaml', 'environment.yml.lock', 'environment.yaml.lock']:
                        dependency_list.extend(parse_conda(file_handle))

                    elif short_file_name == 'package.json':
                        try:
                            dependency_list.extend(parse_package_json(file_handle))
                        except KeyError as e:
                            logger.error(f"package.json for repo at path {path} is missing required key: {e}\n Skipping file...")

        except Exception as e:
            logger.warning(f"Failed to parse {deps_file}: {e}")
            logger.debug(traceback.format_exc())
            continue

    return dependency_list

def get_libyear(current_version, current_release_date, latest_version, latest_release_date):

    if not latest_version:
        return -1
    
    if not latest_release_date:
        return -1

    if not current_version or not current_release_date or not isinstance(current_release_date, str):
        return 0

    current_release_date= dateutil.parser.parse(current_release_date)
    latest_release_date = dateutil.parser.parse(latest_release_date)    

    libdays = (latest_release_date - current_release_date).days
    logger.info(libdays)
    libyear = libdays/365
    return libyear


def get_deps_libyear_data(path, logger):
    current_release_date = None
    libyear = None

    dependencies = get_parsed_deps(path,logger)
    if dependencies:
        for dependency in dependencies:

            #NOTE: Add new if for new package parser
            if dependency['package'] == 'PYPI':
                data = get_pypi_data(dependency['name'])
                if not data:
                    logger.warning(f"Skipping dependency {dependency['name']} - could not find package on PYPI.")
                    continue
                    
                try:
                    current_version = sort_dependency_requirement(dependency,data)
                except (KeyError, TypeError) as e:
                    logger.warning(f"Skipping dependency {dependency['name']} - could not resolve current version requirement: {dependency['requirement']}")
                    continue

                if not current_version:
                    logger.warning(f"Skipping dependency {dependency['name']} - current version is null or unspecified.")
                    continue

                try:
                    latest_version = get_latest_version(data)
                except (KeyError, TypeError):
                    logger.warning(f"Skipping dependency {dependency['name']} - could not get latest version from PYPI.")
                    continue
                
                if not latest_version:
                    logger.warning(f"Skipping dependency {dependency['name']} - latest version is null.")
                    continue

                try:
                    latest_release_date = get_release_date(data, latest_version, logger)
                    current_release_date = get_release_date(data, current_version, logger)
                except KeyError:
                    logger.warning(f"Skipping dependency {dependency['name']} - could not find release dates for version {current_version} or {latest_version}.")
                    continue

                if not current_release_date or not latest_release_date:
                    logger.warning(f"Skipping dependency {dependency['name']} - missing release date information.")
                    continue

            elif dependency['package'] == 'NPM':
                data = get_NPM_data(dependency['name'])
                if not data:
                    logger.warning(f"Skipping dependency {dependency['name']} - could not find package on NPM.")
                    continue

                current_version = get_npm_current_version(data, dependency['requirement'])
                if not current_version:
                    logger.warning(f"Skipping dependency {dependency['name']} - could not resolve current version from requirement: {dependency['requirement']}")
                    continue

                try:
                    latest_version = get_npm_latest_version(data)
                except KeyError:
                    logger.warning(f"Skipping dependency {dependency['name']} - could not get latest version from NPM.")
                    latest_version = None

                if not latest_version:
                    continue

                try:
                    latest_release_date = get_npm_release_date(data, latest_version)
                    current_release_date = get_npm_release_date(data, current_version)
                except KeyError:
                    logger.warning(f"Skipping dependency {dependency['name']} - missing release date info on NPM for {current_version}/{latest_version}")
                    continue
            else:
                # Unsupported package manager
                continue

            libyear = get_libyear(current_version, current_release_date, latest_version, latest_release_date)

            if not dependency['requirement']:
                dependency['requirement'] = 'unspecified'    

            dependency['current_version'] = current_version    
            dependency['latest_version'] = latest_version
            dependency['current_release_date'] = current_release_date
            dependency['latest_release_date'] = latest_release_date
            dependency['libyear'] = libyear

        return [d for d in dependencies if 'libyear' in d]