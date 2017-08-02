#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import traceback
import threading
import json
import time
import logging
from datetime import timedelta

import requests
from werkzeug.routing import Map, Rule, RequestRedirect, BuildError
from werkzeug.exceptions import HTTPException
from thriftpy.rpc import make_server
from easydict import EasyDict as edict
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient, BackendApplicationClient

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "true"

import pyokapi
from pyokapi import okapi_thrift
from thriftpy.transport import TFramedTransportFactory
bin_path = os.environ.get("BIN_PATH", "/home/okapi/bin")

api = threading.local()
url_map = Map()
view_functions = {}

def _decorator(method):
    def d(rule, **options):
        def decorator(f):
            endpoint = options.pop('endpoint', None)
            options["methods"] = (method,)
            #f = gen.coroutine(f)
            add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator
    return d

for m in ['get', 'post', 'put', 'delete']:
    setattr(pyokapi, m, _decorator(m))
setattr(pyokapi, "api", api)

def _endpoint_from_view_func(view_func):
    """Internal helper that returns the default endpoint for a given
    function.  This always is the function name.
    """
    assert view_func is not None, 'expected view func if endpoint ' \
                                  'is not provided.'
    return view_func.__name__
    
def add_url_rule(rule, endpoint=None, view_func=None, **options):
    if endpoint is None:
        endpoint = _endpoint_from_view_func(view_func)
    options['endpoint'] = endpoint
    methods = options.pop('methods', None)

    # if the methods are not given and the view_func object knows its
    # methods we can use that instead.  If neither exists, we go with
    # a tuple of only `GET` as default.
    if methods is None:
        methods = getattr(view_func, 'methods', None) or ('GET',)
    methods = set(methods)

    # Methods that should always be added
    required_methods = set(getattr(view_func, 'required_methods', ()))

    # starting with Flask 0.8 the view_func object can disable and
    # force-enable the automatic options handling.
    provide_automatic_options = getattr(view_func,
        'provide_automatic_options', None)

    if provide_automatic_options is None:
        if 'OPTIONS' not in methods:
            provide_automatic_options = True
            required_methods.add('OPTIONS')
        else:
            provide_automatic_options = False

    # Add the required methods now.
    methods |= required_methods

    # due to a werkzeug bug we need to make sure that the defaults are
    # None if they are an empty dictionary.  This should not be necessary
    # with Werkzeug 0.7
    options['defaults'] = options.get('defaults') or None

    rule = Rule(rule, methods=methods, **options)
    rule.provide_automatic_options = provide_automatic_options

    url_map.add(rule)
    if view_func is not None:
        old_func = view_functions.get(endpoint)
        if old_func is not None and old_func != view_func:
            raise AssertionError('View function mapping is overwriting an '
                                 'existing endpoint function: %s' % endpoint)
        view_functions[endpoint] = view_func


class Dispatcher(object):

    def InvokeAPI(self, api_path, method, arg, headers, body):

        try:
            print(type(api_path), type(method), type(arg), type(headers), type(body))
            if sys.version_info[0] < 3 :
                if isinstance(api_path, unicode):
                    api_path = api_path.encode('utf-8')
                if isinstance(method, unicode):
                    method = method.encode('utf-8')
                            
            api_path = api_path if api_path.startswith('/') else '/%s' % api_path
            api.args = arg = edict(arg if arg else {})
            api.headers = headers = edict(headers if headers else {})
            
            print("service path: %s, method: %s" % (api_path, method))
            print("arg: %s, headers: %s" % (arg, headers))
             
            if headers.get("Content-Type", '') == "application/json":
                body = json.loads(body)
                if isinstance(body, dict):
                    body = edict(body)
            api.body = body
            #print('body:%s' % api.body)

            try:
                urls = url_map.bind('')
                endpoint, args = urls.match(api_path, method)
                print(endpoint)
                data = view_functions[endpoint](**args)
            except HTTPException as he:
                traceback.print_exc()
                data = he.get_description(), he.code, he.get_headers(None)
            except Exception as e:
                traceback.print_exc()
                data = 'exceptions:%s' % traceback.format_exc(), 500
            result = self.make_response(data)
            #print(result)
        except Exception as e:
            result  = okapi_thrift.Response(code = 602, body = traceback.format_exc(), headers = {})
            
        return result
        
    def make_response(self, rv):
        
        if isinstance(rv, okapi_thrift.Response):
            return rv
        
        status = headers = None          
                
        if isinstance(rv, tuple):
            body, status, headers = rv + (None,) * (3 - len(rv))
        else:
            body = "" if (rv is None or rv == '') else rv
            
        status = status if status else 200
        headers = headers if headers else {}
        
        if isinstance(headers, list):
            _headers = {}
            for k,v in headers:
                _headers[k] = v
            headers = _headers
        
        if isinstance(body, dict) or isinstance(body, list):
            body = json.dumps(body)
            headers["Content-Type"] = "application/json"
        else:
            if sys.version_info[0] >= 3:
                body = str(body)
            elif isinstance(body, unicode):
                body = body.encode('utf8')
            else:
                body = str(body)
            
        if not isinstance(body, bytes):
            body = str(body).encode()
        
        return okapi_thrift.Response(code = status, body = body, headers = headers)

