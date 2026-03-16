#SPDX-License-Identifier: MIT
"""Creates a WSGI server that serves the Augur REST API."""

import glob
import sys
import inspect
import json
import os
import base64
import importlib
import graphene

from typing import List, Any

from pathlib import Path

from flask import Flask, request, Response, redirect, jsonify
from flask_cors import CORS
import pandas as pd
from beaker.util import parse_cache_config_options
from beaker.cache import CacheManager, Cache
from sqlalchemy.pool import StaticPool
from flask_graphql import GraphQLView
from graphene_sqlalchemy import SQLAlchemyObjectType


from augur.application.logs import AugurLogger
from augur.application.db.session import DatabaseSession
from augur.application.config import AugurConfig
from augur.application.db.engine import get_database_string, create_database_engine
from augur.application.db.models import Repo, Issue, PullRequest, Message, PullRequestReview, Commit, IssueAssignee, PullRequestAssignee, PullRequestCommit, PullRequestFile, Contributor, IssueLabel, PullRequestLabel, ContributorsAlias, Release, ClientApplication

from metadata import __version__ as augur_code_version



# from augur.api.routes import AUGUR_API_VERSION
AUGUR_API_VERSION = "api/unstable"

show_metadata = False


def get_file_id(path: str) -> str:
    """Gets the file id of a given path.

    Args:
        path: file path
    
    Examples: 
        If the path /augur/best_routes.py is given it will return "best_routes"

    Returns:
        the filename as a string
    """
    return os.path.splitext(os.path.basename(path))[0]


def create_metrics() -> None:
    """Starts process of adding all the functions from the metrics folder to the flask app as routes."""
    # get a list of the metrics files
    metric_files = get_metric_files()

    # import the metric modules and add them to the flask app using add_metrics
    for file in metric_files:
        importlib.import_module(f"augur.api.metrics.{file}")
        add_metrics(f"augur.api.metrics.{file}")


def add_metrics(module_name: str) -> None:
    """Determine type of metric and call function to add them to the flask app.
    
    This function takes modules that contains metrics, 
    and adds them to the flask app via the add_standard_metric 
    or add_toss_metric methods.

    Note: 
        The attribute is_metric and obj.metadata['type'] 
        are set in file augur/api/routes/util.py in the function 
        register_metric(). This function is a decorator and is 
        how a function is defined as a metric.

    Args:
        module_name: path to the module
    """

    # gets all the members in the module and loops through them
    for _, obj in inspect.getmembers(sys.modules[module_name]):

        # cheks if the object is a function
        if inspect.isfunction(obj) is True:

            # checks if the function has the attribute is_metric. 
            # If it does then it is a metric function and needs to be added to the flask app
            if hasattr(obj, 'is_metric') is True:

                # determines the type of metric and calls the correct method to add it to the flask app
                if obj.metadata['type'] == "standard":
                    add_standard_metric(obj, obj.metadata['endpoint'])
                if obj.metadata['type'] == "toss":
                    add_toss_metric(obj, obj.metadata['endpoint'])



def get_metric_files() -> List[str]:
    """Get list of all the metrics files in the augur/api/metrics directory,

    Returns:
        list of file names
    """
    metric_files = []

    for filename in glob.iglob("augur/api/metrics/**"):
        file_id = get_file_id(filename)
        
        # this filters out files like __init__ and __pycache__. And makes sure it only get py files
        if not file_id.startswith('__') and filename.endswith('.py'):
            metric_files.append(file_id)

    return metric_files
    
