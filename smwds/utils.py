# -*- coding: utf-8 -*-
"""
    Utils has nothing to do with models and views.
"""

import string
import random
import os

from datetime import datetime
from rauth.service import OAuth2Service

# Instance folder path, make it independent.
INSTANCE_FOLDER_PATH = os.path.join('/tmp', 'instance')

ALLOWED_AVATAR_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


# Model
STRING_LEN = 64

github = OAuth2Service(
    name='github',
    base_url='https://api.github.com/',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    client_id= '36a352b5ab807aa9d257',
    client_secret= 'fd6c364b6218244516711fd4b47c3a3683575801',
)

def get_current_time():
    return datetime.utcnow()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_AVATAR_EXTENSIONS


def id_generator(size=10, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def make_dir(dir_path):
    try:
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
    except Exception as e:
        raise e

def convert(data):
  if isinstance(data, bytes):      return data.decode()
  if isinstance(data, (str, int)): return str(data)
  if isinstance(data, dict):       return dict(map(convert, data.items()))
  if isinstance(data, tuple):      return tuple(map(convert, data))
  if isinstance(data, list):       return list(map(convert, data))
  if isinstance(data, set):        return set(map(convert, data))