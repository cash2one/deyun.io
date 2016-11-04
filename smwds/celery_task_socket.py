 #!/usr/bin/python
#coding:utf-8


from celery import Celery, platforms
from flask import Flask, current_app
import random, time, json, redis, time, logging, base64
from celery.signals import task_prerun
from datetime import timedelta
from celery.schedules import crontab
from weblib.libpepper import Pepper
from weblib.indbapi import Indb
from weblib.sensuapi import SensuAPI
from node import Perf, Perf_Node, Perf_Cpu, Perf_Mem, Perf_TCP, Perf_Disk, Perf_System_Load, Perf_Socket, Perf_Process_Count, Perf_Netif, Perf_Ping, Statistics
from api import Masterdb, Nodedb, Location
from user import User
from collections import defaultdict
from datetime import datetime
from sqlalchemy.sql import func
try:
    from prod import config
except:
    pass
from functools import wraps
from utils import convert
from extensions import celery,db
from requests import post
from flask_socketio import SocketIO

#import app
#tapp,session = app.create_socket_celery()
#celery.init_app(tapp)



celery.config_from_object('celery_socket_config')

logger = logging.getLogger('task')

#celery, session = create_celery_app()

#celery.config_from_object('prod', silent=True)
#load config from celery_config.py , store other api information in prod.py


indbapi = Indb(config['INDB_HOST'] + ':' + config['INDB_PORT'])

sensuapi = SensuAPI(config['SENSU_HOST'] + ':' + config['SENSU_PORT'])

#master = session.query(Masterdb).first()
#try:
#    saltapi = Pepper(master.ret_api())
#    user = master.username
#    pawd = convert(base64.b64decode(master.password))
#except:
saltapi = Pepper(config['SALTAPI_HOST'])
user = config['SALTAPI_USER']
pawd = config['SALTAPI_PASS']

redisapi = redis.StrictRedis(host=config['REDIS_HOST'], port=config['REDIS_PORT'], db=config['REDIS_DB'])


'''
### DOC ###

Celery function description

*self test*


### END ###
'''

def ret_master():
     master = db.session.query(Masterdb).first()
     return master

def socket_emit(meta=None, event='others'):
    try:
        socketio = SocketIO(message_queue=current_app.config['SOCKETIO_REDIS_URL'])
        socketio.emit(event, meta, namespace='/deyunio')
    except Exception as e:
        logger.warning('error in loading sitestatus ' + str(e))
        return {'failed': e}
    return {("sent " + str(event)) : meta}


@celery.task
def self_test(x=16, y=16,url=None):
    x = int(x)
    y = int(y)
    res = x + y
    context = {"id": "test", "x": x, "y": y}
    result = "add((x){}, (y){})".format(context['x'], context['y'])
    goto = "{}".format(context['id'])
    time.sleep(10)
    meta = json.dumps({'result':result, 'goto':goto})
    #post(url, json=meta)
    socketio = SocketIO(message_queue='redis://localhost:6379/0')
    socketio.emit('connect', meta, namespace='/deyunio')
    return meta

@celery.task
def emit_site_status():
    try:
        data = convert(redisapi.hgetall('sitestatus'))
    except Exception as e :
        logger.warning('error in loading sitestatus ')
        return {'failed': e}
    meta = json.dumps(data)
    socket_emit(meta = meta, event='sitestatus')


'''
### DOC ###

Celery function description

*to obtain token from saltstack api, based on pepper*


### END ###
'''
def salttoken():
    try:
        if redisapi.hexists(name='salt', key='token'):
            if (time.time() - float(bytes.decode(redisapi.hget(name='salt', key='expire')))) < 0.0:
                ret = redisapi.hget(name='salt', key='token')
                return convert(ret)
            else:
                return saltlogin(saltapi.login(user, pawd, 'pam'))
        else:
            return saltlogin(saltapi.login(user, pawd, 'pam'))
    except Exception as e:
        return {'falid': e}


def saltlogin(loginresult=None):
    if loginresult:
        for k in loginresult.keys():
            redisapi.hset(name='salt', key=k, value=loginresult[k])
    else:
        raise Exception('require login string')
    return salttoken()

'''
### DOC ###

Celery function description

*salt api wraper for saltstack api, token stored in redis cache and tries to reflash when expired*


### END ###
'''

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

'''
### DOC ###

Celery function description

*Get minion status from saltstack api and store in redis cache*


### END ###
'''
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


'''
### DOC ###

Celery function description

*check saltstack api status*


### END ###
'''
@celery.task
@salt_command
def salt_api_status():
    try:
        ret = saltapi.req_get(path='stats')
    except Exception as e :
        return {'failed' : e}
    return ret


'''
### DOC ###

Celery function description

*update status subtask when syncing*


### END ###
'''
@salt_command
def salt_minion(node_name):
    try:
        ret = saltapi.req_get('/minions/' + node_name)
    except Exception as e:
        return {'failed': e}
    return ret

@celery.task
def salt_mark_status(k,v):
    target_node = db.session.query(
                Nodedb).filter_by(node_name=k).first()
    master = ret_master()
    #TODO
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
    db.session.add(target_node)
    db.session.commit()

