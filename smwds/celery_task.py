#!/usr/bin/python
#coding:utf-8

from celery import Celery, platforms
from flask import Flask, current_app
import random, time, json, redis, time, logging, base64
from app import create_celery_app
from celery.signals import task_prerun
from datetime import timedelta
from celery.schedules import crontab
from weblib.libpepper import Pepper
from weblib.indbapi import Indb
from weblib.sensuapi import SensuAPI
from node import Perf, Perf_Node, Perf_Cpu, Perf_Mem, Perf_TCP, Perf_Disk, Perf_System_Load, Perf_Socket, Perf_Process_Count, Perf_Netif, Perf_Ping
from api import Masterdb, Nodedb, Location
from collections import defaultdict
try:
    from prod import config
except:
    pass
from functools import wraps
from utils import convert

logger = logging.getLogger('task')

#celery_app = Flask(__name__)

#celery_app.config.from_pyfile('prod.py', silent=True)

#indbapi = Indb(app.config['INDB_HOST'] + ':' + app.config['INDB_PORT'])

#sensuapi = SensuAPI(app.config['SENSU_HOST'] + ':' + app.config['SENSU_PORT'])


celery, session = create_celery_app()

celery.config_from_object('prod', silent=True)

indbapi = Indb(config['INDB_HOST'] + ':' + config['INDB_PORT'])

sensuapi = SensuAPI(config['SENSU_HOST'] + ':' + config['SENSU_PORT'])

master = session.query(Masterdb).first()
try:
    saltapi = Pepper(master.ret_api())
    user = master.username
    pawd = convert(base64.b64decode(master.password))
except:
    saltapi = Pepper(config['SALTAPI_HOST'])
    user = config['SALTAPI_USER']
    pawd = config['SALTAPI_PASS']

redisapi = redis.StrictRedis(host=config['REDIS_HOST'], port=config['REDIS_PORT'], db=config['REDIS_DB'])


'''
def make_celery(app):
    celery = Celery(celery_app.__class__)
    platforms.C_FORCE_ROOT = True
    # load setting.py config
    celery.config_from_object('celery_config')

    #celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with celery_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return (app,celery)

app, celery = make_celery(app)
app.create_app().app_context().push()
'''
def salttoken(loginresult=None):
    if redisapi.hexists(name='salt',key='token'):
        if (time.time() - float(bytes.decode(redisapi.hget(name='salt', key='expire')))) < 0.0:
            ret = redisapi.hget(name='salt',key='token')
            return convert(ret)
        else:
            return salttoken(saltapi.login(user, pawd, 'pam'))
    if loginresult:
        for k in loginresult.keys():
            redisapi.hset(name='salt', key=k, value=loginresult[k])
    return salttoken()

