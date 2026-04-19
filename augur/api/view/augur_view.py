from flask import render_template, redirect, url_for, session, request, jsonify
from flask_login import LoginManager, current_user, login_required
from io import StringIO
from .utils import *
from .init import logger
from .url_converters import *

from functools import wraps

# from .server import User
from ..server import app, db_session
from augur.application.db.models import User, UserSessionToken
from augur.api.routes import AUGUR_API_VERSION
from augur.api.util import get_bearer_token

import time, traceback

login_manager = LoginManager()

login_manager.init_app(app)

app.secret_key = getSetting("session_key")

app.url_map.converters['list'] = ListConverter
app.url_map.converters['bool'] = BoolConverter
app.url_map.converters['json'] = JSONConverter

# Code 404 response page, for pages not found
@app.errorhandler(404)
def page_not_found(error):
    if AUGUR_API_VERSION in str(request.path):
        return jsonify({"status": "Not Found"}), 404

    return render_template('index.j2', title='404'), 404

@app.errorhandler(405)
def unsupported_method(error):
    if AUGUR_API_VERSION in str(request.path):
        return jsonify({"status": "Unsupported method"}), 405
    
    return render_message("405 - Method not supported", "The resource you are trying to access does not support the request method used"), 405

@app.errorhandler(403)
def forbidden(error):
    if AUGUR_API_VERSION in str(request.url_rule):
        return jsonify({"status": "Forbidden"}), 403
    
    return render_message("403 - Forbidden", "You do not have permission to view this page"), 403

@app.errorhandler(500)
def internal_server_error(error):
    if AUGUR_API_VERSION in str(request.path):
        return jsonify({"status": error.original_exception}), 500
    error = error.original_exception
    try:
        errout = StringIO()
        traceback.print_tb(error.__traceback__, file=errout)
        # traceback.print_exception(error, file=errout)
        stacktrace = errout.getvalue()
        stacktrace += f"\n{type(error).__name__}: {str(error)}"
        errout.close()
    except Exception as e:
        logger.error(e)
        raise e
    
    return render_message("500 - Internal Server Error", """An error occurred while trying to service your request.
                          Please try again, and if the error persists, please file a GitHub issue with a description
                          of what you were doing before this error occurred accompanied by the below error message:""", error=stacktrace), 500

@app.template_filter("escape_ID")
def escape_HTML_ID(data: str) -> str:
    # Done this way in case we want to add more replacements in the future
    data = data.replace(".", "\\.")
    return data

@app.template_filter("quoted")
def quote_surrounded(data: str) -> str:
    return '"' + data + '"'

@login_manager.unauthorized_handler
def unauthorized():
    if AUGUR_API_VERSION in str(request.path):
        token_str = get_bearer_token()
        token = db_session.query(UserSessionToken).filter(UserSessionToken.token == token_str).first()
        if not token:
            return jsonify({"status": "Session expired"})

        return jsonify({"status": "Login required"})

    session["login_next"] = url_for(request.endpoint, **request.args)
    return redirect(url_for('user_login'))

@login_manager.user_loader
def load_user(user_id):

    user = User.get_user(db_session, user_id)
    if not user:
        return None

    groups = user.groups
    tokens = user.tokens
    applications = user.applications
    for application in applications:
        sessions = application.sessions
    for group in groups:
        repos = group.repos
    for token in tokens:
        application = token.application


    # The flask_login library sets a unique session["_id"]
    # when login_user() is called successfully
    if session.get("_id") is not None:
    
        user._is_authenticated = True
        user._is_active = True

    return user

@login_manager.request_loader
def load_user_request(request):
    token = get_bearer_token()
    current_time = int(time.time())

    token = db_session.query(UserSessionToken).filter(UserSessionToken.token == token, UserSessionToken.expiration >= current_time).first()

    if token:
        user = token.user
        user._is_authenticated = True
        user._is_active = True
        return user
    
    return None

@app.template_filter('as_datetime')
def as_datetime(seconds):
    time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(seconds))