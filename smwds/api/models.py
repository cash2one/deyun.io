# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc, func
from sqlalchemy.orm import backref

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin

from extensions import db, cache
from utils import get_current_time
from constants import USER, USER_ROLE, ADMIN, INACTIVE, USER_STATUS, \
    SEX_TYPES, STRING_LEN
from sqlalchemy_utils import UUIDType,  JSONType
from flask_sqlalchemy import Pagination
import uuid

class Masterdb(db.Model):
    __tablename__ = 'masterdb'

    def __repr__(self):
        return '<Master APi %r>' % self.master_name

    #id = Column(db.Integer, primary_key=True)
    id = Column(UUIDType(binary=False), primary_key=True)
    master_name = Column(db.String(STRING_LEN), nullable=False,
                         unique=True, index=True, info={'verbose_name': u'主机名', })
    master_ip = Column(db.String(STRING_LEN), nullable=False,
                       unique=False, info={'verbose_name': u'主机IP', })
    master_port = Column(db.String(STRING_LEN), nullable=False,
                         default="", info={'verbose_name': u'主机端口', })
    master_api_url = Column(db.String(STRING_LEN), nullable=False, default="", info={
                            'verbose_name': u'主机API地址', })
    master_api_port = Column(db.Integer, nullable=False, default=0, info={
                             'verbose_name': u'主机API端口', })
    username = Column(db.String(STRING_LEN),  nullable=False, default='salt')
    password = Column(db.String(STRING_LEN),  nullable=False, default='sugar')
    #location = Column(db.String(STRING_LEN), nullable=False, default="")
    location_id = Column(UUIDType(binary=False), db.ForeignKey(
        'location.id'), nullable=False, default="", info={'verbose_name': u'提供商', })
    location = db.relationship('Location', backref='masters')
    bio = Column(db.Text, default="", info={'verbose_name': u'备注', })
    ssh_key = Column(db.String(STRING_LEN))
    create_at = Column(db.DateTime, nullable=False, default=get_current_time, info={
                       'verbose_name': u'创建时间', })
    update_at = Column(db.DateTime, info={'verbose_name': u'更新时间', })
    operator = Column(UUIDType(binary=False), nullable=True,
                      info={'verbose_name': u'Master', })
    avatar = Column(db.String(STRING_LEN), nullable=False, default='')
    token = Column(db.String(STRING_LEN), nullable=False, default='')
    token_expire = Column(db.Float, nullable=False, default=0.0)
    minion_data = Column(JSONType(1000), nullable=False, default='')

    def ret_api(self):
        #return self.master_api_url + ":" + str(self.master_api_port)
        return self.master_api_url
    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count

    @classmethod
    def get_list(cls, page=1):
        q = cls.query.order_by(cls.update_at.desc())
        return cls.paginate(query=q, page=page)

    @staticmethod
    def paginate(query, page, per_page=20, error_out=False):
        if error_out and page < 1:
            abort(404)
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)

        # No need to count if we're on the first page and there are fewer
        # items than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = query.order_by(None).count()

        return Pagination(query, page, per_page, total, items)
'''
Tag = server role
'''

class Tag(db.Model):

    __tablename__ = 'tag'

    def __repr__(self):
        return '<Tag %r>' % self.name

    id = Column(db.Integer, primary_key=True)
    node_id = Column(UUIDType(binary=False), db.ForeignKey('nodedb.id'))
    node = db.relationship('Nodedb', backref='tags',foreign_keys="Tag.node_id")
    name = Column(db.String(STRING_LEN), nullable=False,
                  default='', info={'verbose_name': u'名称', })
    type = Column(db.String(STRING_LEN), nullable=False,
                  default='', info={'verbose_name': u'类型', })
    url = Column(db.String(STRING_LEN), nullable=False, default='')


class Location(db.Model):
    id = Column(UUIDType(binary=False), primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False,
                  default='', info={'verbose_name': u'名称', })
    type = Column(db.String(STRING_LEN), nullable=False,
                  default='', info={'verbose_name': u'类型', })
    bandwidth = Column(db.String(STRING_LEN), nullable=False,
                       default='', info={'verbose_name': u'带宽', })
    avatar = Column(db.String(STRING_LEN), nullable=False, default='')
    address = Column(db.String(STRING_LEN), nullable=False,
                     default='', info={'verbose_name': u'网址', })


class Nodedb(db.Model):

    __tablename__ = 'nodedb'

    def __repr__(self):
        return '<node %r>' % self.node_name

    #id = Column(db.Integer, primary_key=True)
    id = Column(UUIDType(binary=False), default=uuid.uuid4, primary_key=True)
    node_name = Column(db.String(STRING_LEN), nullable=False,
                       unique=True, index=True, info={'verbose_name': u'Node名', })
    #node_ip = Column(db.String(STRING_LEN), nullable=False,
    #                 unique=False, info={'verbose_name': u'Node IP', })
    node_ip = Column(JSONType(10000), nullable=False, default='')
    node_port = Column(db.String(STRING_LEN), nullable=False,
                       default="", info={'verbose_name': u'Node 端口', })
    username = Column(db.String(STRING_LEN),  nullable=False, default='salt')
    password = Column(db.String(STRING_LEN),  nullable=False, default='sugar')
    #location = Column(db.String(STRING_LEN), nullable=False, default="")
    #location_id = Column(UUIDType(binary=False), db.ForeignKey(
    #    'location.id'), nullable=False, default="", info={'verbose_name': u'提供商', })
    #location = db.relationship('Location', backref='nodes')
    bio = Column(db.Text, default="", info={'verbose_name': u'备注', })
    ssh_key = Column(db.String(STRING_LEN))
    create_at = Column(db.DateTime, nullable=False, default=get_current_time, info={
                       'verbose_name': u'创建时间', })
    update_at = Column(db.DateTime, info={'verbose_name': u'更新时间', })
    master_id = Column(UUIDType(binary=False), db.ForeignKey(
        'masterdb.id'), nullable=False, default="", info={'verbose_name': u'Master', })
    master = db.relationship('Masterdb', backref='nodes')
    avatar = Column(db.String(STRING_LEN), nullable=False, default='')
    minion_data = Column(JSONType(10000), nullable=False, default='')
    os = Column(db.String(STRING_LEN), nullable=False, default='')
    kenel = Column(db.String(STRING_LEN), nullable=False, default='')
    core = Column(db.Integer, nullable=False, default=0)
    cpu = Column(db.String(STRING_LEN), nullable=False, default='')
    mem  = Column(db.String(STRING_LEN), nullable=False, default='')
    host = Column(db.String(STRING_LEN), nullable=False, default='')
    status = Column(db.String(STRING_LEN), nullable=False, default='')

    @classmethod
    def get_nodes(cls):
        q = cls.query.with_entities(cls.node_name).all()
        return q

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count

    @classmethod
    def get_list(cls, page=1):
        q = cls.query.order_by(cls.update_at.desc())
        return cls.paginate(query=q, page=page)

    @staticmethod
    def paginate(query, page, per_page=20, error_out=False):
        if error_out and page < 1:
            abort(404)
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)

        # No need to count if we're on the first page and there are fewer
        # items than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = query.order_by(None).count()

        return Pagination(query, page, per_page, total, items)
