
# -*- coding: utf-8 -*-

import time
import json
import requests
import hashlib
import logging
import redis
from utils import convert 
from flask import Blueprint, request, jsonify, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from flask_restful import Api, Resource
from extensions import cache, db
from weblib.libpepper import Pepper
from weblib.indbapi import Indb
from weblib.sensuapi import SensuAPI
from api.models import Masterdb, Nodedb, Location
from flask_sqlalchemy import Pagination
try:
    from prod import config
except:
    from config import DefaultConfig as config

indbapi = Indb(config['INDB_HOST'] + ':' + config['INDB_PORT'])

sensuapi = SensuAPI(config['SENSU_HOST'] + ':' + config['SENSU_PORT'])

redisapi = redis.StrictRedis(host=config['REDIS_HOST'], port=config['REDIS_PORT'], db=config['REDIS_DB'])

api = Blueprint('api', __name__, url_prefix='/api/v1')
logger = logging.getLogger('api')
logger.setLevel(20)
api_wrap = Api(api, catch_all_404s=False)


'''
### DOC ###
view function for api


'''


@api.before_request
def api_before_request():
    pass

def api_log(status_code):
    logger.info(str(current_user.name) + "@uid:" + str(current_user.id)+ " @session:"+ session.session_id + " @request_url:" + request.url + " @ret:" + str(status_code))

def getsaltapi(master):

    sapi = Pepper(master.ret_api())
    if ((time.time() - master.token_expire) >= 0.0):
        ret = sapi.login(master.username, master.password, 'pam')
        master.token = ret['token']
        master.token_expire = ret['expire']
        db.session.add(master)
        db.session.commit()
    else:
        sapi.auth['token'] = master.token
    return sapi


def getsaltapi_node(node):
    node_master = node.master
    return getsaltapi(node_master)


class saltapi_get(Resource):
    '''
    A api warper for saltstack original apis so we can addd more functions.and

    What GET could fetch from master: 
    /jobs/(jid)  List jobs or show a single job from the job cache.
    /minions/(mid) A convenience URL for getting lists of minions or getting minion details
    /events/ An HTTP stream of the Salt master event bus (Not a good idea to use in API)
    /keys/ Convenience URLs for working with minion keys
    /ws/token  Return a websocket connection of Salt's event stream
    /stats/ Expose statistics on the running CherryPy server
    '''

    @cache.memoize(timeout=60 * 60)
    def get(self, master_id, path):
        target = Masterdb.query.filter_by(id=master_id).first_or_404()
        t_api = getsaltapi(target)
        try:
            data = t_api.req_get('/' + path)
        except Exception as e:
            api_log(e)
            return e 
        api_log(200)
        return data



class saltapi_monion(Resource):
    '''
    A correct api qunery would update minion db in database 
    '''
    @cache.cached(timeout=60 * 60)
    def get(self, minion_id):
        target_node = Nodedb.query.filter_by(node_name=minion_id).first_or_404()
        t_api = getsaltapi_node(target_node)
        try:
            api_data = t_api.req_get('/minions/' + target_node.node_name)
        except Exception as e:
            return e
        if api_data['return'][0] == {}:
            api_log(201)
            return {'status': 201, 'result': 'no data'}     
        else:

            md5_data = json.dumps(api_data['return'][0], sort_keys=True)
            db_data = api_data['return'][0][minion_id]
            db_data['md5'] = hashlib.md5(str(md5_data).encode()).hexdigest()

            if target_node.minion_data == '':
                target_node.minion_data = db_data
            elif target_node.minion_data['md5'] != db_data['md5']:
                db.session.add(target_node)
                target_node.os = db_data['lsb_distrib_description'] 
                target_node.cpu = db_data['num_cpus'] + ' * '  + db_data['cpu_model'] 
                target_node.kenel = db_data['kernelrelease']
                target_node.mem = db_data['mem_total']
                target_node.host = db_data['host']
                db.session.commit()
            api_log(200)
            return md5_data




@cache.memoize(timeout=60 * 60)
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
    # current_app.logger.info(json.dumps(data))
    # return json.dumps(data)
    return json.dumps(data)


class influx_db(Resource):

    @cache.memoize(timeout=60 * 60)
    def get(self, table, db, node):
        indbapi = Indb(current_app.config[
                       'INDB_HOST'] + ':' + current_app.config['INDB_PORT'])
        ret = indbapi.ret_point_24h(table=table, db=db, host=node)

        return json.dumps(ret)

class site_status(Resource):
    def get(self):
        data = redisapi.hgetall('sitestatus')
        if data:
            return json.dumps(convert(data))

api_wrap.add_resource(site_status, '/sitestatus')
api_wrap.add_resource(saltapi_get, '/<string:master_id>/<string:path>')
api_wrap.add_resource(saltapi_monion, '/nodes/<string:minion_id>')
api_wrap.add_resource(influx_db, '/indb/24/<string:node>/<string:db>/<string:table>')