# NOTE: Paramater on=None removed, since it is not used in the function Aug 18, 2022 - Andrew Brain
def route_transform(func: Any, args: Any=None, kwargs: dict=None, repo_url_base: str=None, orient: str ='records',
    group_by: str=None, aggregate: str='sum', resample=None, date_col: str='date') -> str:
    """Call a metric function and apply data transformations.

    Note:
        This function takes a function and it arguments, calls the function, then converts it to json if possible.
        It also does some manipulation of the data if paramaters like group_by, aggregate, and respample are set

    Args:
        func: function that is called
        args:
        kwargs:
        repo_url_base:
        orient: 
        group_byf
        on
        aggregate:
        resample:
        date_col:

    Returns:
        The result of calling the function and applying the data transformations
    """
    # this defines the way a pandas dataframe is converted to json
    if orient is None:
        orient = 'records'

    result = ''

    if not show_metadata:

        if args is None:
            args = ()

        if kwargs is None:
            kwargs = {}

        if repo_url_base:
            kwargs['repo_url'] = str(base64.b64decode(repo_url_base).decode())

        # calls the function that was passed to get the data
        data = func(*args, **kwargs)
        
        # most metrics return a pandas dataframe, which has the attribute to_json
        # so basically this is checking if it is a pandas dataframe
        if hasattr(data, 'to_json'):

            # if group_by is defined it groups by the group_by value 
            # and uses the aggregate to determine the operation performed
            if group_by is not None:
                data = data.group_by(group_by).aggregate(aggregate)

            # This code block is resampling the pandas dataframe, here is the documentation for it
            # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
            if resample is not None:
                data['idx'] = pd.to_datetime(data[date_col])
                data = data.set_index('idx')
                data = data.resample(resample).aggregate(aggregate)
                data['date'] = data.index
            
            # converts pandas dataframe to json
            result = data.to_json(orient=orient, date_format='iso', date_unit='ms')
        else:
            # trys to convert dict to json
            try:
                
                result = json.dumps(data)
            except:
                result = data
    else:
        result = json.dumps(func.metadata)

    # returns the result of the function
    return result

def flaskify(function: Any) -> Any:
    """Simplifies API endpoints that just accept owner and repo, transforms them and spits them out.
    """
    if cache_manager:
        def cache_generated_function(*args, **kwargs):
            def heavy_lifting():
                return route_transform(function, args, kwargs, **request.args.to_dict())
            body = server_cache.get(key=str(request.url), createfunc=heavy_lifting)
            return Response(response=body,
                            status=200,
                            mimetype="application/json")
        cache_generated_function.__name__ = function.__name__
        logger.info(cache_generated_function.__name__)
        return cache_generated_function

    def generated_function(*args, **kwargs):
        kwargs.update(request.args.to_dict())
        return Response(response=route_transform(function, args, kwargs, **request.args.to_dict()),
                        status=200,
                        mimetype="application/json")
    generated_function.__name__ = function.__name__
    return generated_function

def routify(func: Any, endpoint_type: str) -> Any:
    """Wraps a metric function allowing it to be mapped to a route,
    get request args and also transforms the metric functions's
    output to json

    :param func: The function to be wrapped
    :param endpoint_type: The type of API endpoint, i.e. 'repo_group' or 'repo'
    """

    # this is that is generated by routify() as passed to the app.route() decorator
    # basically this is the function that is called when an endpoint is pinged
    def endpoint_function(*args, **kwargs) -> Response:

        # sets the kwargs as the query paramaters or the arguments sent in the headers 
        kwargs.update(request.args.to_dict()) 

        # if repo_group_id is not specified, it sets it to 1 which is the default repo group
        if 'repo_group_id' not in kwargs and func.metadata["type"] != "toss":
            kwargs['repo_group_id'] = 1


        # this function call takes the arguments specified when the endpoint is pinged
        # and calls the actual function in the metrics folder and then returns the result
        # NOTE: This also converts the data into json if the function returns a pandas dataframe or dict
        data =  route_transform(func, args, kwargs)


        # this is where the Response is created for all the metrics 
        return Response(response=data,
                        status=200,
                        mimetype="application/json")

    # this sets the name of the endpoint function
    # so that the repo_endpoint, repo_group_endpoint, and deprecated_repo_endpoint
    # don't create endpoint funcitons with the same name
    endpoint_function.__name__ = f"{endpoint_type}_" + func.__name__
    return endpoint_function

    
def add_standard_metric(function: Any, endpoint: str) -> None:
    """Add standard metric routes to the flask app.
    
    Args:
        function: the function that needs to be mapped to the routes
        endpoint: the path that the endpoint should be defined as
    """
    repo_endpoint = f'/{app.augur_api_version}/repos/<repo_id>/{endpoint}'
    repo_group_endpoint = f'/{app.augur_api_version}/repo-groups/<repo_group_id>/{endpoint}'
    deprecated_repo_endpoint = f'/{app.augur_api_version}/repo-groups/<repo_group_id>/repos/<repo_id>/{endpoint}'

    
    # These three lines are defining routes on the flask app, and passing a function.
    # Essetially the strucutre of this is app.route(endpoint)(function).
    # So when this code is executed, it calls routify() which returns a function.
    # The function that is returned is the function that is registerred with the route, and called when the route is pinged
    
    # Simply routify() is called by the route being pinged, and 
    # then routify() returns a function so it is called, 
    # and then that function returns a Response
    app.route(repo_endpoint)(routify(function, 'repo'))
    app.route(repo_group_endpoint)(routify(function, 'repo_group'))
    app.route(deprecated_repo_endpoint )(routify(function, 'deprecated_repo'))

