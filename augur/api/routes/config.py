#SPDX-License-Identifier: MIT
"""
Creates routes for config functionality
"""
import logging
from flask import request, jsonify, current_app
import sqlalchemy as s

# Disable the requirement for SSL by setting env["AUGUR_DEV"] = True
from augur.api.util import ssl_required, admin_required
from augur.application.db.lib import get_session
from augur.application.db.models import Config
from augur.application.config import AugurConfig
from augur.application.db.session import DatabaseSession
from ..server import app

logger = logging.getLogger(__name__)

from augur.api.routes import AUGUR_API_VERSION

@app.route(f"/{AUGUR_API_VERSION}/config/get", methods=['GET', 'POST'])
@ssl_required
def get_config():
    with DatabaseSession(logger, engine=current_app.engine) as session:
        
        config_dict = AugurConfig(logger, session).config.load_config()

    return jsonify(config_dict), 200

@app.route(f"/{AUGUR_API_VERSION}/config/set", methods=['GET', 'POST'])
@ssl_required
@admin_required
def set_config_item():
    setting = request.args.get("setting")
    section = request.args.get("section")
    value = request.values.get("value")
    
    result = {
        "section_name": section,
        "setting_name": setting,
        "value": value
    }
    
    if not setting or not section or not value:
        return jsonify({"status": "Missing argument"}), 400
    
    with get_session() as session:
        config = AugurConfig(logger, session)
        config.add_or_update_settings([result])
    
    return jsonify({"status": "success"})

@app.route(f"/{AUGUR_API_VERSION}/config/update", methods=['POST'])
@ssl_required
def update_config():
    update_dict = request.get_json()

    with get_session() as session:

        for section, data in update_dict.items():

            for key, value in data.items():

                try:
                    config_setting = session.query(Config).filter(Config.section_name == section, Config.setting_name == key).one()
                except s.orm.exc.NoResultFound:
                    return jsonify({"status": "Bad Request", "section": section, "setting": key}), 400

                config_setting.value = value

                session.add(config_setting)

        session.commit()

    return jsonify({"status": "success"}), 200