def salt_command(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        try:
            saltkey = salttoken()
            saltapi.auth['token'] = saltkey
            return f(*args, **kwds)
        except Exception as e:
            return {'failed': e}
    return wrapper

@celery.task
@salt_command
def salt_minion_status():
    try:
        ret = saltapi.runner('manage.status')
        result = []
        count = 0
        if len(ret['return'][0]['up']) > 0:
            for node in ret['return'][0]['up']:
                count += redisapi.hset(name='status', key=node, value='up')
                result.append(node)
        if len(ret['return'][0]['down']) > 0:
            for node in ret['return'][0]['down']:
                count += redisapi.hset(name='status', key=node, value='down')
                result.append(node)
    except Exception as e:
        return {'failed': e}
    return {'ok': str(result) + ' updated with redis return: ' + str(count)}

@celery.task
@salt_command
def salt_api_status():
    try:
        ret = saltapi.req_get(path='stats')
    except Exception as e :
        return {'failed' : e}
    return ret



@celery.task
def hello_world(x=16, y=16):
    x = int(x)
    y = int(y)
    res = add.apply_async((x, y))
    context = {"id": res.task_id, "x": x, "y": y}
    result = "add((x){}, (y){})".format(context['x'], context['y'])
    goto = "{}".format(context['id'])
    return json.dumps({'result':result, 'goto':goto})

@celery.task
def sync_node_from_influxdb():
    try:
        data = sensuapi.get('clients')
        result =[]
    except Exception as e:
        return {'failed' : e}
    for item in data:
        try:
            sensunode = session.query(Perf_Node).filter_by(sensu_node_name=item["name"]).first()
        except Exception as e:
            return {'failed' : e}
        try:
            if sensunode :
                sensunode.sensu_subscriptions = item["address"]
                sensunode.sensu_version = item["version"]
                sensunode.sensu_timestamp = item["timestamp"]
                result.append(sensunode)
            else:
                sensunode = Perf_Node(
                        sensu_node_name = item["name"],
                        sensu_subscriptions = item["address"],
                        sensu_version = item["version"],
                        sensu_timestamp = item["timestamp"]
                        )
                result.append(sensunode)
        except Exception as e:
            return {'failed' : e}
        session.add(sensunode)
    try:
        session.commit()
    except Exception as e:
        return {'failed' : e}

    return {'successed' : result}

@celery.task
def sync_praser_data(data):
    result = defaultdict(list)
    for row in data:
        for item in row:
            result[item['tags']['host']].append(item['values'][0][1])
    return result

@celery.task
def sync_cpu_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('cpu_user'))
    praser.append(indbapi.get_sync_data('cpu_nice'))
    praser.append(indbapi.get_sync_data('cpu_system'))
    praser.append(indbapi.get_sync_data('cpu_idle'))
    praser.append(indbapi.get_sync_data('cpu_iowait'))
    praser.append(indbapi.get_sync_data('cpu_irq'))
    praser.append(indbapi.get_sync_data('cpu_softirq'))
    praser.append(indbapi.get_sync_data('cpu_steal'))
    praser.append(indbapi.get_sync_data('cpu_guest'))
    #return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
    try:
        for (k,v) in data.items():
            target_node = Perf_Cpu(
            node_name=k,
            cpu_user=v[0],
            cpu_nice=v[1],
            cpu_system=v[2],
            cpu_idle=v[3],
            cpu_iowait=v[4],
            cpu_irq=v[5],
            cpu_softirq=v[6],
            cpu_steal=v[7],
            cpu_guest=v[8],  
                )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' + str((k,v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Cpu'+ str(data))
    return {'successed': result}

@celery.task
def sync_mem_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('memory_percent_usedWOBuffersCaches'))
    praser.append(indbapi.get_sync_data('memory_percent_freeWOBuffersCaches'))
    praser.append(indbapi.get_sync_data('memory_percent_swapUsed'))
    praser.append(indbapi.get_sync_data('memory_percent_free'))
    #return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
    try:
        for (k,v) in data.items():
            target_node = Perf_Mem(
            node_name=k,
            mem_usedWOBuffersCaches=v[0],
            mem_freeWOBuffersCaches=v[1],
            mem_swapUsed=v[2] 
                )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' + str((k,v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Mem'+ str(data))
    return {'successed': result}

@celery.task
def sync_tcp_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('tcp_UNKNOWN'))
    praser.append(indbapi.get_sync_data('tcp_ESTABLISHED'))
    praser.append(indbapi.get_sync_data('tcp_SYN_SENT'))
    praser.append(indbapi.get_sync_data('tcp_SYN_RECV'))
    praser.append(indbapi.get_sync_data('tcp_FIN_WAIT1'))
    praser.append(indbapi.get_sync_data('tcp_FIN_WAIT2'))
    praser.append(indbapi.get_sync_data('tcp_CLOSE'))
    praser.append(indbapi.get_sync_data('tcp_CLOSE_WAIT'))
    praser.append(indbapi.get_sync_data('tcp_LAST_ACK'))
    praser.append(indbapi.get_sync_data('tcp_LISTEN'))
    praser.append(indbapi.get_sync_data('tcp_CLOSING'))
    #return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
    try:
        for (k,v) in data.items():
            target_node = Perf_TCP(
            node_name=k,
            tcp_UNKNOWN=v[0],
            tcp_ESTABLISHED=v[1],
            tcp_SYN_SENT=v[2],
            tcp_SYN_RECV=v[3],
            tcp_FIN_WAIT1=v[4],
            tcp_FIN_WAIT2=v[5],
            tcp_CLOSE=v[6],
            tcp_CLOSE_WAIT=v[7],
            tcp_LAST_ACK=v[8],
            tcp_LISTEN=v[9],
            tcp_CLOSING=v[10],   
                )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' + str((k,v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Tcp'+ str(data))
    return {'successed': result}

