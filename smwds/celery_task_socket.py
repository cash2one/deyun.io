#!/usr/bin/python
# coding:utf-8


from celery import Celery, platforms
from flask import Flask, current_app
import random
import time
import json
import redis
import time
import logging
import base64
import psycopg2
from celery.signals import task_prerun
from datetime import timedelta
from celery.schedules import crontab
from weblib.libpepper import Pepper, PepperException
from weblib.indbapi import Indb
from weblib.sensuapi import SensuAPI
from node import Perf, Perf_Node, Perf_Cpu, Perf_Mem, Perf_TCP, Perf_Disk, Perf_System_Load, Perf_Socket, Perf_Process_Count, Perf_Netif, Perf_Ping, Statistics
from api import Masterdb, Nodedb, Location
from user import User
from collections import defaultdict
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import desc
try:
    from prod import config
except:
    pass
from functools import wraps
from utils import convert
from extensions import celery, db
from requests import post
from flask_socketio import SocketIO
from statistics import mean

#import app
#tapp,session = app.create_socket_celery()
# celery.init_app(tapp)


celery.config_from_object('celery_socket_config')

logger = logging.getLogger('task')
logger.setLevel(20)
#celery, session = create_celery_app()

#celery.config_from_object('prod', silent=True)
# load config from celery_config.py , store other api information in prod.py


indbapi = Indb(config['INDB_HOST'] + ':' + config['INDB_PORT'])

sensuapi = SensuAPI(config['SENSU_HOST'] + ':' + config['SENSU_PORT'])

#master = session.query(Masterdb).first()
# try:
#    saltapi = Pepper(master.ret_api())
#    user = master.username
#    pawd = convert(base64.b64decode(master.password))
# except:
saltapi = Pepper(config['SALTAPI_HOST'])
user = config['SALTAPI_USER']
pawd = config['SALTAPI_PASS']

redisapi = redis.StrictRedis(host=config['REDIS_HOST'], port=config[
                             'REDIS_PORT'], db=config['REDIS_DB'])


'''
### DOC ###

Celery function description

*self test*


### END ###
'''
socketio = SocketIO(message_queue='redis://localhost:6379/0')


def ret_master():
    master = db.session.query(Masterdb).first()
    return master


def socket_emit(meta=None, event='others', room=None):
    try:
        if room:
            socketio.emit(event, meta, room=room, namespace='/deyunio')
        else:
            room = 'all'
            socketio.emit(event, meta, room='all', namespace='/deyunio')
    except Exception as e:
        logger.warning('error in emitting sitestatus to room :' +
                       str(room) + '  ' + str(e))
        return {'failed': e}
    logger.info({('sent ' + str(event) + ' to ' + str(room)): meta})
    return {('sent ' + str(event)): meta}


@celery.task
def self_test(x=16, y=16, url=None):
    x = int(x)
    y = int(y)
    res = x + y
    context = {"id": "test", "x": x, "y": y}
    result = "add((x){}, (y){})".format(context['x'], context['y'])
    goto = "{}".format(context['id'])
    time.sleep(10)
    meta = json.dumps({'result': result, 'goto': goto})
    #post(url, json=meta)
    socketio = SocketIO(message_queue='redis://localhost:6379/0')
    socketio.emit('connect', meta, namespace='/deyunio')
    #socketio.emit(event='hackerlist',meta=son.dumps({'emit_msg':'self test finished','type':'success'}))
    return meta
'''
emit index page data 
'''


@celery.task
def db_update_node_tag():
    try:
        data = db.session.query(Nodedb).all()
        master_data = db.session.query(Masterdb).all()
        for q in data:
            print(q)
            tag = Tag(
                node_id=q.id,
                node=q,
                name='Salt Node',
                type='default',
                url='fa fa-soundcloud'
            )
            db.session.add(tag)
            for p in master_data:
                if p.master_name == q.node_name:
                    tag = Tag(
                        node_id=q.id,
                        node=q,
                        name='Master Node',
                        type='primary',
                        url='fa fa-soundcloud'
                    )
    except Exception as e:
        logger.warning('error in creating tag ' + str(tag))
        return {'failed': e}
    else:
        db.session.commit()
        logger.info('db tags created')
        return {'ok': 'db tags created'}


