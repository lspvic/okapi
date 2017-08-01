# coding: utf-8 
import importlib
import os

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
config_name = os.environ.get('okapi_config', 'okapi.config.Config')
app.config.from_object(config_name) 
db = SQLAlchemy(app)

from .oauth2 import mod as oauth2_mod, oauth
from .account import mod as account_mod
from .service import mod as service_mod
from .admin import mod as admin_mod
from .dummy import mod as dummy_mod

app.register_blueprint(oauth2_mod, url_prefix='/okapi/oauth2/v1')
app.register_blueprint(account_mod, url_prefix='/okapi/account/v1')
app.register_blueprint(service_mod, url_prefix='/okapi/service/v1')
app.register_blueprint(admin_mod, url_prefix='/okapi/admin/v1')
app.register_blueprint(dummy_mod, url_prefix='/okapi/dummy/v1')

@app.route("/<username>/<service>/<version>/<path:path>")
@oauth.require_oauth()
def api_handler(username, service, version, path):
    return 'unimplemented'

@app.route("/")
def list():
    return ""
    
@app.route("/<username>")
def list_by_user(username):
    return ""
    
@app.route("/<username>/<service>")
def api_info(username, service):
    return ""
    
@app.errorhandler(404)
def not_found(error):
    return "service not found", 404
    
@app.errorhandler(500)
def interal_error(error):
    app.logger.debug("internal error", exc_info = True)
    return "internal error", 500


