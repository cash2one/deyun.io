# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc
from sqlalchemy.orm import backref

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin

from extensions import db
from utils import get_current_time
from constants import USER, USER_ROLE, AD(MIN, INACTIVE, USER_STATUS, \
    SEX_TYPES, STRING_LEN
from sqlalchemy_utils import UUIDType



class apidb(db.Model):
    __tablename__ = 'api'

    def __repr__(self):
      return '<Master APi %r>' % self.master_name

    #id = Column(db.Integer, primary_key=True)
    id = Column(UUIDType(binary=False), primary_key=True)
    master_name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    master_ip = Column(db.String(STRING_LEN), nullable=False, unique=True)
    master_port = Column(db.String(STRING_LEN), nullable=False, default="")
    master_api_url = Column(db.String(STRING_LEN), nullable=False, default="")
    master_api_port  = Column(db.Integer, nullable=False, default=0)
    location = Column(db.String(STRING_LEN), nullable=False, default="")
    bio = Column(db.Text, default="")
    ssh_key = Column(db.String(STRING_LEN))
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    update_at = Column(db.DateTime)
    operator = Column(UUIDType(binary=False), nullable=True, info={verbose_name : u'Master',})
    avatar = Column(db.String(STRING_LEN))

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)

class location(db.Model):
    uuid = Column(UUIDType(binary=False), primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, default='', info={verbose_name : u'名称',})
    type = Column(db.String(STRING_LEN), nullable=False, default='', info={verbose_name : u'类型',})
    bandwidth = Column(db.String(STRING_LEN), nullable=False, default='', info={verbose_name : u'带宽',})
    avatar = Column(db.String(STRING_LEN))
    address = Column(db.String(STRING_LEN), nullable=False, default='', info={verbose_name : u'网址',})
    