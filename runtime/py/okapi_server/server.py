#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import traceback
import threading
import json
import time
from datetime import timedelta
from werkzeug.routing import Map, Rule, RequestRedirect, BuildError
from werkzeug.exceptions import HTTPException

from thriftpy.rpc import make_server
from easydict import EasyDict as edict

from tornado import gen, ioloop
import pyokapi
from pyokapi import client, api, okapi_thrift
from thriftpy.transport import TFramedTransportFactory
bin_path = os.environ.get("BIN_PATH", "/home/okapi/bin")

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
            
            print("invoke %s, service path: %s, method: %s" % (api_id, api_path, method))
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

def serve_forever(runtime, port):  
    import_module(runtime)
    try:
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
    return api_details
        
def deploy(runtime):
    r = client.get("/okapi/service/v1/%s/%s/binary" % (service_id, version))
    path = "%s/%s/" % (bin_path, service_id)
    from tempfile import NamedTemporaryFile
    import zipfile
    with NamedTemporaryFile('wb') as f:
        f.write(r.stream.read())
        f.flush()
        z = zipfile.ZipFile(f.name)
        z.extractall(path)
        z.close()
    sys.path.insert(0, path)
    import_module()
    
if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("action", help="")
    parser.add_argument("name", help="")
    parser.add_argument("version", help="")
    parser.add_argument("port", help="")
    args = parser.parse_args()
    runtime = client.get("")
    if args.action == "deploy":
        deploy(runtime)
    elif args.action == "serve":
        serve_forever(runtime, port)
