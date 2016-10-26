# -*- coding: utf-8 -*-
import flask

from flask_sqlalchemy import SQLAlchemy
from flask import session

db = SQLAlchemy()

from flask_login import LoginManager
login_manager = LoginManager()

# https://docs.getsentry.com/hosted/clients/python/integrations/flask/
from raven.contrib.flask import Sentry
sentry = Sentry()

from flask_cache import Cache
cache = Cache()

import uuid
from flask_login import AnonymousUserMixin
class Anonymous(AnonymousUserMixin):
  def __init__(self):
    self.name = 'Guest'
    self.id = session.session_id

from celery import Celery

class FlaskCelery(Celery):

    def __init__(self, *args, **kwargs):

        super(FlaskCelery, self).__init__(*args, **kwargs)
        self.patch_task()

        if 'app' in kwargs:
            self.init_app(kwargs['app'])

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                if flask.has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
                else:
                    with _celery.app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app
        self.config_from_object(app.config)


celery = FlaskCelery()
