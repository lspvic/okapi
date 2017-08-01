# coding:utf-8

from flask import Blueprint

from .oauth2 import oauth

mod = Blueprint("test", __name__)

def success():
    return 'success'
    
mod.add_url_rule("/direct", 'direct', view_func = success)
mod.add_url_rule("/api", 'api', view_func = oauth.require_oauth("api")(success))
mod.add_url_rule("/manage", 'manage', view_func = oauth.require_oauth("manage")(success))
mod.add_url_rule("/admin", 'admin', view_func = oauth.require_oauth("admin")(success))
mod.add_url_rule("/register", 'register', view_func = oauth.require_oauth("admin", "check")(success))
