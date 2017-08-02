# -*- coding:utf-8 -*-

import time
from datetime import datetime, timedelta

from sqlalchemy.orm import relationship

from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, index=True,
                         nullable=False)
    nickname = db.Column(db.String(40), nullable = False)
    email = db.Column(db.String(50), nullable = False)
    tel = db.Column(db.String(20))
    password = db.Column(db.String(256), nullable = False)
    is_admin = db.Column(db.Boolean(), default = False)
    
    def __repr__(self):
        return "User(name:%s, nickname:%s)" % (self.username, self.nickname)
    
    def check_password(self, password):
        return self.password == password

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    client_id = db.Column(db.String(40), unique=True, index = True)
    client_secret = db.Column(db.String(55))
    client_type = db.Column(db.String(20), default='public')
    _redirect_uris = db.Column(db.Text, default = 'http://localhost:8000/authorized http://localhost/authorized')
    _default_scope = db.Column(db.Text, default='')
    _allowed_grant_types = db.Column(db.Text, default = 'authorization_code password client_credentials refresh_token')
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable = False,
    )
    user = relationship('User')
    
    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scope:
            return self._default_scope.split()
        return []

    @property
    def allowed_grant_types(self):
        if self._allowed_grant_types:
            return self._allowed_grant_types.split()
        return []

class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')
    )
    user = relationship('User')

    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id', ondelete='CASCADE'),
        nullable=False,
    )
    client = relationship('Client')
    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(255))
    scope = db.Column(db.Text)
    expires = db.Column(db.DateTime)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return None

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id', ondelete='CASCADE'),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')
    )
    user = relationship('User')
    client = relationship('Client')
    token_type = db.Column(db.String(40))
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    expires = db.Column(db.DateTime)
    scope = db.Column(db.Text)

    def __init__(self, **kwargs):
        expires_in = kwargs.pop('expires_in', None)
        if expires_in is not None:
            self.expires = datetime.utcnow() + timedelta(seconds=expires_in)

        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
        
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable = False,
    )
    user = relationship('User')
    name = db.Column(db.String(40), nullable = False)
    title = db.Column(db.String(40), nullable = False)
    description = db.Column(db.Text, nullable = False)
    tags = db.Column(db.Text, default = "")
    
    def __repr__(self):
        return "Service(name=%s, User=%s)" % (self.name, self.user)
    
class Runtime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(
        db.String(40),
        nullable = False,
        index = True,
    )
    username = db.Column(
        db.String(40),
        nullable = False,
        index = True,
    )
    version = db.Column(db.String(40), nullable = False, default = "v1")
    runtime = db.Column(db.String(10), nullable = False)
    create_time = db.Column(db.Integer, nullable=False, default = lambda :int(time.time()))
    notes = db.Column(db.Text, nullable = False)
    update_time = db.Column(db.Integer, nullable = False, default = lambda :int(time.time()))
    entrypoint = db.Column(db.String(256), nullable = False)
    obsolete = db.Column(db.Boolean(), default = False, nullable = False)
    
    @property
    def full_name(self):
        return "%s_%s_%s" % (self.username, self.service_name, self.version)
        
    def __repr(self):
        return self.full_name
    
    def to_dict(self):
        return {
            "notes" : self.notes,
            "service_name" : self.service_name,
            "runtime" : self.runtime,
            "entrypoint" : self.entrypoint,
            "create_time" : self.create_time,
            "update_time" : self.update_time,
            "version" : self.version,
        }
    
def prepare():
    db.drop_all()
    db.create_all()
    user = User(
        username='okapi', nickname='okapi', 
        email='okapi@okapi.site', password='okapi', 
        is_admin = True
    )
    
    user2 = User(
        username='lspvic', nickname='睡不着',
        email='lspvic@qq.com', password='lspvic',
        tel='17606529782'
    )
    
    admin_client = Client(
        name='admin_client', 
        client_id='admin_client',         
        client_type='confidential',
        _redirect_uris=(
            'http://localhost:8000/authorized '
            'http://localhost/authorized'
        ),
        user_id = 1,
        _default_scope = "admin",
        _allowed_grant_types = 'password',
    )

    manage_client = Client(
        name='manage_client', 
        client_id='manage_client',
        client_type='confidential',
        _redirect_uris=(
            'http://localhost:8000/authorized '
            'http://localhost/authorized'
        ),
        _default_scope = "manage",
        _allowed_grant_types = 'password',
        user_id = 1,
    )

    db.session.add(user)
    db.session.add(user2)
    db.session.add(admin_client)
    db.session.add(manage_client)
    db.session.commit()
        