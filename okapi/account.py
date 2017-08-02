# coding:utf-8

from flask import Blueprint, request, jsonify
from oauthlib.common import generate_token

from . import app, db
from .oauth2 import oauth, Client

mod = Blueprint("user", __name__)

@mod.route("/", methods = ['GET', 'PUT'])
@oauth.require_oauth('manage')
def mod_user():
    user = request.oauth.user
    if request.method == "GET":
        return jsonify(username=user.username,
            nickname = user.nickname,
            email = user.email,
            tel = user.tel,
        )
    else:
        info = request.json
        for attr in ('nickname', 'email', 'tel'):
            if attr in info:
                setattr(user, attr, info[attr])
        db.session.commit()
        return "", 201

@mod.route("/password", methods = ['PUT'])
@oauth.require_oauth('manage')
def mod_password():
    # TODO
    raise

@mod.route("/client_id", methods = ['GET', 'PUT'])
@oauth.require_oauth('manage')
def client_id():
    user = request.oauth.user
    name = 'api_call_client'
    client = Client.query.filter_by(user_id=user.id, name = name).first()
    if client:
        if request.method == 'GET':
            client_id = client.client_id
        else:
            client.client_id = generate_token()
            db.session.commit()
    else:
        client = Client(name = name,
            client_id=generate_token(), 
            user_id=user.id, 
            _default_scope = 'api', 
            _allowed_grant_types = 'client_credentials',
            client_type = 'confidential')
        app.logger.debug("%r api client id changed: %s" % (user, client.client_id))
        db.session.add(client)
        db.session.commit()
    return jsonify(client_id = client.client_id)