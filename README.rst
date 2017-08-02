OKAPI: A Microservice Framework
=======================
Deploy and Try
----------------
#. Install `docker` and `docker-compose`
#. Clone this repo to `okapi` folder and `cd okapi` 
#. Run `docker-compose up`
#. Run `docker exec okapi_engine_1 python -c 'from okapi.models import prepare; prepare();'`
#. API gateway is on `http://localhost:5000`
#. Run `pytest tests/test.py` to test the system
#. Inspect `tests/test.py` to learn functionalities. 

Features
---------
#. Upload API program
#. Multiple languge support
#. Compose other API easily
#. Strict privilege control
#. Seperate containers
#. API invoke statistics

REST API Endpoint
--------------------
- OAuth2 prefix: `/okapi/oauth2/v1`
    POST `/token`
        Retrieve an access_token.
    POST `/revoke`
        Refresh access_token.
- User prefix: `/okapi/account/v1`
    GET PUT `/`
        Retrieve or modify user's own profile.
    GET PUT `/client_id`
        Retrieve or refresh user's API invoke client id and secret.
- Service and Runtime prefix `/okapi/service/v1`
    POST `/`
        Create a service profile.
    GET PUT `/<id>`
        Retrieve or modify service(`id`) profile.
    POST `/<id>/update`
        Create a service runtime, namely update service to a new version.
    GET PUT `/<id>/<version>`
         Retrieve or update runtime's info.
    POST `/<id>/<version>/binary`
        Upload a runtime's program.
- Dummy for test previliges, prefix `/okapi/dummy/v1`
    GET `/direct`
    GET `/api`
    GET `/manage`
    GET `/admin`
    GET `/register`
- Gateway **no prefix**
    METHOD `/<user>/<service>/<version>`
        Call a user's specified verson of service APIs.