'''
### DOC ###

Celery function description

*search the cmdb first the tries to update information when available*
this task based on the result of salt_minion_status, may return none


### END ###
'''



@celery.task
@salt_command
def salt_nodes_sync():
    result = []
    count = 0
    data = redisapi.hgetall(name='status')
    if not data:
        return {'failed': 'no status data in redis cache '}
    try:
        for (k, v) in convert(data).items():
            if v == 'down':
                salt_mark_status(k, v)
                continue
            target_node = db.session.query(
                Nodedb).filter_by(node_name=k).first()
            node_data = salt_minion(k)
            db_data = node_data['return'][0][k]
            master = ret_master()
            #TODO
            try:
                if target_node:
                    target_node.minion_data = db_data
                    target_node.node_ip=db_data.get('ipv4','1.1.1.1'),
                    target_node.os = db_data.get('lsb_distrib_description') or (
                        db_data.get('lsb_distrib_id') + db_data.get('lsb_distrib_release')) or (db_data.get('osfullname') + db_data('osrelease'))
                    target_node.cpu = str(db_data[
                        'num_cpus']) + ' * ' + str(db_data['cpu_model'])
                    target_node.kenel = db_data['kernelrelease']
                    target_node.core = int(db_data['num_cpus']),
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
                        core=int(db_data['num_cpus']),
                        mem=db_data['mem_total'],
                        host=db_data['host'],
                        master=master,
                        status=v
                    )
            except KeyError as e:
                logger.warning('updating ' + k + ' with error:' + str(e.args))
                continue
            result.append(target_node)
            db.session.add(target_node)
    except Exception as e:
        logger.warning('Error while updaing ' + str(((k, v))) + str(e.args))
    db.session.commit()

    return {'ok': str(result) + ' updated with redis return: ' + str(count)}



'''
### DOC ###

Celery function description

*influx syncing tasks*


### END ###
'''
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

'''
### DOC ###

Update statistics hash in redis

'''

@celery.task
def statistics_sync():
    result = []
    data = convert(redisapi.hgetall(name='sitestatus'))
    if not data:
        logger.warning('no site status data in redis cache')
        return {'failed': 'no site status data in redis cache'}
    try:
        state = Statistics(
            system_capacity = data['system_capacity'],
            managed_nodes = data['managed_nodes'],
            system_utilization = convert(redisapi.hgetall(name='sitestatus')).get('system_utilization',''),
            user_count = data['user_count'],
            registered_master = data['registered_master'],
            total_task = data['total_task'],
            service_level = convert(redisapi.hgetall(name='sitestatus')).get('service_level',''),
            uptime = data['uptime'],
            page_visit_count = data['page_visit_count'],
            api_visit_count = data['api_visit_count']
            )
        db.session.add(state)
        db.session.commit()
        result.append(state)
    except Exception as e:
        logger.warning('error in creating data in statistics')
        return {'failed': e}
    logger.info('Completed in writing data to statistics' + str(result))
    return {'successed': result}

@celery.task
def statistics_page_visit():
    try:
        data = convert(redisapi.hgetall(name='sitestatus'))
        if not data:
            logger.warning('no site status data in redis cache')
            return {'failed': 'no site status data in redis cache'} 
        if data.get('page_visit_count' , None):
            page_visit_count = int(data['page_visit_count'])
        else:
            page_visit_count = 0
        redisapi.hset('sitestatus', 'page_visit_count', page_visit_count + 1)
    except Exception as e:
        return {'failed': e} 
    return {'successed': 'page visit updated'}

@celery.task
def statistics_api_visit():
    try:
        data = convert(redisapi.hgetall(name='sitestatus'))
        if not data:
            logger.warning('no site status data in redis cache')
            return {'failed': 'no site status data in redis cache'} 
        if data.get('api_visit_count' , None):
            page_visit_count = int(data['api_visit_count'])
        else:
            page_visit_count = 0
        redisapi.hset('sitestatus', 'api_visit_count', page_visit_count + 1)
    except Exception as e:
        return {'failed': e} 
    return {'successed': 'page visit updated'}


@celery.task
def statistics_update():
    try:
        redisapi.hset('sitestatus', 'managed_nodes', Nodedb.get_count())
        redisapi.hset('sitestatus', 'system_capacity', session.query(
            func.sum(Nodedb.core).label('average')).all()[0][0])
        redisapi.hset('sitestatus', 'system_utilization', json.dumps(session.query(
            Perf_System_Load.node_name, func.avg(
                Perf_System_Load.load_avg_fifteen).label('average')
        ).group_by('node_name').all()))
        redisapi.hset('sitestatus', 'user_count', User.get_count())
        redisapi.hset('sitestatus', 'registered_master', Masterdb.get_count())
        redisapi.hset('sitestatus', 'total_task', 0)
        redisapi.hset('sitestatus', 'service_level', json.dumps(session.query(
            Perf_Ping.node_name, func.avg(
                Perf_Ping.ping_packet_loss).label('average')
        ).group_by('node_name').all()))
        redisapi.hset('sitestatus', 'uptime', (datetime.utcnow() - session.query(
            Masterdb.create_at).first()[0]).days)
    except Exception as e:
        logger.warning('error in writing sitestatus ')
        return {'failed': e}
    logger.info('Completed in updating site status')
