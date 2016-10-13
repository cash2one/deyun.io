#!/usr/bin/python
#coding:utf-8

from celery import Celery, platforms
from flask import Flask, current_app
from extensions import db 
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
                logger.warn('updating ' + k + ' with error:' + str(e.args))
                continue
            result.append(target_node)
            session.add(target_node)
    except Exception as e:
        logger.warn('Error while updaing ' + db_data['id'] + str(e.args))
    session.commit()

    return {'ok': str(result) + ' updated with redis return: ' + str(count)}


@celery.task
def sync_node_from_saltstack():
    pass 