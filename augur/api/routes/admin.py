from augur.api.routes import AUGUR_API_VERSION
from ..server import app
import sqlalchemy as s
import json
from subprocess import run, PIPE, Popen
from flask import Response, current_app, jsonify

from augur.application.db.lib import get_value
from augur.application.logs import AugurLogger
from augur.api.util import admin_required

logger = AugurLogger("augur").get_logger()

@app.route(f"/{AUGUR_API_VERSION}/admin/shutdown")
@admin_required
def shutdown_system():
    run("augur backend stop-collection-blocking".split(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    Popen("augur backend stop", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    
    return jsonify({"status": "shutdown"})

@app.route(f"/{AUGUR_API_VERSION}/admin/restart")
@admin_required
def restart_system():
    Popen("python scripts/control/restart.py", shell=True)

    return jsonify({"status": "restart"})