@celery.task
def redis_update_nodelist():
    try:
        result = []
        data = {}
        node_data = Nodedb.query.all()
        for q in node_data:
            taglist = []
            for x in q.tags:
                taglist.append(
                    '<span class="label label-' + x.type + '"><i class="' +
                    x.url + '"></i> ' + x.name + '</span>'
                )
                #'<button class="btn btn-'+ x.type +' btn-circle" type="button"  data-container="body" data-toggle="popover" data-placement="top" data-content="' + x.name + '" data-original-title="" title=""><i class="' + x.url + '"></i></button>')
            data['Name'] = q.node_name
            data['Tag'] = taglist
            if q.status == 'up':
                data['Status'] = '<p><span class="label label-primary">' + \
                    q.status + '</span></p>'
            elif q.status == 'down':
                data['Status'] = '<p><span class="label label-warning">' + \
                    q.status + '</span></p>'
            else:
                data['Status'] = '<p><span class="label ">' + \
                    'unknow' + '</span></p>'
            data['Type'] = q.os
            data['Information'] = q.cpu + ' ' + q.mem + 'M'
            data['Note'] = q.bio
            data['Operator'] = q.master.master_name
            data['Date'] = str(q.create_at)
            data['Task'] = [x.task_name for x in q.tasks]
            result.append(data)
            data = {}
        meta = json.dumps(result)
    except Exception as e:
        logger.warning('error in syncing nodelist ' + str(meta))
        return {'failed': e}
    else:
        redisapi.set('node_list', meta)
        logger.info('redis node list updated' + str(meta))
        return {'ok': 'redis node list updated'}


@celery.task
def emit_nodelist(room=None):
    try:
        data = json.loads(convert(redisapi.get('node_list')))
    except Exception as e:
        logger.warning('error in loading index_data ' + str(data))
        return {'failed': e}

    meta = json.dumps(data)
    if room:
        socket_emit(meta=meta, event='nodelist', room=room)
        #socket_emit(meta=json.dumps({'emit_msg':'master status updated','type':'success'}),event='hackerlist',room=room)
        logger.info({'ok': 'emit_master_status' + str(room)})
    else:
        socket_emit(meta=meta, event='nodelist')
        logger.info({'ok': 'emit_master_status to all'})


def get_toplogy():
    m_node = Masterdb.query.all()
    s_node = Nodedb.query.all()
    node_list = []
    for item in s_node:
        node_list.append({'data': {'id': item.node_name}})
    for item in m_node:
        node_list.append({'data': {'id': item.master_name}})
    edge_list = []
    for item in s_node:
        edge_list.append(
            {'data': {'source': item.node_name, 'target': item.master.master_name}})
    data = {
        'nodes': node_list,
        'edges': edge_list
    }
    logger.info({'ok': 'get_toplogy'})
    return json.dumps(data)


@celery.task
def redis_master_status_update():
    try:
        master = Masterdb.query.first()
        r = indbapi.ret_point_24h(
            table='memory_percent_usedWOBuffersCaches', db='graphite', host=master.master_name)
        p = indbapi.ret_point_24h(
            table='cpu_user', db='graphite', host=master.master_name)
        index_data = {
            'top': get_toplogy(),
            'master': {'name': master.master_name, 'mem': r, 'cpu': p}
        }
    except Exception as e:
        logger.warning('error in writing master status ' +
                       str(e) + ' data:' + index_data)
        return {'failed': index_data}
    else:
        redisapi.set('index_data', json.dumps(index_data))

        emit_master_status.delay(room='all')
    logger.info({'ok': index_data})
    socket_emit(meta=json.dumps(
        {'emit_msg': 'redis status updated', 'type': 'success'}), event='hackerlist')
    return {"ok": index_data}


