# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc, func
from sqlalchemy.orm import backref
from sqlalchemy_utils import aggregated
from extensions import db
from utils import get_current_time
from api import Masterdb, Nodedb
from constants import SEX_TYPES, STRING_LEN


class Message(db.Model):

    __tablename__ = 'messages'

    id = Column(db.Integer, primary_key=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    receive_at = Column(db.DateTime)
    target = Column(db.String(STRING_LEN), nullable=False,
                    unique=True, index=True)
    is_read = Column(db.Boolean)


class Statistics(db.Model):

    __tablename__ = 'statistics'

    id = Column(db.Integer, primary_key=True)
    update_at = Column(db.DateTime)
    managed_nodes = Column(db.Integer, nullable=False, default=0)
    system_capacity = Column(db.Integer, nullable=False, default=0)
    system_utilization = Column(db.Float, nullable=False, default=0.0)
    user_count = Column(db.Integer, nullable=False, default=0.0)
    registered_master = Column(db.Integer, nullable=False, default=0)
    total_task = Column(db.Integer, nullable=False, default=0)
    service_level = Column(db.Integer, nullable=False, default=0)

    uptime = Column(db.DateTime, nullable=False, default=get_current_time)
    page_visit_count = Column(db.Integer, nullable=False, default=0)
    api_visit_count = Column(db.Integer, nullable=False, default=0)

    @staticmethod
    def update(cls):
        pass

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns([func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count

