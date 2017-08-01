# -*- coding: utf-8 -*-

import os
from datetime import timedelta

class Config(object):

    #SERVER_NAME = "xms.okapi.site"
    DEBUG = True
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.db')
    
    LOG_DIR = "xms.log"


class RemoteDevConfig(Config):

    #SERVER_NAME = "xms.okapi.site"
    # if actual host is not the SERVER_NAME, it will response 404 for every route
    
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://okapi:43%xdR+g@mysql/okapi?charset=utf8'
    SQLALCHEMY_POOL_RECYCLE = 3600
    
    # for logging in __init__
    LOG_DIR = '/var/log/xms.log'    

class ProductionConfig(RemoteDevConfig):
    DEBUG = False
    
