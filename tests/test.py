# -*- coding: utf-8 -*-

import unittest
import os
from functools import partial

import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient, BackendApplicationClient

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "true"

base_url = "http://118.89.166.229:5001"
#base_url = "http://localhost:5000"
token_url = base_url + "/okapi/oauth2/v1/token"

class TestCase(unittest.TestCase): 
    
    @classmethod
    def setUpClass(self):
        self.admin_client = OAuth2Session(client = LegacyApplicationClient(client_id="admin_client"))
        self.admin_client.fetch_token(token_url, 
            client_id = "admin_client",
            username = "okapi",
            password = "okapi",
        )
        
        self.manage_client = OAuth2Session(client = LegacyApplicationClient(client_id="manage_client"))
        self.manage_client.fetch_token(token_url, 
            client_id = "manage_client",
            username = "lspvic",
            password = "lspvic",
        )

    def test_scopes(self):

        resp = requests.get(base_url + "/okapi/dummy/v1/direct")
        self.assertEqual(resp.text, 'success')
        
        resp = self.manage_client.get(base_url + "/okapi/account/v1/client_id")
        client_id = resp.json()["client_id"]
        api_client = OAuth2Session(client = BackendApplicationClient(client_id = client_id))
        api_client.fetch_token(token_url, client_id = client_id)
        
        self.assertEqual(
            requests.get(base_url + "/okapi/dummy/v1/api").status_code, 
            401
        ) 
        self.assertEqual(
            api_client.get(base_url + "/okapi/dummy/v1/api").text, 
            'success'
        )
        self.assertEqual(
            self.manage_client.get(base_url + "/okapi/dummy/v1/api").status_code, 
            401
        )        
        self.assertEqual(
            self.admin_client.get(base_url + "/okapi/dummy/v1/api").status_code,
            401
        )
        self.assertEqual(
            api_client.get(base_url + "/okapi/dummy/v1/manage").status_code, 
            401
        )
        self.assertEqual(
            self.manage_client.get(base_url + "/okapi/dummy/v1/manage").text, 
            "success"
        )        
        self.assertEqual(
            self.admin_client.get(base_url + "/okapi/dummy/v1/manage").status_code,
            401
        )
        self.assertEqual(
            api_client.get(base_url + "/okapi/dummy/v1/admin").status_code, 
            401
        )
        self.assertEqual(
            self.manage_client.get(base_url + "/okapi/dummy/v1/admin").status_code, 
            401
        )        
        self.assertEqual(
            self.admin_client.get(base_url + "/okapi/dummy/v1/admin").text,
            "success"
        )
        self.assertEqual(
            self.admin_client.get(base_url + "/okapi/dummy/v1/register").text,
            "success"
        )
        self.assertEqual(
            self.admin_client.get(base_url + "/okapi/account/v1/client_id").status_code, 
            401
        )       
    
    def test_user_create(self):

        data = {"username": "dummy",
            "nickname": "柳生一刀",
            "email": "dummy@qq.com",
            "tel": "15869189782",
            "password": "dummy",
        }
        
        self.assertEqual(
            self.admin_client.post(base_url + "/okapi/admin/v1/user", json = data).status_code, 
            201
        )
        
        manage_client =OAuth2Session(client = LegacyApplicationClient(client_id="manage_client"))
        manage_client.fetch_token(token_url, 
            client_id = "manage_client",
            username = data["username"],
            password = data["password"],
        )
        
        content = manage_client.get(base_url + "/okapi/account/v1/").json()
        del data["password"]
        self.assertDictEqual(content, data)
        
        update =  {"tel": "17606529782", "nickname": "不想写论文"}
        
        self.assertEqual(
            manage_client.put(base_url + "/okapi/account/v1/", json =update).status_code, 
            201
        )
        content = manage_client.get(base_url + "/okapi/account/v1/").json()
        data.update(update)
        self.assertDictEqual(content, data)
        
        api_client_id_old = manage_client.get(base_url + "/okapi/account/v1/client_id").json()["client_id"]
        api_client_id_new = manage_client.put(base_url + "/okapi/account/v1/client_id").json()["client_id"]
        self.assertNotEqual(api_client_id_new, api_client_id_old)
        
        ## TODO: modify password
        
        self.assertEqual(
            self.admin_client.delete(base_url + "/okapi/admin/v1/user/%s" % data["username"]).status_code,
            201
        )
    
    def test_new_token(self):
        self.assertEqual(
            self.manage_client.get(base_url + "/okapi/dummy/v1/manage").text, 
            "success"
        )
        token = self.manage_client.token
        self.manage_client.fetch_token(token_url, 
            client_id = "manage_client",
            username = "okapi",
            password = "okapi",
        )
        
        new_token = self.manage_client.token
        self.manage_client.token = token
        self.assertEqual(
            self.manage_client.get(base_url + "/okapi/dummy/v1/manage").status_code, 
            200
        )
        
        self.manage_client.token = new_token
        self.assertEqual(
            self.manage_client.get(base_url + "/okapi/dummy/v1/manage").text, 
            "success"
        )

    def  test_service(self):
        service = {
            'name': 'weather',
            'title': '天气',
            'description': '提供天气情况查询',
            'tags':'weather',
        }
        client = self.manage_client
        
        self.assertEqual(
            client.post(base_url + "/okapi/service/v1/", json=service).status_code, 201)
        self.assertDictEqual(
            client.get(base_url + "/okapi/service/v1/weather").json(), service
        )
        
        update = {'title': '天气查询', 'tags': 'weather life'}
        service.update(update)
        self.assertEqual(
            client.put(base_url + "/okapi/service/v1/weather",  json=update).status_code, 201)
        self.assertDictEqual(
            client.get(base_url + "/okapi/service/v1/weather").json(), service
        )

    def test_service_version(self):
        version = {
            "notes": "initial version",
            "runtime": "py3",
            "entrypoint": "flighzl",
        }
        resp = self.manage_client.post(base_url + "/okapi/service/v1/weather/update", json=version)
        self.assertEqual(resp.status_code, 201)
        service_info = resp.json()        
        version = service_info["version"]
        self.assertDictEqual(
            self.manage_client.get(base_url + "/okapi/service/v1/weather/%s" % version).json(), service_info)
        update = {"notes": "updated", "entrypoint": "flight"}
        self.assertEqual(
            self.manage_client.put(base_url + "/okapi/service/v1/weather/%s" % version, json=update).status_code, 201
        )
        service_info.update(update)
        del service_info["update_time"]
        new_info = self.manage_client.get(base_url + "/okapi/service/v1/weather/%s"% version).json()
        del new_info["update_time"]
        self.assertDictEqual(new_info, service_info)
            
    def test_upload_binary(self):
        version = {
            "notes": "initial version",
            "runtime": "py3",
            "entrypoint": "flighzl",
        }
        resp = self.manage_client.post(base_url + "/okapi/service/v1/weather/update", json=version)
        self.assertEqual(resp.status_code, 201)
        with open("example.zip", "rb") as fp:
            self.assertEqual(
                self.manage_client.post(base_url + "/okapi/service/v1/weather/v1/binary", data=fp.read()).status_code,
                201
            )
        resp = self.manage_client.get(base_url + "/okapi/service/v1/weather/v1/binary")
        with open("example2.zip", "wb") as fp:
            fp.write(resp.content)
        
if __name__ == "__main__":
    unittest.main()