def serve_forever(runtime, port, client):
    try:
        api_details = import_module(runtime.entrypoint)
        r = client.post("http://okapi-engine:5000/okapi/service/v1/%s/%s/spec" % (runtime.service_name, runtime.service_version), json = api_details)
        logging.debug("post service spec status: %s" % r.status_code)
    except:
        traceback.print_exc()
    try:
        logging.info("start to serve on port %s" % port)
        server = make_server(okapi_thrift.InvokeService, Dispatcher(), '0.0.0.0', port, trans_factory=TFramedTransportFactory())
        server.serve()
    except Exception as e:
        traceback.print_exc()
        sys.exit(2)  # serve fails (e.g. port already used) or serve exited (e.g. user press CTRL+C)

def import_module(name):
    __import__(name)
    api_details = []
    for rule in url_map.iter_rules():
        ms = rule.methods - set(["OPTIONS", "HEAD"])
        api_details.append({'rule': rule.rule, 'methods': list(ms), 'function': rule.endpoint})
    logging.debug("getting service api specs: %s" % api_details)
    return api_details
        
def deploy(runtime, client):
    try:
        r = client.get("http://okapi-engine:5000/okapi/service/v1/%s/%s/binary" % 
            (runtime.service_name, runtime.service_version)
        )
    except:
        logging.debug("request error", exc_info = True)
    if not r.ok:
        raise
    path = "%s/%s/" % (bin_path, runtime.service_name)
    from tempfile import NamedTemporaryFile
    import  zipfile
    with NamedTemporaryFile('wb') as f:
        f.write(r.content)
        f.flush()
        z = zipfile.ZipFile(f.name)
        z.extractall(path)
        z.close()
    sys.path.insert(0, path)
    
if __name__ == '__main__':
    
    username = os.environ.get("OKAPI_USER_NAME", None)
    service_name = os.environ.get("OKAPI_SERVICE_NAME", None)
    service_version = os.environ.get("OKAPI_SERVICE_VERSION", None)
    port = int(os.environ.get("OKAPI_DEPLOY_PORT", 23241))
    entrypoint = os.environ.get("OKAPI_ENTRYPOINT", None)
    client_id = os.environ.get("OKAPI_CLIENT_ID", None)
    client_secret = os.environ.get("OKAPI_CLIENT_SECRET", None)
    
    runtime = edict(username = username,
        service_name = service_name,
        service_version = service_version,
        entrypoint = entrypoint,
        client_id = client_id,
        client_secret = client_secret,
    )
    
    token_url = "http://okapi-engine:5000" + "/okapi/oauth2/v1/token"
    client = OAuth2Session(client = BackendApplicationClient(client_id = client_id))
    client.mount('http://', 
        requests.adapters.HTTPAdapter(max_retries=2, pool_connections=1, pool_maxsize=1)
    )

    client.headers.update({"Connection": "close"})
    client.fetch_token(token_url, client_id = client_id, client_secret = client_secret)
        
    deploy(runtime, client)
    serve_forever(runtime, port, client)
