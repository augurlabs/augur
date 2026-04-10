from flask import Flask, request, session, render_template, url_for, redirect, send_file, Response
from sqlalchemy import MetaData, Table, create_engine
from bootstrap import ServerThread, Environment
from sqlalchemy.orm import Session
from secrets import token_hex
from functools import wraps
from pathlib import Path
import os

import threading, json, subprocess, re, importlib.util, sys

env = Environment()

# Assuming the script is run from the root project directory
# (IE: where the makefile is located)
top = Path.cwd()
template_dir = top / "augur/templates/"
static_dir = top / "augur/static/"

# Use CONFIG_DATADIR if set, otherwise default to project root for db.config.json
config_dir = Path(os.getenv("CONFIG_DATADIR", str(top)))
dbfile = config_dir / "db.config.json"

config_script = top / "scripts/install/config.sh"

print(top)

if "metadata" not in sys.modules:
    # Docker build changes module hierarchy for some reason
    spec = importlib.util.spec_from_file_location("metadata", top / "metadata.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["metadata"] = module
    spec.loader.exec_module(module)

from metadata import __version__

def requires_key(func):
    global app
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.args.get("key") or request.form.get("key") or session.get("key")
        
        if not key or key != app.secret_key:
            return redirect(url_for("root"))
        return func(*args, **kwargs)
    
    return wrapper

def get_db_config() -> dict[str, dict[str, str]]:
    out = subprocess.Popen("augur config get_all_json".split(), text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    result = out.communicate()[0]
    return json.loads(result)

def render_section(template, **kwargs):
    global app
    with app.app_context():
        return json.loads(render_template(f"json/{template}.j2", **kwargs))

def get_db_string(db_config):
    return f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database_name']}"

def first_time(setup_key, port = 5000):
    """
    Run first time setup for this instance.
    """
    global app
    app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
    app.secret_key = setup_key
    sections = []
    
    dbconf = {
        "user":"", 
        "password":"", 
        "host":"", 
        "port":"", 
        "database_name":""
    }
    
    if dbstring := env["AUGUR_DB"]:
        sections.append({ "title": "Database", "settings": [
            { "id": "connection_string",
                "display_name": "Database Connection String",
                "value": dbstring,
                "description": "This connection string was provided pre-setup as an environment variable."
            }
        ]})
    else:
        if dbfile.exists():
            dbconf = json.load(dbfile.open())
        sections.append(render_section("db.json", dbconf=dbconf, subtitle="Current config"))

    def all_in(source, update):
        for key in update.keys():
            if key not in source:
                return False
        return True

    # Create a multithreading context for message passing
    update_complete = threading.Condition()
    
    @app.route("/favicon.ico")
    def get_favicon():
        return send_file(static_dir / "favicon" / "favicon.ico")

    @app.route("/", methods = ["GET", "POST"])
    def root():
        key = request.args.get("key") or request.form.get("key") or session.get("key")
        
        if not key or key != app.secret_key:
            return render_template("first-time-key.j2")
        
        session["key"] = key
        return render_template("first-time.j2", sections = sections, version = __version__)
    
    @app.route("/config")
    @requires_key
    def config():
        sections = []
        config = get_db_config()
        facade_dir = ""
        
        for section_name, section_dict in config.items():
            temp_section = {"title": section_name, "settings": []}
            for setting_name, value in section_dict.items():
                temp_section["settings"].append({
                    "id": f"{section_name}.{setting_name}",
                    "display_name": setting_name.replace("_", " ").title(),
                    "value": value,
                    "description": ""
                })
                
                if section_name == "Facade" and setting_name == "repo_directory":
                    facade_dir = value
                    
            sections.append(temp_section)

        credentials = {}
        if facade_dir:
            try:
                credential_file = Path(facade_dir) / ".git-credentials"
                for line in credential_file.read_text().splitlines():
                    match = re.match("https://(.*?):(.*?)@(.*?)\\.\\w+", line)
                    groups = match.groups()
                    if groups[2] not in credentials:
                        credentials[groups[2]] = groups[0]
            except:
                credentials.clear()
                
        gh_name, gl_name = credentials.get("github"), credentials.get("gitlab")
        essential_config = json.loads(render_template("json/essential_config.json.j2", conf=config, gh_name=gh_name, gl_name=gl_name))
        
        for setting in essential_config["settings"]:
            if env[setting["id"]]:
                setting["value"] = env[setting["id"]]

        return render_template("first-time-config.j2", essential_config=essential_config, sections = sections, version = __version__)
    
    @app.route("/db/test")
    @requires_key
    def test_db():
        test = subprocess.Popen("augur db test-connection".split(), text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        result = test.communicate()
        if test.returncode:
            return result[1], 500
        elif result[0]:
            return result[0], 500
        return "Success!"
    
    @app.route("/db/version")
    @requires_key
    def version_db():
        out = subprocess.Popen("augur db print-db-version".split(), text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        result = out.communicate()[0]
        return result or "Undefined"
    
    @app.route("/db/versions/list")
    @requires_key
    def versions_db():
        out = subprocess.Popen("augur db check-for-upgrade".split(), text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        result = out.communicate()[0]
        return result or "Error"
    
    @app.route("/db/config/load", methods=["POST"])
    @requires_key
    def update_config_db():
        data = request.get_json()
        
        result = subprocess.Popen("augur db create-schema".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result.wait()

        for key, value in data.items():
            env[key] = value
        result = subprocess.Popen(f"{config_script}", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            result.wait(120)
        except:
            return "Timeout reached waiting for database update to complete", 500

        return "https://www.google.com"
    
    @app.route("/db/config/download")
    @requires_key
    def get_config_db():
        out = subprocess.Popen("augur config get_all_json".split(), text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        result = out.communicate()[0]
        return Response(result, 
            mimetype='application/json',
            headers={'Content-Disposition':'attachment;filename=config.json'})
    
    @app.route("/db/update", methods=["GET", "POST"])
    @requires_key
    def update_db():
        if dbstring := request.args.get("dbstring"):
            env["AUGUR_DB"] = dbstring
        else:
            data = request.get_json()
            dbconf.update(data)
            json.dump(dbconf, dbfile.open("w"), indent=4)
            sections.clear()
            sections.append(render_section("db.json", dbconf=dbconf, subtitle="Updated config"))
        
        return redirect(url_for("root"))

    @app.route("/stop")
    @requires_key
    def shutdown():
        # Notify the primary thread that the temp server is going down
        global do_continue
        do_continue = request.args.get("continue")
        update_complete.acquire()
        update_complete.notify_all()
        update_complete.release()
        return "Server shutting down"

    # Start a single-use server for first-time setup
    server = ServerThread(app, port = port, reraise = True)
    server.start()

    # Listen for the server /stop command, then shutdown the server
    update_complete.acquire()
    try:
        update_complete.wait()
    except KeyboardInterrupt as e:
        # Shutdown gracefully on interrupt and abort relaunch
        print("Shutting down on keyboard interrupt")
    except Exception as e:
        # On an unexpected exception, reraise after shutting down
        raise e
    finally:
        server.shutdown()
        update_complete.release()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = input("Enter the port to use for the configuration interface [8075]: ") or "8075"
    
    setup_key = token_hex()
    print("-" * 40)
    print("The configuration interface is starting up")
    print("You'll need the following key to unlock the interface:", setup_key)
    print("If you're hosting Augur locally, you can open this link to access the interface:")
    print(f"http://127.0.0.1:{port}?key={setup_key}")
    
    first_time(setup_key, port)
    
    print("First time setup exiting")
    
    global do_continue
    if do_continue:
        if env["AUGUR_DOCKER_DEPLOY"]:
            augur = subprocess.Popen(f"augur backend start {env['AUGUR_FLAGS'] or ''}".split())
            augur.wait()
        else:
            subprocess.Popen(f"nohup augur backend start {env['AUGUR_FLAGS'] or ''}".split())

    #     if not settings:
    #         # First time setup was aborted, so just quit
    #         os._exit(1)

    #     with open(config_location, "w") as config_file:
    #         yaml.dump(settings, config_file)

    # if not env["DEVELOPMENT"] and not gunicorn_location.is_file():
    #     with open(gunicorn_location, "w") as gunicorn_py:
    #         gunicorn_py.write(gunicorn_conf)

    # if env["DEVELOPMENT"]:
    #     from augur_view import app
    #     server = ServerThread(app, port = server_port, address = host_address, reraise = True)
    #     server.start()
    # else:
    #     server = subprocess.Popen(["gunicorn", "-c", str(gunicorn_location), "-b", f"{host_address}:{server_port}", "augur_view:app"])

    # try:
    #     server.wait()
    # except KeyboardInterrupt:
    #     # Shutdown gracefully on interrupt
    #     server.terminate()
    #     print("\nShutting down gracefully")