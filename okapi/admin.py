# coding:utf-8

from flask import Blueprint, request

from . import app, db
from .oauth2 import oauth, User

mod = Blueprint("admin", __name__)

@mod.route("/user", methods = ["POST"])
@oauth.require_oauth('admin', 'check')
def create_user():
    info = request.json
    user = User(username = info["username"],
        nickname = info["nickname"],
        email = info["email"],
        tel = info.get("tel", None),
        password = info["password"]
    )
    app.logger.debug("add user %r to db" % user)
    db.session.add(user)
    db.session.commit()
    return "", 201

@mod.route("/user/<username>", methods = ["DELETE"])
@oauth.require_oauth('admin')
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        if user.username == request.oauth.user.username:
            return "you cannot delete your account", 403
        db.session.delete(user)
        db.session.commit()
        return "", 201
    return "user not found", 404
    
@mod.route("/user/<username>/admin", methods = ['PUT'])
@oauth.require_oauth("admin")
def set_admin(username):
    user = User.query.filter_by(username=username).first()
    if user:
        if user.username == request.oauth.user.username:
            return "you cannot change your admin status", 403
        user.is_admin = request.json["admin"]
        db.session.commit()
        return "", 201
    return "user not found", 404