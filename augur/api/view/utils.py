"""
Defines utility functions used by the augur api views
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import render_template, flash, url_for
from .init import init_logging
from .init import *
from augur.application.db.lib import get_value
import urllib.error, math, yaml, urllib3, time, math


init_logging()

from .init import logger

""" ----------------------------------------------------------------
loadSettings:
    This function attempts to load the application settings from the config file
    (defined in init.py). It is assumed that the filename or file path defined
    during initialization is sufficient to locate the config file, and that the
    current process has read access to that file.

    If loading the config file fails, default settings are loaded via
    init_settings() and an attempt is made to write default settings to the
    provided config file.
"""
def loadSettings():
    global settings
    configFilePath = Path(configFile)
    if not configFilePath.is_file():
        init_settings()
        with open(configFile, 'w') as file:
            logger.info(f"Generating default configuration file: {configFile}")
            yaml.dump(settings, file)
            logger.info("Default configuration file successfully generated.")
    else:
        with open(configFilePath) as file:
            settings = yaml.load(file, Loader=yaml.FullLoader)
    
    # # Ensure that the cache directory exists and is valid
    # cachePath = Path(settings["caching"])

    cachePath = Path.cwd() / "augur" / "static" / "cache"

    if not cachePath.is_dir():
        if cachePath.is_file():
            raise Exception(f"Cannot initialize caching: cache path [{cachePath}] is a file")
        else:
            try:
                cachePath.mkdir(parents=True)
                logger.info("cache directory initialized")
            except Exception as err:
                raise Exception(f"Cannot initialize caching: could not create cache directory [{cachePath}]")

    # Use the resolved path for cache directory access
    settings["caching"] = cachePath

""" ----------------------------------------------------------------
"""
def getSetting(key, section = "View"):
    if section == "View":
        if key == "serving":
            return "http://127.0.0.1:5000/api/unstable"
        return settings[key]
    else:
        return get_value(section, key)

loadSettings()

#version_check(settings)

cache_files_requested = []

""" ----------------------------------------------------------------
"""
def cacheFileExists(filename):
    cache_file = Path(filename)
    if cache_file.is_file():
        if(getSetting('cache_expiry') > 0):
            cache_file_age = time.time() - cache_file.stat().st_mtime
            if(cache_file_age > getSetting('cache_expiry')):
                try:
                    cache_file.unlink()
                    logger.info(f"Cache file {filename} removed due to expiry")
                    return False
                except Exception as e:
                    logger.error("Error: cache file age exceeds expiry limit, but an exception occurred while attempting to remove")
                    logger.error(e)
        return True
    else:
        return False

""" ----------------------------------------------------------------
"""
def toCacheFilename(endpoint, append = True):
    return endpoint.replace("/", ".").replace("?", "_").replace("=", "_") + ('.agcache' if append else "")

def toCacheFilepath(endpoint, append = True):
    return getSetting('caching').joinpath(toCacheFilename(endpoint, append))

def toCacheURL(endpoint):
    return getSetting('approot') + str(toCacheFilepath(endpoint))

""" ----------------------------------------------------------------
"""
def download(url, cmanager, filename, image_cache, image_id, repo_id = None):
    image_cache[image_id] = {}
    image_cache[image_id]['filename'] = filename
    filename = toCacheFilepath(filename, False)
    if cacheFileExists(filename):
        image_cache[image_id]['exists'] = True
        return
    try:
        response = cmanager.request('GET', url)
    except Exception as e:
        logger.error("Could not make request: " + str(e))
        raise e
    
    if "json" in response.headers['Content-Type']:
        logger.warn(f"repo {repo_id}: unexpected json response in image request")
        logger.warn(f"  response: {response.data.decode('utf-8')}")
        image_cache[image_id]['exists'] = False
        return
    if response and response.status == 200:
        image_cache[image_id]['exists'] = True
        try:
            with open(filename, 'wb') as f:
                logger.info("Writing image: " + str(filename))
                f.write(response.data)
        except Exception as err:
            logger.error("An exception occurred writing a cache file to disk")
            logger.error(err)


""" ----------------------------------------------------------------
renderRepos:
    This function renders a list of repos using a given view, while passing query
    data along. This function also processes pagination automatically for the
    range of data provided. If a query is provided and filtering is enabled, the
    data will be filtered using the 'repo_name', 'repo_group_id' or 'rg_name'.
@PARAM:     view: String
        A string representing the template to use for displaying the repos.
@PARAM:     query: String
        The query argument from the previous page.
@PARAM:     data: Dictionary
        The repo data to display on the page
@PARAM:     sorting: String = None
        The key in the data to sort by
@PARAM:     rev: Boolean = False
        Determines if the sorted data should be displayed in descending order
@PARAM:     page: String = None
        The current page to use within pagination
@PARAM:     filter: Boolean = False
        Filter data using query
@PARAM:     pageSource: String = "repos/views/table"
        The base url to use for the page links
"""
def renderRepos(view, query, data, sorting = None, rev = False, page = None, filter = False, pageSource = "repo_table_view", sortBasis = None):
    pagination_offset = getSetting('pagination_offset')
    
    """ ----------
        If the data does not exist, we cannot construct the table to display on
        site. Rendering the table module without data displays an error message
    """
    if(data is None):
        return render_template('index.j2', body="repos-" + view, title="Repos")

    # If a query exists and filtering is set to true, attempt to filter the data
    if((query is not None) and filter):
        results = []
        for repo in data:
            if (query in repo["repo_name"]) or (query == str(repo["repo_group_id"])) or (query in repo["rg_name"]):
                results.append(repo)
        data = results

    # Determine the maximum number of pages which can be displayed from the data
    pages = math.ceil(len(data) / pagination_offset)

    if page is not None:
        page = int(page)
    else:
        page = 1

    """ ----------
        Caller requested sorting of the data. The data is a list of dictionaries
        with numerous sortable elements, and the "sorting" parameter is assumed
        to be the key of the desired element in the dictionary by which to sort.

        We need the "or 0" here to ensure the comparison is valid for rows which
        do not have data for the requested column (we're making the assumption
        that the data type is comparable to integer 0).
    """
    if sorting is not None:
        try:
            data = sorted(data, key = lambda i: i[sorting] or 0, reverse = rev)
        except Exception as e:
            flash("An error occurred during sorting")
            logger.error(str(e))

    """ ----------
        Here we extract a subset of the data for display on the site. First we
        calculate the start index within the data of our current "page" (x),
        then we index to that position plus the pagination offset (or page size)
        defined above. The result is a list which contains *at most* a number of
        entries equal to the pagination offset
    """
    x = pagination_offset * (page - 1)
    data = data[x: x + pagination_offset]

    return render_module("repos-" + view, title="Repos", repos=data, query_key=query, activePage=page, pages=pages, offset=pagination_offset, PS=pageSource, reverse = rev, sorting = sorting)

""" ----------------------------------------------------------------
    Renders a simple page with the given message information, and optional page
    title and redirect
"""
def render_message(messageTitle, messageBody = None, title = None, redirect = None, pause = None, **kwargs):
    return render_module("notice", messageTitle=messageTitle, messageBody=messageBody, title=title, redirect=redirect, pause=pause, **kwargs)

""" ----------------------------------------------------------------
"""
def render_module(module, **args):
    args.setdefault("body", module)
    return render_template('index.j2', **args)

""" ----------------------------------------------------------------
"""
