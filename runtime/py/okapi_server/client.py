#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json, time, os
import requests
import traceback
from easydict import EasyDict as edict
from datetime import timedelta

from pyokapi import _client, okapi_thrift

from thriftpy.rpc import make_client
from thriftpy.transport import TFramedTransportFactory

OKAPI_HOST = os.environ.get('OKAPI_HOST', 'okapi')
OKAPI_PORT = int(os.environ.get('OKAPI_PORTS', 23241))   
               
def _invoke(uri, method = 'get', args = None, headers = None, body = None):

    headers = edict(headers) if headers else edict({})
    args = edict(args) if args else edict({})
    
    seg = uri.split('/')
    remote_id = '.'.join(seg[:3])
    api_path = '/'.join(seg[3:])
    
    print("api id: %s, api path: %s" % (remote_id, api_path), headers)  
    if remote_id != 'okapi.services.1':
        s_info = _invoke('okapi/services/1/%s/deploy/select' % remote_id)
        if s_info.code == 200:
            print('get service address success:', s_info.body)
            _host = s_info.body.host
            _port = s_info.body.port
        else:
            print('get service address fails, %s, %s' % (s_info.code, s_info.body))
            return s_info
    else:
        _host = OKAPI_HOST
        _port = OKAPI_PORT
    try:
        if isinstance(body, dict) or isinstance(body, list):
            print('dict true', headers)
            headers["Content-Type"] = "application/json"
            body = json.dumps(body).encode()
        
        print(args)    
        for arg in args:
            val = str(args[arg])
            setattr(args, arg, val)        

        client = make_client(okapi_thrift.InvokeService, _host, _port, trans_factory=TFramedTransportFactory())
        result = client.InvokeAPI(api_path, method, args, headers, body)
        result = _client.norm_resp(result)
        return result

    except:
        traceback.print_exc()        
        resp = okapi_thrift.Response(code = 600, body = 'connection fails')
        return resp

def invoke(uri, method = 'get', args = None, headers = None, body = None):
    if uri.startswith('http://') or uri.startswith('https://'):
        return _client.invoke(uri, method, args, headers, body)
    else:
        return _invoke(uri, method, args, headers, body)
        
def get(uri, args = None, headers = None, body = None):
    return invoke(uri, method = 'get', args = None, headers = None, body = None)

def post(uri, args = None, headers = None, body = None):
    return invoke(uri, method = 'post', args = None, headers = None, body = None)

def put(uri, args = None, headers = None, body = None):
    return invoke(uri, method = 'put', args = None, headers = None, body = None)
    
def delete(uri, args = None, headers = None, body = None):
    return invoke(uri, method = 'delete', args = None, headers = None, body = None)
