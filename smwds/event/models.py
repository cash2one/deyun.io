# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc
from sqlalchemy.orm import backref

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin

from extensions import db
from utils import get_current_time
from constants import USER, USER_ROLE, ADMIN, INACTIVE, USER_STATUS, \
    SEX_TYPES, STRING_LEN