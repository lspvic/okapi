# -*- coding:utf-8 -*-
import requests
import traceback
import json
from easydict import EasyDict as edict
from pyokapi import Response

OKAPI_SCHEME = 'http'
OKAPI_HOST = 'api.okapi.pub'

def norm_req(api_url):
    if api_url.startswith('http://') or api_url.startswith('https://'):
        return api_url
    else:
        if not api_url.startswith('/'):
            api_url = '/%s' % api_url
        
        return '%s://%s%s' % (OKAPI_SCHEME, OKAPI_HOST, api_url)

def norm_resp(result):
    result.headers = result.headers if result.headers else {}
    content_type = result.headers.get("Content-Type", "")
    if content_type == "application/json":
        if type(result.body) == bytes:
            result.body = result.body.decode()
        result.body = json.loads(result.body)
        if isinstance(result.body, dict):
            result.body = edict(result.body)
    return result

for m in ['get', 'post', 'put', 'delete']:
    globals()[m] = getattr(requests, m)
    
def invoke(uri, method = 'get', args = None, headers = None, body = None):
    uri = norm_req(uri)
    print('forward service: %s' % uri)
    method = method.upper()
    headers = headers if headers else {}
    args = args if args else {}
    if body and (method == 'GET' or method == 'DELETE'):
        body = None
    elif (method == 'POST' or method == 'PUT') and not body:
        body = ''
    try:
        if isinstance(body, dict) or isinstance(body, list):
            body = json.dumps(body)
            headers["Content-Type"] = "application/json"
            
        resp = getattr(requests, method.lower())(url = uri, params = args, headers = headers, data = body)                      
        resp = Response(code = resp.status_code, headers = resp.headers, body = resp.content)
        print("success %s: %s" % (uri, resp.code))
        resp = norm_resp(resp)
        return resp
    except:
        traceback.print_exc()
        resp = Response(code = 602, body = 'forward service request fails: %s' % traceback.format_exc())
        return resp
