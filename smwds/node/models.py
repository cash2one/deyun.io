# -*- coding: utf-8 -*-

from sqlalchemy import Column, desc, func
from sqlalchemy.orm import backref
from sqlalchemy_utils import aggregated
from sqlalchemy_utils import UUIDType
from sqlalchemy_utils import ScalarListType
from extensions import db, cache
from utils import get_current_time
from api.models import Masterdb, Nodedb
from constants import STRING_LEN


class Perf(db.Model):

    __tablename__ = 'perf'

    id = Column(db.Integer, primary_key=True)
    node_id = Column(UUIDType(binary=False))
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
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
    def get_perf(cls, n_name):

        r = cls.query.filter_by(result=True, node_name=n_name).statement.with_only_columns(
            [func.count()]).order_by(None)
        p = cls.query.filter_by(node_name=n_name).statement.with_only_columns(
            [func.count()]).order_by(None)
        result = (db.session.execute(r).scalar() + 1.0) / \
            (db.session.execute(p).scalar() + 1.0)
        if result:
            return result
        else:
            return 0.0


class Perf_Node(db.Model):
    __tablename__ = 'perf_sensu_nodes'

    def __repr__(self):
        return '<sensu_node %r>' % self.sensu_node_name

    id = Column(db.Integer, primary_key=True)
    sensu_node_name = Column(db.String(255), nullable=False,
                             unique=False, index=True)
    sensu_subscriptions = Column(ScalarListType(), nullable=False,
                                 unique=False)
    sensu_version = Column(db.String(255), nullable=False,
                           unique=False)
    sensu_timestamp = Column(db.Integer, nullable=False,
                             unique=False, default=0)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'sensu_node_name': dump_datetime(self.modified_at),
            # This is an example how to deal with Many2Many relations
            'many2many': self.serialize_many2many
        }

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_Cpu(db.Model):
    __tablename__ = 'perf_monitor_data_cpu'

    def __repr__(self):
        return '<cpu_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    cpu_user = Column(db.Float, nullable=False, default=0.0)
    cpu_nice = Column(db.Float, nullable=False, default=0.0)
    cpu_system = Column(db.Float, nullable=False, default=0.0)
    cpu_idle = Column(db.Float, nullable=False, default=0.0)
    cpu_iowait = Column(db.Float, nullable=False, default=0.0)
    cpu_irq = Column(db.Float, nullable=False, default=0.0)
    cpu_softirq = Column(db.Float, nullable=False, default=0.0)
    cpu_steal = Column(db.Float, nullable=False, default=0.0)
    cpu_guest = Column(db.Float, nullable=False, default=0.0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_Mem(db.Model):
    __tablename__ = 'perf_monitor_data_mem'

    def __repr__(self):
        return '<mem_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    mem_usedWOBuffersCaches = Column(db.Float, nullable=False, default=0.0)
    mem_freeWOBuffersCaches = Column(db.Float, nullable=False, default=0.0)
    mem_swapUsed = Column(db.Float, nullable=False, default=0.0)
    mem_free = Column(db.Float, nullable=False, default=0.0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_TCP(db.Model):
    __tablename__ = 'perf_monitor_data_tcp'

    def __repr__(self):
        return '<tcp_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    tcp_UNKNOWN = Column(db.Float, nullable=False, default=0.0)
    tcp_ESTABLISHED = Column(db.Float, nullable=False, default=0.0)
    tcp_SYN_SENT = Column(db.Float, nullable=False, default=0.0)
    tcp_SYN_RECV = Column(db.Float, nullable=False, default=0.0)
    tcp_FIN_WAIT1 = Column(db.Float, nullable=False, default=0.0)
    tcp_FIN_WAIT2 = Column(db.Float, nullable=False, default=0.0)
    tcp_CLOSE = Column(db.Float, nullable=False, default=0.0)
    tcp_CLOSE_WAIT = Column(db.Float, nullable=False, default=0.0)
    tcp_LAST_ACK = Column(db.Float, nullable=False, default=0.0)
    tcp_LISTEN = Column(db.Float, nullable=False, default=0.0)
    tcp_CLOSING = Column(db.Float, nullable=False, default=0.0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_Disk(db.Model):
    __tablename__ = 'perf_monitor_data_disk'

    def __repr__(self):
        return '<disk_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    disk_usage_root_used = Column(db.Float, nullable=False, default=0.0)
    disk_usage_root_avail = Column(db.Float, nullable=False, default=0.0)
    disk_usage_root_used_percentage = Column(
        db.Float, nullable=False, default=0.0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_System_Load(db.Model):
    __tablename__ = 'perf_monitor_data_system_load'

    def __repr__(self):
        return '<sys_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    load_avg_one = Column(db.Float, nullable=False, default=0.0)
    load_avg_five = Column(db.Float, nullable=False, default=0.0)
    load_avg_fifteen = Column(db.Float, nullable=False, default=0.0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_Socket(db.Model):
    __tablename__ = 'perf_monitor_data_socket'

    def __repr__(self):
        return '<socket_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    sockets_total_used = Column(db.Integer, nullable=False, default=0)
    sockets_TCP_inuse = Column(db.Integer, nullable=False, default=0)
    sockets_TCP_orphan = Column(db.Integer, nullable=False, default=0)
    sockets_TCP_tw = Column(db.Integer, nullable=False, default=0)
    sockets_TCP_alloc = Column(db.Integer, nullable=False, default=0)
    sockets_TCP_mem = Column(db.Integer, nullable=False, default=0)
    sockets_UDP_inuse = Column(db.Integer, nullable=False, default=0)
    sockets_UDP_mem = Column(db.Integer, nullable=False, default=0)
    sockets_UDPLITE_inuse = Column(db.Integer, nullable=False, default=0)
    sockets_RAW_inuse = Column(db.Integer, nullable=False, default=0)
    sockets_FRAG_inuse = Column(db.Integer, nullable=False, default=0)
    sockets_FRAG_memory = Column(db.Integer, nullable=False, default=0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_Process_Count(db.Model):
    __tablename__ = 'perf_monitor_data_process_count'

    def __repr__(self):
        return '<proc_count_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    process_count = Column(db.Integer, nullable=False, default=0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_Netif(db.Model):
    __tablename__ = 'perf_monitor_data_netif'

    def __repr__(self):
        return '<netif_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    netif = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    netif_tx_bytes = Column(db.BigInteger, nullable=False, default=0)
    netif_rx_bytes = Column(db.BigInteger, nullable=False, default=0)
    netif_rx_errors = Column(db.BigInteger, nullable=False, default=0)
    netif_rx_packets = Column(db.BigInteger, nullable=False, default=0)
    netif_tx_packets = Column(db.BigInteger, nullable=False, default=0)
    netif_speed = Column(db.BigInteger, nullable=False, default=0)

    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count


class Perf_Ping(db.Model):
    __tablename__ = 'ping_monitor_data_ping'

    def __repr__(self):
        return '<ping_monitor_data %r>' % self.node_name

    id = Column(db.Integer, primary_key=True)
    node_name = Column(db.String(255), nullable=False,
                       unique=False, index=True)
    create_at = Column(db.DateTime, nullable=False, default=get_current_time)
    ping_target = Column(db.String(255), nullable=False,
                         unique=False, index=True)
    ping_packet_loss = Column(db.Integer, nullable=False, default=0)
    ping_avg = Column(db.Float, nullable=False, default=0.0)


    @classmethod
    def get_count(cls):
        count_q = cls.query.statement.with_only_columns(
            [func.count()]).order_by(None)
        count = db.session.execute(count_q).scalar()
        return count
