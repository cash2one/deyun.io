
# -*- coding: utf-8 -*-

import time
import json
import requests
import hashlib
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from flask_restful import Api, Resource
from extensions import cache, db
from weblib.libpepper import Pepper
from weblib.indbapi import Indb
from api.models import Masterdb, Nodedb, Location


api = Blueprint('api', __name__, url_prefix='/api/v1')

api_wrap = Api(api, catch_all_404s=False)


@api.before_request
def api_before_request():
    pass


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
        return t_api.req_get('/' + path)


class saltapi_monion(Resource):
    '''
    A correct api qunery would update minion db in database 
    '''
    @cache.memoize(timeout=60 * 60)
    def get(self, minion_id, path):
        target_node = Nodedb.query.filter_by(node_name=monion_id).first_or_404()
        t_api = getsaltapi(ß)
        try:
            api_data = t_api.req_get('/' + target_nodez.name + '/' + path)
        except Exception as e:
            return e
        if api_data['return'][0] == {}:
            return {'status': 200, 'result': 'no data'}
        else:

            md5_data = json.dumps(api_data['return'][0], sort_keys=True)
            db_data = api_data['return'][0]
            db_data['md5'] = hashlib.md5(str(md5_data).encode()).hexdigest()

            if target_node.minion_data == '':
                target_node.minion_data = db_data
                db.session.add(target_node)
                db.session.commit()
            elif target_node.minion_data['md5'] != db_data['md5']:
                target_node.minion_data = db_data
                db.session.add(target_node)
                db.session.commit()
            return data


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


api_wrap.add_resource(saltapi_get, '/<string:master_id>/<string:path>')
api_wrap.add_resource(
    saltapi_monion, '/nodes/<string:minion_id>/<string:path>')
api_wrap.add_resource(
    influx_db, '/indb/24/<string:node>/<string:db>/<string:table>')
