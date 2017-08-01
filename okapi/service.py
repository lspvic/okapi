# coding:utf-8

import time

from flask import Blueprint, request, jsonify, make_response, send_file

from . import app, db
from .oauth2 import oauth
from .models import Service, ServiceVersion
from .tasks import start_service

binary_path = "/var/lib/okapi/binary"

mod = Blueprint("service", __name__)

@mod.route("/")
@oauth.require_oauth('manage')
def list():
    services = Service.query.filter_by(user_id=requst.oauth.user.id).all()
    data = []
    for service in services:
        data.append({
            "name": service.name,
            "description": service.description,
            "tags": service.tags,
        })
    return jsonify(data)
    
@mod.route("/", methods = ['POST'])
@oauth.require_oauth('manage')
def create():
    data = request.json
    service = Service.query.filter_by(name=data["name"], user_id = request.oauth.user.id).first()
    if service:
        return "service already exists", 405
    service = Service(user_id=request.oauth.user.id, **data)
    db.session.add(service)
    db.session.commit()
    return "", 201   
    
@mod.route("/<id>", methods = ['GET', 'PUT'])
@oauth.require_oauth('manage')
def add(id):
    service = Service.query.filter_by(name=id, user_id = request.oauth.user.id).first()
    if not service:
        return "service not found", 404
    if request.method == "GET":
        return jsonify(name=service.name, 
            title = service.title,
            description=service.description, 
            tags=service.tags
        )
    else:
        data = request.json
        for attr in ("title", "description", "tags"):
            if attr in data:
                setattr(service, attr, data[attr])
        db.session.commit()
        return "", 201


@mod.route("/<id>/<version>/binary", methods = ['GET', 'POST'])    
@oauth.require_oauth('manage')
def upload(id, version):
    username = request.oauth.user.username
    service_version = ServiceVersion.query.filter_by(
        username = username,
        service_name = id,
        version = version
    ).first()
    if not service_version:
        return "service version not found", 404
    name = "%s/%s_%s_%s" % (binary_path, username,
        id, version
    )
    if request.method == "POST":
        with open(name, "wb") as f:
            f.write(request.stream.read())
        start_service(service_version)
        return "success", 201
    else:
        with open(name, "rb") as fp:
            return fp.read()
    
@mod.route("/<id>/update", methods = ['POST'])
@oauth.require_oauth('manage')
def update(id):
    username = request.oauth.user.username
    count = ServiceVersion.query.filter_by(
        username = username,
        service_name = id).count()
    data = request.json
    notes = data["notes"]
    runtime = data["runtime"]
    if runtime not in ("py2", "py3", "java"):
        return "runtime not supported", 405
    entrypoint = data["entrypoint"]
    version = "v%s" % (count+1)
    service_version = ServiceVersion(
        username=username, service_name=id,
        notes=notes, runtime=runtime, 
        version=version, entrypoint=entrypoint)
    db.session.add(service_version)
    db.session.commit()
    return jsonify(**service_version.to_dict()), 201
    
@mod.route("/<id>/<version>",methods=['GET', 'PUT'])
@oauth.require_oauth('manage')
def update_info(id, version):
    service_version = ServiceVersion.query.filter_by(
        username = request.oauth.user.username,
        service_name = id,
        version = version
    ).first()
    if not service_version:
        return "version not found", 404
    if request.method == "GET":
        return jsonify(**service_version.to_dict())
    else:
        data = request.json
        if 'runtime' in data:
            runtime = data["runtime"]
            if runtime not in ("py2", "py3", "java", "forward"):
                return "runtime not supported", 405   
            service_version.runtime = runtime
        for attr in ('notes', 'entrypoint'):
            if attr in data:
                setattr(service_version, attr, data[attr])
        service_version.update_time = int(time.time())
        db.session.commit()
        return   "", 201