# -*- coding: utf-8 -*-
import docker
from oauthlib.common import generate_token

from . import app, db
from .models import Client, User

docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

def start_service(runtime):
    client_id = "%s_container" % runtime.username
    client = Client.query.filter_by(client_id=client_id).first()
    if client is None:
        user = User.query.filter_by(username=runtime.username).first()
        client = Client(client_id=client_id, 
            name = client_id,
            user_id = user.id,
            client_secret=generate_token(), 
            client_type = "confidential",
            _default_scope = "manage api",
            _allowed_grant_types = "client_credentials",
        )
        db.session.add(client)
        db.session.commit()
    environment  = {
        "OKAPI_USER_NAME": runtime.username,
        "OKAPI_SERVICE_NAME": runtime.service_name,
        "OKAPI_SERVICE_VERSION": runtime.version,
        "OKAPI_DEPLOY_PORT": 23241,
        "OKAPI_ENTRYPOINT": runtime.entrypoint,
        "OKAPI_CLIENT_ID": client.client_id,
        "OKAPI_CLIENT_SECRET": client.client_secret,
    }
    container_name = "%s_%s_%s" % (runtime.username, runtime.service_name, runtime.version)
    try:
        container = docker_client.containers.get(container_name)
        container.remove(force=True)
    except:
        app.logger.debug("get container error", exc_info = True)
    container = docker_client.containers.run('okapi/okapi-py', detach=True,
        environment = environment,
        network = "okapi_network",
        name = container_name,
    )
    app.logger.debug(container.logs())
    app.logger.debug("container id:%s, name:%s" % (container.id, container.name))