def add_toss_metric(function: Any, endpoint: str) -> None:
    """Add toss metric routes to the flask app.
    
    Args:
        function: the function that needs to be mapped to the routes
        endpoint: the path that the endpoint should be defined as
    """
    repo_endpoint = f'/{app.augur_api_version}/repos/<repo_id>/{endpoint}'
    app.route(repo_endpoint)(routify(function, 'repo'))

def create_cache_manager() -> CacheManager:
    """Create cache for endpoints?
    
    Returns:
        manager of the cache
    """

    cache_config = {
        'cache.type': 'file',
        # Allow setting cache directories via environment variables
        'cache.data_dir': Path(env.setdefault("CACHE_DATADIR", 'runtime/cache/')),
        'cache.lock_dir': Path(env.setdefault("CACHE_LOCKDIR", 'runtime/cache/')),
    }

    if not os.path.exists(cache_config['cache.data_dir']):
        os.makedirs(cache_config['cache.data_dir'])
    if not os.path.exists(cache_config['cache.lock_dir']):
        os.makedirs(cache_config['cache.lock_dir'])
    cache_parsed = parse_cache_config_options(cache_config)
    cache = CacheManager(**cache_parsed)

    return cache

def get_server_cache(cache_manager) -> Cache:
    """Create the server cache, set expiration, and clear
    
    Returns:
        server cache
    """

    expire = int(augur_config.get_value('Server', 'cache_expire'))
    server_cache = cache_manager.get_cache('server', expire=expire)
    server_cache.clear()

    return server_cache


logger = AugurLogger("server").get_logger()
url = get_database_string()
engine = create_database_engine(url, poolclass=StaticPool, connect_args={"application_name": f"augur v{augur_code_version}"})
db_session = DatabaseSession(logger, engine)
augur_config = AugurConfig(logger, db_session)


def get_connection(table, cursor_field_name, connection_class, after, limit, extra_condition=False):

    cursor_field = getattr(table, cursor_field_name)
    query = db_session.query(table).order_by(cursor_field)

    if after:
        cursor_id = after
        query = query.filter(cursor_field > cursor_id)

    if extra_condition:
            field = getattr(table, extra_condition["field_name"])
            query = query.filter(field == extra_condition["value"])

    # get one more item to determine if there is a next page
    items = query.limit(limit + 1).all()
    has_next_page = len(items) > limit
    items = items[:limit]

    
    if items:
        next_cursor = getattr(items[-1], cursor_field_name)
    else:
        next_cursor = None

    return connection_class(items=items, page_info=PageInfoType(next_cursor=next_cursor, has_next_page=has_next_page))