@celery.task
def emit_master_status(room=None):
    try:
        data = json.loads(convert(redisapi.get('index_data')))
    except Exception as e:
        logger.warning('error in loading index_data ' + str(data))
        return {'failed': e}
    meta = json.dumps(data)
    if room:
        socket_emit(meta=meta, event='m_status', room=room)
        #socket_emit(meta=json.dumps({'emit_msg':'master status updated','type':'success'}),event='hackerlist',room=room)
        logger.info({'ok': 'emit_master_status' + str(room)})
    else:
        socket_emit(meta=meta, event='m_status')
        logger.info({'ok': 'emit_master_status to all'})


'''
emit the site status data by sockitio
'''


def mean_status(data):
    '''
    return the mean value for the value[1]
    '''
    j = json.loads(data)
    r = mean([x[1] for x in j]) * 100
    return '{:.2f}'.format(r)


def spark_data():
    ret = {}
    a = db.session.query(Statistics.managed_nodes).order_by(
        desc(Statistics.update_at)).limit(8).all()
    ret['n'] = [r for r, in a]
    b = db.session.query(Statistics.registered_master).order_by(
        desc(Statistics.update_at)).limit(8).all()
    ret['m'] = [r for r, in b]
    return json.dumps(ret)


def ret_socket_sitestatus():
    d = convert(redisapi.hgetall('sitestatus'))
    d['service_level'] = str(100.0 - float(mean_status(d['service_level'])))
    d['system_utilization'] = str(mean_status(d['system_utilization']))
    a = db.session.query(Statistics.managed_nodes).order_by(
        desc(Statistics.update_at)).limit(8).all()
    d['n'] = [r for r, in a]
    b = db.session.query(Statistics.registered_master).order_by(
        desc(Statistics.update_at)).limit(8).all()
    d['m'] = [r for r, in b]
    return d


@celery.task
def emit_site_status(room=None):
    try:
        data = ret_socket_sitestatus()
    except Exception as e:
        logger.warning('error in loading sitestatus to ' + str(room))
        return {'failed': e}
    meta = json.dumps(data)
    if room:
        socket_emit(meta=meta, event='sitestatus', room=room)
        logger.info({'ok': 'emit_site_status to ' + str(room)})
    else:
        socket_emit(meta=meta, event='sitestatus')
        logger.info({'ok': 'emit_site_status to all'})


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

This taks should go with below task follow:
1. obtain the jid from salt api.(salt-api could only return the jid by load_async function)
2. boardcast the information by websocket "initilized task"
3. rest a while (could see the state change in web when debuging)
4. ask for the salt api for taks result (emitting "running")
5. after api returned the result, emitting the final result  

'''


@celery.task
@salt_command
def salt_exec_func(tgt='*', func='test.ping', arg=None, kwarg=None):
    try:
        result = saltapi.local_async(tgt=tgt, fun=func, arg=arg, kwarg=kwarg)
        jid = result['return'][0]['jid']
        tgt = result['return'][0]['minions']
        i = int(redisapi.hlen('salt_task_list')) + 1
        one = {}
        one['jid'] = jid
        one['start'] = ''
        one['end'] = ''
        one['fun'] = func
        one['arg'] = arg
        one['kwarg'] = kwarg
        one['tgt'] = tgt
        one['ret'] = ''
        one['status'] = '<button type="button" class="btn btn-xs btn-outline btn-primary  "><i class="fa fa-send-o"></i> Excuting</button>'
        one['text'] = 'text-navy animated infinite flash'
        redisapi.hset('salt_task_list', i, json.dumps(one))
    except Exception as e:
        logger.warning('error in getting saltstack jid', e)
        return {'failed:': e}
    try:
        i = 0
        while(i < 600):
            try:
                i = i + 1
                ret = saltapi.lookup_jid(jid['return'])
                if ret['return'] != [{}]:
                    break
            except PepperException as e:
                pass
            time.sleep(5)
        else:
            # TODO timeout
            return {'failed:': {'Task Running Timeout'}}
    except Exception as e:
        logger.warning('error in geting job status', e)
        return {'failed:': e}
    logger.info({'ok':  str(jid) + ' : ' + str(tgt)})
    socket_emit(meta=json.dumps(
        {'func': 'salt_task_list'}), event='func_init', room='all')
    return {"ok": 'salt_task_list'}


@celery.task
def emit_salt_task_list(room=None):
    try:
        data = ''
        data = convert(redisapi.hgetall('salt_task_list'))
    except Exception as e:
        logger.warning('error in loading salt_task_list '+str(data), e)
        return {'failed': e}
    meta = json.dumps(data)
    if room:
        socket_emit(meta=meta, event='salt_task_list', room=room)
        logger.info({'ok': 'emit_salt_task_list' + str(room)})
    else:
        socket_emit(meta=meta, event='salt_task_list')
        logger.info({'ok': 'emit_salt_task_list to all'})

@celery.task
@salt_command
def emit_salt_jid(jid,room):
    try:
        meta = json.dumps({'msg':'initialization completed, loading data...','jid':jid})
        socket_emit(meta=meta, event='salt_jid', room=room)
        ret = saltapi.lookup_jid(jid)
    except Exception as e:
        logger.exception(e)
        meta = json.dumps({'msg':'error, please try again later...','jid':jid})
        socket_emit(meta=meta, event='salt_jid', room=room)
        return 1
    else:
        logger.info({'ok': 'emit_salt_jid'})
        meta = json.dumps({'msg':'job info loaded.','jid':jid})
        socket_emit(meta=meta, event='salt_jid', room=room)
        meta = json.dumps(ret)
        socket_emit(meta=meta, event='salt_jid', room=room)
        return 0


'''
### DOC ###

