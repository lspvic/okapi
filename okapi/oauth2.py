# coding:utf-8
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_oauthlib.provider import OAuth2Provider

from .import app, db
from .models import User, Grant, Token, Client

oauth = OAuth2Provider(app)

@oauth.clientgetter
def get_client(client_id):
    client = Client.query.filter_by(client_id=client_id).first()
    return client

@oauth.grantgetter
def get_grant(client_id, code):
    return Grant.query.filter_by(client_id=client_id, code=code).first()

@oauth.tokengetter
def get_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    if refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()
    return None

@oauth.grantsetter
def set_grant(client_id, code, request, *args, **kwargs):
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        scope=' '.join(request.scopes),
        user_id=g.user.id,
        expires=expires,
    )
    db.session.add(grant)
    db.session.commit()

@oauth.tokensetter
def set_token(token, req, *args, **kwargs):
    tok = Token(**token)
    tok.user_id = req.user.id
    tok.client_id = req.client.client_id
    Token.query.filter_by(user_id=tok.user_id, client_id=tok.client_id).delete()
    db.session.add(tok)
    db.session.commit()

@oauth.usergetter
def get_user(username, password, client, request, **kwargs):
    user = User.query.filter_by(username=username, password=password).first()
    if user and user.check_password(password):
        if "admin" in client.default_scopes and not user.is_admin:
            return None
        return user
    app.logger.debug("user: %r is None or check password failed", user)
    return None
    
mod = Blueprint("oauth", __name__)

@mod.route('/authorize', methods=['GET', 'POST'])
@oauth.authorize_handler
def authorize(*args, **kwargs):
    # NOTICE: for real project, you need to require login
    if request.method == 'GET':
        # render a page for user to confirm the authorization
        return render_template('confirm.html')

    if request.method == 'HEAD':
        # if HEAD is supported properly, request parameters like
        # client_id should be validated the same way as for 'GET'
        response = make_response('', 200)
        response.headers['X-Client-ID'] = kwargs.get('client_id')
        return response

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'

@mod.route('/token', methods=['POST'])
@oauth.token_handler
def access_token():
    return {}

@mod.route('/revoke', methods=['POST'])
@oauth.revoke_handler
def revoke_token():
    pass

@oauth.invalid_response
def require_oauth_invalid(req):
    return jsonify(message=req.error_message), 401