########### Repo Types ##################
class RepoType(SQLAlchemyObjectType):
    class Meta:
        model = Repo
        use_connection = True

    issues = graphene.Field(lambda: IssueConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    prs = graphene.Field(lambda: PullRequestConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    messages = graphene.Field(lambda: MessageConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    releases = graphene.List(lambda: ReleaseType)
    cursor = graphene.String()
        
    def resolve_cursor(self, info):
        return str(self.repo_id)

    def resolve_issues(self, info, after=None, limit=None):
        condition = {"field_name": "repo_id", "value": self.repo_id}
        issue_connection = get_connection(Issue, "issue_id", IssueConnection, after, limit, condition)
        return issue_connection
    
    def resolve_prs(self, info, after=None, limit=None):
        condition = {"field_name": "repo_id", "value": self.repo_id}
        pr_connection = get_connection(PullRequest, "pull_request_id", PullRequestConnection, after, limit, condition)
        return pr_connection
    
    def resolve_messages(self, info, after=None, limit=None):
        condition = {"field_name": "repo_id", "value": self.repo_id}
        messages_connection = get_connection(Message, "msg_id", MessageConnection, after, limit,condition)
        return messages_connection
    
    def resolve_releases(self, info):
        return self.releases
    
class ReleaseType(SQLAlchemyObjectType):

    class Meta:
        model = Release
        use_connection = True


############### Issue Objects #############
class IssueType(SQLAlchemyObjectType):
    class Meta:
        model = Issue
        use_connection = True

    repo = graphene.Field(RepoType)
    messages = graphene.List(lambda: MessageType)
    labels = graphene.List(lambda: IssueLabelType)
    assignees = graphene.List(lambda: IssueAssigneeType)
    cursor = graphene.String()

    def resolve_cursor(self, info):
        return str(self.issue_id)

    def resolve_repo(self, info):
        return self.repo
    
    def resolve_messages(self, info):
        messages = [ref.message for ref in self.message_refs]
        return messages
    
    def resolve_labels(self, info):
        return self.labels
    
    def resolve_assignees(self, info):
        return self.assignees
    
class IssueAssigneeType(SQLAlchemyObjectType):

    class Meta:
        model = IssueAssignee
        use_connection = True

class IssueLabelType(SQLAlchemyObjectType):

    class Meta:
        model = IssueLabel
        use_connection = True


################ Pull Request Objects ############
class PullRequestType(SQLAlchemyObjectType):
    class Meta:
        model = PullRequest
        use_connection = True

    repo = graphene.Field(RepoType)
    messages = graphene.List(lambda: MessageType)
    reviews = graphene.List(lambda: PullRequestReviewType)
    labels = graphene.List(lambda: PrLabelType)
    assignees = graphene.List(lambda: PullRequestAssigneeType)
    files = graphene.List(lambda: PullRequestFileType)
    cursor = graphene.String()

    def resolve_cursor(self, info):
        return str(self.pull_request_id)

    def resolve_repo(self, info):
        return self.repo
    
    def resolve_messages(self, info):
        messages = [ref.message for ref in self.message_refs]
        return messages
    
    def resolve_reviews(self, info):
        return self.reviews
    
    def resolve_labels(self, info):
        return self.labels
    
    def resolve_assignees(self, info):
        return self.assignees
    
    def resolve_files(self, info):
        return self.files
    
class PullRequestAssigneeType(SQLAlchemyObjectType):

    class Meta:
        model = PullRequestAssignee
        use_connection = True
    
class PullRequestReviewType(SQLAlchemyObjectType):

    class Meta:
        model = PullRequestReview
        use_connection = True

class PrLabelType(SQLAlchemyObjectType):

    class Meta:
        model = PullRequestLabel
        use_connection = True


class PullRequestFileType(SQLAlchemyObjectType):

    class Meta:
        model = PullRequestFile
        use_connection = True

class PullRequestCommitType(SQLAlchemyObjectType):

    class Meta:
        model = PullRequestCommit
        use_connection = True



########### Contributor Types #############
class ContributorType(SQLAlchemyObjectType):

    class Meta:
        model = Contributor
        use_connection = True
    
    issues_opened = graphene.List(lambda: IssueType)
    pull_requests = graphene.List(lambda: PullRequestType)
    pull_request_reviews = graphene.List(lambda: PullRequestReviewType)
    commits = graphene.List(lambda: CommitType)
    cursor = graphene.String()

    def resolve_cursor(self, info):
        return str(self.cntrb_id)

    def resolve_issues_opened(self, info):
        return self.issues_opened
    
    def resolve_pull_requests(self, info):
        return self.pull_requests

    def resolve_pull_request_reviews(self, info):
        return self.pull_request_reviews
    
    def resolve_commits(self, info):
        return self.commits
    
class ContributorAliasType(SQLAlchemyObjectType):

    class Meta:
        model = ContributorsAlias
        use_connection = True



########### Other Types ################
class MessageType(SQLAlchemyObjectType):

    class Meta:
        model = Message
        use_connection = True

    def resolve_repo(self, info):
        return self.repo
    
    cursor = graphene.String()

    def resolve_cursor(self, info):
        return str(self.msg_id)
    
class CommitType(SQLAlchemyObjectType):

    class Meta:
        model = Commit
        use_connection = True

    messages = graphene.List(MessageType)

    def resolve_repo(self, info):
        return self.repo

class PageInfoType(graphene.ObjectType):
    next_cursor = graphene.String()
    has_next_page = graphene.Boolean()




########### Connection Objects #############
class GenericConnection(graphene.ObjectType):
    page_info = graphene.Field(PageInfoType)

class RepoConnection(GenericConnection):
    items = graphene.List(RepoType)

class IssueConnection(GenericConnection):
    items = graphene.List(IssueType)

class PullRequestConnection(GenericConnection):
    items = graphene.List(PullRequestType)

class CommitConnection(GenericConnection):
    items = graphene.List(CommitType)

class ContributorConnection(GenericConnection):
    items = graphene.List(ContributorType)

class MessageConnection(GenericConnection):
    items = graphene.List(MessageType)


############### Base Query object ##############
class Query(graphene.ObjectType):

    repos = graphene.Field(RepoConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    repo = graphene.Field(RepoType, id=graphene.Int())

    issues = graphene.Field(IssueConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    issue = graphene.Field(IssueType, id=graphene.Int())

    prs = graphene.Field(PullRequestConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    pr = graphene.List(PullRequestType, id=graphene.Int())

    messages = graphene.Field(MessageConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    commits = graphene.Field(CommitConnection, after=graphene.String(), limit=graphene.Int(default_value=10))

    contributors = graphene.Field(ContributorConnection, after=graphene.String(), limit=graphene.Int(default_value=10))
    contributor = graphene.Field(ContributorType, id=graphene.UUID())

    def resolve_repos(self, info, after=None, limit=None):
        repo_connection = get_connection(Repo, "repo_id", RepoConnection, after, limit)
        return repo_connection

    def resolve_repo(self, info, id):
        return db_session.query(Repo).filter(Repo.repo_id==id).first()

    def resolve_issues(self, info, after=None, limit=None):
        issue_connection = get_connection(Issue, "issue_id", IssueConnection, after, limit)
        return issue_connection
    
    def resolve_issue(self, info, id):
        return db_session.query(Issue).filter(Issue.issue_id==id).first()

    def resolve_prs(self, info, after=None, limit=None):
        pr_connection = get_connection(PullRequest, "pull_request_id", PullRequestConnection, after, limit)
        return pr_connection
    
    def resolve_pr(self, info, id):
        return db_session.query(PullRequest).filter(PullRequest.pull_request_id==id).first()
    
    def resolve_messages(self, info, after=None, limit=None):
        messages_connection = get_connection(Message, "msg_id", MessageConnection, after, limit)
        return messages_connection
    
    def resolve_commits(self, info, after=None, limit=None):
        commit_connection = get_connection(Commit, "cmt_id", CommitConnection, after, limit)
        return commit_connection
    
    def resolve_contributors(self, info, after=None, limit=None):
        contributors_connection = get_connection(Contributor, "cntrb_id", ContributorConnection, after, limit)
        return contributors_connection
    
    def resolve_contributor(self, info, id):
        return db_session.query(Contributor).filter(Contributor.cntrb_id==id).first()
    



template_dir = str(Path(__file__).parent.parent / "templates")
static_dir = str(Path(__file__).parent.parent / "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
logger.debug("Created Flask app")

# defines the api version on the flask app, 
# so when we pass the flask app to the routes files we 
# know can access the api version via the app variable
app.augur_api_version = AUGUR_API_VERSION
app.engine = engine

CORS(app)
app.url_map.strict_slashes = False

app.config['WTF_CSRF_ENABLED'] = False


logger.debug("Creating API routes...")
create_metrics()

@app.route('/ping')
@app.route('/status')
@app.route('/healthcheck')
def index():
    """
    Redirects to health check route
    """
    return redirect(app.augur_api_version)

@app.route(f'/{app.augur_api_version}/')
@app.route(f'/{app.augur_api_version}/status')
def status():
    """
    Health check route
    """
    status = {
        'status': 'OK',
        'version': augur_code_version
    }
    return Response(response=json.dumps(status),
                    status=200,
                    mimetype="application/json")

schema = graphene.Schema(query=Query)

class AuthenticatedGraphQLView(GraphQLView):
    def dispatch_request(self):
        
        api_key = request.headers.get('x-api-key')

        client_applications = db_session.query(ClientApplication).all()
        api_keys = [app.api_key for app in client_applications]
        
        if not api_key or api_key not in api_keys:
            return jsonify(error="Invalid or missing API key"), 403
        
        return super().dispatch_request()

schema = graphene.Schema(query=Query)

app.add_url_rule(f'/{app.augur_api_version}/graphql', view_func=AuthenticatedGraphQLView.as_view('graphql', schema=schema, graphiql=True))

from .routes import *

# import frontend routes
from .view.augur_view import *
from .view.routes import *
from .view.api import *

cache_manager = create_cache_manager()
server_cache = get_server_cache(cache_manager)