Celery function description

*Get minion status from saltstack api and store in redis cache*


### END ###
'''


@celery.task
@salt_command
def redis_salt_minion_status_update():
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
        logger.warning('error in updaing minion status in redis :' + str(e))
        return {'failed': e}
    logger.info('minion status updated')
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
    except Exception as e:
        return {'failed': e}
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
def salt_mark_status(k, v):
    target_node = db.session.query(
        Nodedb).filter_by(node_name=k).first()
    master = ret_master()
    # TODO
    if target_node:
        target_node.status = v
    else:
        target_node = Nodedb(
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
def db_salt_nodes_sync():
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
            # TODO
            try:
                if target_node:
                    target_node.minion_data = db_data
                    target_node.node_ip = db_data.get('ipv4', '1.1.1.1'),
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
                        node_ip=db_data.get('ipv4', '1.1.1.1'),
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
        result = []
    except Exception as e:
        return {'failed': e}
    for item in data:
        try:
            sensunode = session.query(Perf_Node).filter_by(
                sensu_node_name=item["name"]).first()
        except Exception as e:
            return {'failed': e}
        try:
            if sensunode:
                sensunode.sensu_subscriptions = item["address"]
                sensunode.sensu_version = item["version"]
                sensunode.sensu_timestamp = item["timestamp"]
                result.append(sensunode)
            else:
                sensunode = Perf_Node(
                    sensu_node_name=item["name"],
                    sensu_subscriptions=item["address"],
                    sensu_version=item["version"],
                    sensu_timestamp=item["timestamp"]
                )
                result.append(sensunode)
        except Exception as e:
            return {'failed': e}
        session.add(sensunode)
    try:
        session.commit()
    except Exception as e:
        return {'failed': e}

    return {'successed': result}


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
    # return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
    try:
        for (k, v) in data.items():
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
        logger.warning('error in creating data ' +
                       str((k, v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Cpu' + str(data))
    return {'successed': result}


@celery.task
def sync_mem_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('memory_percent_usedWOBuffersCaches'))
    praser.append(indbapi.get_sync_data('memory_percent_freeWOBuffersCaches'))
    praser.append(indbapi.get_sync_data('memory_percent_swapUsed'))
    praser.append(indbapi.get_sync_data('memory_percent_free'))
    # return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
    try:
        for (k, v) in data.items():
            target_node = Perf_Mem(
                node_name=k,
                mem_usedWOBuffersCaches=v[0],
                mem_freeWOBuffersCaches=v[1],
                mem_swapUsed=v[2]
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
    logger.info('Completed in writing data to Pref_Mem' + str(data))
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
    # return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
    try:
        for (k, v) in data.items():
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
        logger.warning('error in creating data ' +
                       str((k, v)) + ' in ' + str(data))
        return {'failed': e}
    try:
        session.commit()
    except Exception as e:
        logger.warning('error in writing data ' + str(data))
        return {'failed': e}
    logger.info('Completed in writing data to Pref_Tcp' + str(data))
    return {'successed': result}


@celery.task
def sync_disk_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('disk_usage_root_used'))
    praser.append(indbapi.get_sync_data('disk_usage_root_avail'))
    praser.append(indbapi.get_sync_data('disk_usage_root_used_percentage'))
    # return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
    try:
        for (k, v) in data.items():
            target_node = Perf_Disk(
                node_name=k,
                disk_usage_root_used=v[0],
                disk_usage_root_avail=v[1],
                disk_usage_root_used_percentage=v[2]
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
    logger.info('Completed in writing data to Pref_Disk' + str(data))
    return {'successed': result}


@celery.task
def sync_load_from_influxdb():
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('load_load_avg_one'))
    praser.append(indbapi.get_sync_data('load_load_avg_five'))
    praser.append(indbapi.get_sync_data('load_load_avg_fifteen'))
    # return sync_praser_data(praser)
    try:
        data = sync_praser_data(praser)
    except Exception as e:
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
    try:
        for (k, v) in data.items():
            target_node = Perf_System_Load(
                node_name=k,
                load_avg_one=v[0],
                load_avg_five=v[1],
                load_avg_fifteen=v[2]
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
    logger.info('Completed in writing data to Pref_Load' + str(data))
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
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
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
    logger.info('Completed in writing data to Pref_Socket' + str(data))
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
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
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
    logger.info('Completed in writing data to Process_count' + str(data))
    return {'successed': result}


@celery.task
def sync_netif_from_influxdb(netif='eth0'):
    praser = []
    result = []
    praser.append(indbapi.get_sync_data('net_' + netif + '_tx_bytes'))
    praser.append(indbapi.get_sync_data('net_' + netif + '_rx_bytes'))
    praser.append(indbapi.get_sync_data('net_' + netif + '_tx_packets'))
    praser.append(indbapi.get_sync_data('net_' + netif + '_rx_packets'))
    praser.append(indbapi.get_sync_data('net_' + netif + '_tx_errors'))
    praser.append(indbapi.get_sync_data('net_' + netif + '_if_speed'))
    try:
        data = sync_praser_data(praser)
        # return sync_praser_data(praser)
    except Exception as e:
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
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
    praser.append(indbapi.get_sync_data('ping_' + node + '_packet_loss'))
    praser.append(indbapi.get_sync_data('ping_' + node + '_avg'))
    try:
        data = sync_praser_data(praser)
        # return sync_praser_data(praser)
    except Exception as e:
        logger.error(
            'error while prasering data from influx db: ' + str(praser))
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
def db_statistics_sync():
    result = []
    data = convert(redisapi.hgetall(name='sitestatus'))
    if not data:
        logger.warning('no site status data in redis cache')
        return {'failed': 'no site status data in redis cache'}
    try:
        state = Statistics(
            system_capacity=data['system_capacity'],
            managed_nodes=data['managed_nodes'],
            system_utilization=convert(redisapi.hgetall(
                name='sitestatus')).get('system_utilization', ''),
            user_count=data['user_count'],
            registered_master=data['registered_master'],
            total_task=data['total_task'],
            service_level=convert(redisapi.hgetall(
                name='sitestatus')).get('service_level', ''),
            uptime=data['uptime'],
            page_visit_count=data['page_visit_count'],
            api_visit_count=data['api_visit_count']
        )
        db.session.add(state)
        db.session.commit()
        result.append(state)
    except Exception as e:
        logger.warning('error in creating data in statistics :' + str(e))
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
        if data.get('page_visit_count', None):
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
        if data.get('api_visit_count', None):
            page_visit_count = int(data['api_visit_count'])
        else:
            page_visit_count = 0
        redisapi.hset('sitestatus', 'api_visit_count', page_visit_count + 1)
    except Exception as e:
        return {'failed': e}
    return {'successed': 'page visit updated'}


@celery.task
def redis_statistics_update():
    try:
        redisapi.hset('sitestatus', 'managed_nodes', Nodedb.get_count())
        redisapi.hset('sitestatus', 'system_capacity', db.session.query(
            func.sum(Nodedb.core).label('average')).all()[0][0])
        redisapi.hset('sitestatus', 'system_utilization', json.dumps(db.session.query(
            Perf_System_Load.node_name, func.avg(
                Perf_System_Load.load_avg_fifteen).label('average')
        ).group_by('node_name').all()))
        redisapi.hset('sitestatus', 'user_count', User.get_count())
        redisapi.hset('sitestatus', 'registered_master', Masterdb.get_count())
        redisapi.hset('sitestatus', 'total_task', 0)
        redisapi.hset('sitestatus', 'service_level', json.dumps(db.session.query(
            Perf_Ping.node_name, func.avg(
                Perf_Ping.ping_packet_loss).label('average')
        ).group_by('node_name').all()))
        redisapi.hset('sitestatus', 'uptime', (datetime.utcnow() - db.session.query(
            Masterdb.create_at).first()[0]).days)
    except Exception as e:
        logger.warning('error in writing sitestatus ' + str(e))
        return {'failed': e}
    logger.info('Completed in updating site status')
    emit_site_status.delay(room='all')
'''
Text Color:
text-danger text-navy text-primary text-success text-info text-warning  text-muted text-white
'''


@celery.task
def redis_salt_task_sync():
    try:
        posconn = psycopg2.connect(dbname=config['POSTGRESQL_DB'], user=config[
                                   'POSTGRESQL_USER'], host=config['POSTGRESQL_HOST'], password=config['POSTGRESQL_PASSWD'])
        cur = posconn.cursor()
        cur.execute("SELECT * FROM redis_task_list LIMIT 80;")
        i = 100
        for line in cur:
            one = {}
            one['jid'] = line[0]
            one['start'] = str(line[1].replace(microsecond=0)) if type(
                line[1]) is datetime.datetime else ''
            one['end'] = str(line[2].replace(microsecond=0)) if type(
                line[2]) is datetime.datetime else ''
            one['fun'] = line[3]
            one['arg'] = line[4]
            one['kwarg'] = line[5]
            one['tgt'] = line[6]
            #one['ret'] = line[7]
            one['status'] = '<button type="button" class="btn btn-xs btn-outline btn-success  "><i class="fa fa-check-circle-o"></i> Completed</button>' if line[
                8] is True else '<button type="button" class="btn btn-xs btn-outline btn-warning  "><i class="fa fa-times-circle-o"></i> Failed</button>'
            one['text'] = 'text-success' if line[8] is True else 'text-warning'
            redisapi.hset('salt_task_list', i, json.dumps(one))
            i -= 1
    except Exception as e:
        posconn.close()
        logger.warning('error in syncing redis_salt_task_sync ', e)
        return {'failed': e}
    posconn.close()
    logger.info('Completed in syncing redis_salt_task_sync ')
    return str(i) + ' records synced'


@celery.task
def redis_salt_event_sync():
    try:
        # posconn = psycopg2.connect(
        # dbname='salt', user='salt', host='123.56.195.220', password='salt')
        posconn = psycopg2.connect(dbname=config['POSTGRESQL_DB'], user=config[
                                   'POSTGRESQL_USER'], host=config['POSTGRESQL_HOST'], password=config['POSTGRESQL_PASSWD'])
        cur = posconn.cursor()
        cur.execute("SELECT * FROM salt_events LIMIT 100;")
        i = 0
        ret = {}
        for line in cur:
            one = []
            for col in line:
                if type(col) is datetime:
                    col = str(col.replace(microsecond=0))
                one.append(col)
            redisapi.hset('salt_event_list', i, one)
            i += 1
    except Exception as e:
        posconn.close()
        logger.warning('error in syncing redis_salt_event_sync ', e)
        return {'failed': e}
    posconn.close()
    logger.info('Completed in syncing redis_salt_event_sync ')
    return str(i) + ' records synced'
