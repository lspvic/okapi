# -*- coding: utf-8 -*-
import docker
from . import app
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

def start_service(runtime):
    container = client.containers.run('alpine', 'echo hello world', detach=True)
    app.logger.debug(container.logs())
    app.logger.debug("container id:%s, name:%s" % (container.id, container.name))