#SPDX-License-Identifier: MIT
import json
#import gunicorn.app.base
import numpy as np
from celery import group
from celery.result import AsyncResult
from celery.result import allow_join_result

from typing import List
from datetime import datetime
import json
import subprocess

from augur.tasks.util.metadata_exception import MetadataException


def create_grouped_task_load(*args,processes=8,dataList=[],task=None):
    
    if not dataList or not task:
        raise AssertionError
    
    print(f"Splitting {len(dataList)} items")
    #numpyData = np.array(list(dataList))
    listsSplitForProcesses = np.array_split(list(dataList), processes)
    print("Done splitting items.")

    #print("args")
    #print(args)
    task_list = [task.si(data.tolist(), *args) for data in listsSplitForProcesses]

    jobs = group(task_list)

    return jobs



def wait_child_tasks(ids_list):
    for task_id in ids_list:
        prereq = AsyncResult(str(task_id))
        with allow_join_result():
            prereq.wait()


def _make_hashable(obj):
    """Recursively convert unhashable objects (dict, list) to hashable tuples."""
    if isinstance(obj, (tuple, list)):
        return tuple(_make_hashable(e) for e in obj)
    if isinstance(obj, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in obj.items()))
    return obj

def remove_duplicate_dicts(data: List[dict]) -> List[dict]:
    """Remove duplicate dicts from a list

    Args:
        data: list of dicts that is being modified

    Returns:
        list of unique dicts

    Note:
        The dicts must be perfectly the same meaning the field and data must be exactly the same to be removed
        This handles nested unhashable types like dictionaries and lists.
    """
    seen = set()
    unique_data = []
    for d in data:
        h = _make_hashable(d)
        if h not in seen:
            seen.add(h)
            unique_data.append(d)
    return unique_data

def remove_duplicates_by_uniques(data, uniques):

    unique_values = {}

    unique_data = []

    #Deal with null data being passed. 
    if not uniques:
        return data

    for x in data:

        # creates a key out of the uniques as a tuple to avoid string collision issues
        # and handles nested unhashable codes by converting them to hashable tuples
        key = tuple(_make_hashable(x[unique]) for unique in uniques)

        # if a KeyError does not occur then a dict with those values has already been processed
        # if a KeyError occurs a dict with those values has not been found yet
        try:
            unique_values[key]
            continue
        except KeyError:
            unique_values[key] = 1
            unique_data.append(x)

    return unique_data




def remove_duplicate_naturals(data, natural_keys):
    #Removes duplicate records with the same natural values only.

    new_data = []
    unique_values = []

    for record in data:

        #Get the unique part of the data.
        unique_part = {}
        for key in natural_keys:
            unique_part[key] = record[key]
        
        if unique_part not in unique_values:
            unique_values.append(unique_part)
            new_data.append(record)
    
    #print(new_data)
    return new_data

#4th root of 10,000 is 10
#ten days for a 10,000 weight repo to reach zero.
def date_weight_factor(days_since_last_collection,domain_shift=0):
    return (days_since_last_collection - domain_shift) ** 4

def calculate_date_weight_from_timestamps(added,last_collection,domain_start_days=30):
    #Get the time since last collection as well as when the repo was added.
    if last_collection is None:
        delta = datetime.now() - added
        return date_weight_factor(delta.days)
    else:
        delta = datetime.now() - last_collection
        
        factor = date_weight_factor(delta.days,domain_shift=domain_start_days)

        #If the repo is older than thirty days, start to decrease its weight.
        if delta.days >= domain_start_days:
            return factor
        else:
            #Else increase its weight
            return -1 * factor

def parse_json_from_subprocess_call(logger, subprocess_arr, cwd=None):
    logger.info(f"running subprocess {subprocess_arr[0]}")
    if cwd:
        p = subprocess.run(subprocess_arr,cwd=cwd,capture_output=True, text=True, timeout=None)
    else:
        p = subprocess.run(subprocess_arr,capture_output=True, text=True, timeout=None)
    
    logger.info('subprocess completed... ')

    output = p.stdout

    try:
        if output and output.strip():
            required_output = json.loads(output)
        else:
            required_output = {}
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Could not parse required output! \n output: {output} \n Error: {e}")
        raise MetadataException(e, f"output : {output}")
    
    return required_output


# def create_server(app, worker=None):
#     """ Consists of AUGWOP endpoints for the broker to communicate to this worker
#     Can post a new task to be added to the workers queue
#     Can retrieve current status of the worker
#     Can retrieve the workers config object
#     """

#     server.app.route("/AUGWOP/task", methods=['POST', 'GET'])
#     def augwop_task():
#         """ AUGWOP endpoint that gets hit to add a task to the workers queue or is used to get the heartbeat/status of worker
#         """
#         if request.method == 'POST': #will post a task to be added to the queue
#             app.worker.logger.info("Sending to work on task: {}".format(str(request.json)))
#             app.worker.task = request.json
#             return Response(response=request.json,
#                         status=200,
#                         mimetype="application/json")
#         if request.method == 'GET': #will retrieve the current tasks/status of the worker
#             return jsonify({
#                 "status": "ALIVE",
#                 "results_counter": app.worker.results_counter,
#                 "task": app.worker.task,
#             })
#         return Response(response=request.json,
#                         status=200,
#                         mimetype="application/json")

#     server.app.route("/AUGWOP/heartbeat", methods=['GET'])
#     def heartbeat():
#         if request.method == 'GET':
#             return jsonify({
#                 "status": "alive"
#             })

#     server.app.route("/AUGWOP/config")
#     def augwop_config():
#         """ Retrieve worker's config
#         """
#         return app.worker.config

# class WorkerGunicornApplication(gunicorn.app.base.BaseApplication):

#     def __init__(self, app):
#         self.options = {
#             'bind': '%s:%s' % (app.worker.config["host"], app.worker.config["port"]),
#             'workers': 1,
#             'errorlog': app.worker.config['server_logfile'],
#             'accesslog': app.worker.config['server_logfile'],
#             'loglevel': app.worker.config['log_level'],
#             'capture_output': app.worker.config['capture_output']
#         }

#         self.application = app
#         super().__init__()

#     def load_config(self):
#         config = {key: value for key, value in self.options.items()
#                   if key in self.cfg.settings and value is not None}
#         for key, value in config.items():
#             self.cfg.set(key.lower(), value)

#     def load(self):
#         return self.application