@celery.task
def sync_disk_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('disk_usage_root_used'))
    praser.append(indbapi.get_sync_data('disk_usage_root_avail'))
    praser.append(indbapi.get_sync_data('disk_usage_root_used_percentage'))
    #return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
    try:
        for (k,v) in data.items():
            target_node = Perf_Disk(
            node_name=k,
            disk_usage_root_used=v[0],
            disk_usage_root_avail=v[1],
            disk_usage_root_used_percentage=v[2] 
                )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' + str((k,v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Disk'+ str(data))
    return {'successed': result}

@celery.task
def sync_load_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('load_load_avg_one'))
    praser.append(indbapi.get_sync_data('load_load_avg_five'))
    praser.append(indbapi.get_sync_data('load_load_avg_fifteen'))
    #return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
    try:
        for (k,v) in data.items():
            target_node = Perf_System_Load(
            node_name=k,
            load_avg_one=v[0],
            load_avg_five=v[1],
            load_avg_fifteen=v[2] 
                )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' + str((k,v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Load'+ str(data))
    return {'successed': result}

@celery.task
def sync_socket_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('sockets_total_used'))
    praser.append(indbapi.get_sync_data('sockets_TCP_inuse'))
    praser.append(indbapi.get_sync_data('sockets_TCP_orphan'))
    praser.append(indbapi.get_sync_data('sockets_TCP_tw'))
    praser.append(indbapi.get_sync_data('sockets_TCP_alloc'))
    praser.append(indbapi.get_sync_data('sockets_TCP_mem'))
    praser.append(indbapi.get_sync_data('sockets_UDP_inuse'))
    praser.append(indbapi.get_sync_data('sockets_UDP_mem'))
    praser.append(indbapi.get_sync_data('sockets_UDPLITE_inuse'))
    praser.append(indbapi.get_sync_data('sockets_RAW_inuse'))
    praser.append(indbapi.get_sync_data('sockets_RAW_inuse'))
    praser.append(indbapi.get_sync_data('sockets_FRAG_memory'))
    # return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
    try:
        for (k, v) in data.items():
            target_node = Perf_Socket(
                node_name=k,
                sockets_total_used=v[0],
                sockets_TCP_inuse=v[1],
                sockets_TCP_orphan=v[2],
                sockets_TCP_tw=v[3],
                sockets_TCP_alloc=v[4],
                sockets_TCP_mem=v[5],
                sockets_UDP_inuse=v[6],
                sockets_UDP_mem=v[7],
                sockets_UDPLITE_inuse=v[8],
                sockets_RAW_inuse=v[9],
                sockets_FRAG_inuse=v[10],
                sockets_FRAG_memory=v[10],
            )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' +
                       str((k, v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Socket'+ str(data))
    return {'successed': result}

@celery.task
def sync_process_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('process_count'))
    # return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
    try:
        for (k, v) in data.items():
            target_node = Perf_Process_Count(
                node_name=k,
                process_count=v[0]
            )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' +
                       str((k, v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Process_count'+ str(data))
    return {'successed': result}

@celery.task
def sync_netif_from_influxdb(netif='eth0'):
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('net_'+ netif +'_tx_bytes'))
    praser.append(indbapi.get_sync_data('net_' + netif +'_rx_bytes'))
    praser.append(indbapi.get_sync_data('net_' + netif +'_tx_packets'))
    praser.append(indbapi.get_sync_data('net_' + netif +'_rx_packets'))
    praser.append(indbapi.get_sync_data('net_' + netif +'_tx_errors'))
    praser.append(indbapi.get_sync_data('net_' + netif +'_if_speed'))
    try:
        data = sync_praser_data(praser)
        #return sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
        return
    try:
        for (k, v) in data.items():
            target_node = Perf_Netif(
                node_name=k,
                netif=netif,
                netif_tx_bytes=v[0],
                netif_rx_bytes=v[1],
                netif_tx_packets=v[2],
                netif_rx_packets=v[3],
                netif_rx_errors=v[4],
                netif_speed=v[5]
            )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' +
                       str((k, v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_netif')
    return {'successed': result}

@celery.task
def sync_ping_from_influxdb(node='master'):
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('ping_'+ node +'_packet_loss'))
    praser.append(indbapi.get_sync_data('ping_'+ node +'_avg'))
    try:
        data = sync_praser_data(praser)
        #return sync_praser_data(praser)
    except Exception as e:
        logger.error('error while prasering data from influx db: ' + str(praser))
        return
    try:
        for (k, v) in data.items():
            target_node = Perf_Ping(
                node_name=k,
                ping_target=node,
                ping_packet_loss=v[0],
                ping_avg=v[1]
            )
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('error in creating data ' +
                       str((k, v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_ping' + str(result))
    return {'successed': result}

@celery.task
def salt_mark_status(k,v):
    target_node = session.query(
                Nodedb).filter_by(node_name=k).first()
    if target_node:
        target_node.status = v
    else:
        target_node =  Nodedb(
                id=uuid.uuid4(),
                node_name=k,
                node_ip=u'1.1.1.1',
                bio=u'Down',
                master=master,
                status=v
                )
    session.add(target_node)
    session.commit()



@celery.task
@salt_command
def salt_nodes_sync():
    result = []
    count = 0
    data = redisapi.hgetall(name='status')
    try:
        for (k, v) in convert(data).items():
            if v == 'down':
                salt_mark_status(k, v)
                continue
            target_node = session.query(
                Nodedb).filter_by(node_name=k).first()
            node_data = salt_minion(k)
            db_data = node_data['return'][0][k]
            try:
                if target_node:
                    target_node.minion_data = db_data
                    target_node.node_ip=db_data.get('ipv4','1.1.1.1'),
                    target_node.os = db_data.get('lsb_distrib_description') or (
                        db_data.get('lsb_distrib_id') + db_data.get('lsb_distrib_release')) or (db_data.get('osfullname') + db_data('osrelease'))
                    target_node.cpu = str(db_data[
                        'num_cpus']) + ' * ' + str(db_data['cpu_model'])
                    target_node.kenel = db_data['kernelrelease']
                    target_node.mem = db_data['mem_total']
                    target_node.host = db_data['host']
                    target_node.status = v
                    target_node.master = master
                else:
                    target_node = Nodedb(
                        id=uuid.uuid4(),
                        node_name=db_data['id'],
                        node_ip=db_data.get('ipv4','1.1.1.1'),
                        minion_data=db_data,
                        os=db_data.get('lsb_distrib_description') or (
                        db_data.get('lsb_distrib_id') + db_data.get('lsb_distrib_release')) or (db_data.get('osfullname') + db_data('osrelease')),
                        cpu=str(db_data['num_cpus']) + ' * ' +
                        str(db_data['cpu_model']),
                        kenel=db_data['kernelrelease'],
                        mem=db_data['mem_total'],
                        host=db_data['host'],
                        master=master,
                        status=v
                    )
            except KeyError as e:
                logger.warning('updating ' + k + ' with error:' + str(e.args))
                continue
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warning('Error while updaing ' + db_data['id'] + str(e.args))
    session.commit()

    return {'ok': str(result) + ' updated with redis return: ' + str(count)}


