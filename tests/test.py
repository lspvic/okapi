# -*- coding: utf-8 -*-

import pytest
import os
from functools import partial
import json
import logging
import time
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logging.basicConfig(level=logging.DEBUG)

import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient, BackendApplicationClient

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "true"

base_url = "http://118.89.166.229:5001"
#base_url = "http://localhost:5000"
token_url = base_url + "/okapi/oauth2/v1/token"

admin_client = OAuth2Session(client = LegacyApplicationClient(client_id="admin_client"))
admin_client.fetch_token(token_url, 
    client_id = "admin_client",
    username = "okapi",
    password = "okapi",
)

manage_client = OAuth2Session(client = LegacyApplicationClient(client_id="manage_client"))
manage_client.fetch_token(token_url, 
    client_id = "manage_client",
    username = "lspvic",
    password = "lspvic",
)

def test_scopes():

    resp = requests.get(base_url + "/okapi/dummy/v1/direct")
    assert resp.text == 'success'
    
    resp = manage_client.get(base_url + "/okapi/account/v1/client_id")
    client_id = resp.json()["client_id"]
    api_client = OAuth2Session(client = BackendApplicationClient(client_id = client_id))
    api_client.fetch_token(token_url, client_id = client_id)
    
    assert requests.get(base_url + "/okapi/dummy/v1/api").status_code == 401
    assert api_client.get(base_url + "/okapi/dummy/v1/api").text == 'success'
    assert manage_client.get(base_url + "/okapi/dummy/v1/api").status_code == 401
    assert admin_client.get(base_url + "/okapi/dummy/v1/api").status_code == 401
    assert api_client.get(base_url + "/okapi/dummy/v1/manage").status_code == 401
    assert manage_client.get(base_url + "/okapi/dummy/v1/manage").text == "success"
    assert admin_client.get(base_url + "/okapi/dummy/v1/manage").status_code == 401
    assert api_client.get(base_url + "/okapi/dummy/v1/admin").status_code == 401
    assert manage_client.get(base_url + "/okapi/dummy/v1/admin").status_code == 401
    assert admin_client.get(base_url + "/okapi/dummy/v1/admin").text == "success"
    assert admin_client.get(base_url + "/okapi/dummy/v1/register").text == "success"
    assert admin_client.get(base_url + "/okapi/account/v1/client_id").status_code == 401

def test_user_create():

    data = {"username": "dummy",
        "nickname": "柳生一刀",
        "email": "dummy@qq.com",
        "tel": "15869189782",
        "password": "dummy",
    }
    
    assert admin_client.post(base_url + "/okapi/admin/v1/user", json = data).status_code == 201
    
    manage_client =OAuth2Session(client = LegacyApplicationClient(client_id="manage_client"))
    manage_client.fetch_token(token_url, 
        client_id = "manage_client",
        username = data["username"],
        password = data["password"],
    )
    
    content = manage_client.get(base_url + "/okapi/account/v1/").json()
    del data["password"]
    assert content == data
    
    update =  {"tel": "17606529782", "nickname": "不想写论文"}
    
    assert manage_client.put(base_url + "/okapi/account/v1/", json =update).status_code == 201

    content = manage_client.get(base_url + "/okapi/account/v1/").json()
    data.update(update)
    assert content == data
    
    api_client_id_old = manage_client.get(base_url + "/okapi/account/v1/client_id").json()["client_id"]
    api_client_id_new = manage_client.put(base_url + "/okapi/account/v1/client_id").json()["client_id"]
    assert api_client_id_new != api_client_id_old
    
    ## TODO: modify password
    
    assert admin_client.delete(base_url + "/okapi/admin/v1/user/%s" % data["username"]).status_code == 201
    
def test_new_token():
    assert manage_client.get(base_url + "/okapi/dummy/v1/manage").text == "success"

    token = manage_client.token
    manage_client.fetch_token(token_url, 
        client_id = "manage_client",
        username = "lspvic",
        password = "lspvic",
    )
    
    new_token = manage_client.token
    manage_client.token = token
    assert manage_client.get(base_url + "/okapi/dummy/v1/manage").status_code == 401
    
    manage_client.token = new_token
    assert manage_client.get(base_url + "/okapi/dummy/v1/manage").text == "success"

def  test_service():
    service = {
        'name': 'weather',
        'title': '天气',
        'description': '提供天气情况查询',
        'tags':'weather',
    }
    client = manage_client
    
    assert client.post(base_url + "/okapi/service/v1/", json=service).status_code == 201
    assert client.get(base_url + "/okapi/service/v1/weather").json() == service
    
    update = {'title': '天气查询', 'tags': 'weather life'}
    service.update(update)
    assert client.put(base_url + "/okapi/service/v1/weather",  json=update).status_code == 201
    assert client.get(base_url + "/okapi/service/v1/weather").json() == service


def test_service_version():
    version = {
        "notes": "initial version",
        "runtime": "py3",
        "entrypoint": "flightzl",
    }
    resp = manage_client.post(base_url + "/okapi/service/v1/weather/update", json=version)
    assert resp.status_code == 201
    service_info = resp.json()        
    version = service_info["version"]
    assert manage_client.get(base_url + "/okapi/service/v1/weather/%s" % version).json() ==  service_info
    update = {"notes": "updated", "entrypoint": "flightzl"}
    assert manage_client.put(base_url + "/okapi/service/v1/weather/%s" % version, json=update).status_code == 201
    service_info.update(update)
    del service_info["update_time"]
    new_info = manage_client.get(base_url + "/okapi/service/v1/weather/%s"% version).json()
    del new_info["update_time"]
    assert new_info == service_info
            
def test_upload_binary():
    version = {
        "notes": "initial version",
        "runtime": "py3",
        "entrypoint": "flighzl",
    }
    resp = manage_client.post(base_url + "/okapi/service/v1/weather/update", json=version)
    assert resp.status_code == 201
    with open("example.zip", "rb") as fp:
        assert manage_client.post(base_url + "/okapi/service/v1/weather/v1/binary", data=fp.read()).status_code == 201
    #resp = self.manage_client.get(base_url + "/okapi/service/v1/weather/v1/binary")
    #with open("example2.zip", "wb") as fp:
    #    fp.write(resp.content)
    
def test_api_call():
    client_id = manage_client.get(base_url + "/okapi/account/v1/client_id").json()["client_id"]
    api_client = OAuth2Session(client = BackendApplicationClient(client_id = client_id))
    api_client.fetch_token(token_url, client_id = client_id)
    date = (datetime.now() +  timedelta(days=5)).strftime("%Y-%m-%d")
    resp = api_client.get(base_url + "/lspvic/weather/v1/flightzl?depart_city=杭州&arrival_city=天津&time=%s" % date)
    flights = json.loads(resp.content.decode())
    logger.debug("get flights: %s", flights)
    assert flights["flightCnt"] > 0
