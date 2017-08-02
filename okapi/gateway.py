# coding:utf-8

import os

from flask import request
import thriftpy
from thriftpy.rpc import make_client
from thriftpy.transport import TFramedTransportFactory

dirname = os.path.dirname(__file__)
okapi_thrift = thriftpy.load(os.path.join(dirname, "okapi.thrift"), module_name="okapi_thrift")

from . import app
from .oauth2 import oauth
from .models import Runtime

@app.route("/<username>/<service>/<version>/<path:path>", methods = ["GET", "POST", "PUT", "DELETE"])
@oauth.require_oauth("api")
def api_handler(username, service, version, path):
    runtime = Runtime.query.filter_by(
        username = username,
        service_name = service,
        version = version,
        obsolete = False,
    ).first()
    if runtime is None:
        return "service not found", 404
    
    if request.method in ('POST', 'PUT'):
        body = request.content
    else:
        body = None
    client = make_client(okapi_thrift.InvokeService, runtime.full_name, 23241, trans_factory=TFramedTransportFactory())
    result = client.InvokeAPI(path, request.method, request.args, request.headers, body)
    return result.body, result.code, result.headers
        
    