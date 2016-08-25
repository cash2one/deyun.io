# -*- coding: utf-8 -*-

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

