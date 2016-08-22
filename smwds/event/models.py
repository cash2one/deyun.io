# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc
from sqlalchemy.orm import backref


from extensions import db
from utils import get_current_time

class Message(db.Model)

    __tablename__ = 'messages'

    id = Column(db.Integer, primary_key=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    receive_at = Column(db.DateTime)
    target = Column(db.String(STRING_LEN), nullable=False, unique=True,index=True)    
    is_read = Column(db.Boolean)

class Statistics(db.model)

    __tablename__ = 'statistics'

    id = Column(db.Integer, primary_key=True)
    update_at = Column(db.DateTime)
    current_task = Column(db.Integer, nullable = False, default = 0)
    total_task = Column(db.Integer, nullable = False, default = 0)
    managed_nodes = Column(db.Integer, nullable = False, default = 0)
    registered_master = Column(db.Integer, nullable = False, default = 0)
    uptime = Column(db.DateTime, nullable=False, default=get_current_time)
    page_visit_count = Column(db.Integer, nullable = False, default = 0)
    api_visit_count = Column(db.Integer, nullable = False, default = 0)
    


