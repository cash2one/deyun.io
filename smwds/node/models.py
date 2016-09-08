# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc, func
from sqlalchemy.orm import backref
from sqlalchemy_utils import aggregated
from sqlalchemy_utils import UUIDType
from extensions import db, cache
from utils import get_current_time
from api import Masterdb, Nodedb
from constants import STRING_LEN


class Perf(db.Model):

    __tablename__ = 'perf'

    id = Column(db.Integer, primary_key=True)
    node_id = Column(UUIDType(binary=False))
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True, info={'verbose_name': u'主机名', })
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    service = Column(db.String(STRING_LEN), nullable=False, default="other")
    result = Column(db.Boolean, nullable=False, default=True)
    value = Column(db.String(STRING_LEN), nullable=False, default="NONE")

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count

    @classmethod
    @cache.memoize(timeout=120)
    def get_perf(cls,n_name):

        r = cls.query.filter_by(result=True,node_name=n_name).statement.with_only_columns([func.count()]).order_by(None) 
        p = cls.query.filter_by(node_name=n_name).statement.with_only_columns([func.count()]).order_by(None) 
        result = (db.session.execute(r).scalar() + 1.0) / (db.session.execute(p).scalar() + 1.0)
        if result:
            return result
        else:
            return 0.0