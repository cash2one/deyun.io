
# -*- coding: utf-8 -*-

import time
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_restful import Api, Resource
from extensions import cache, db
from weblib.libpepper import Pepper
from api.models import Masterdb, Nodedb, Location


saltapi = Pepper()
api = Blueprint('api', __name__, url_prefix='/api/v1')
#api = Blueprint('api', __name__)
api_wrap = Api(api, catch_all_404s=False)


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
    node_master  = node.master
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
    #@login_required
    def get(self, master_id, path):
        target = Masterdb.query.filter_by(id=master_id).first_or_404()
        t_api = getsaltapi(target)
        return t_api.req_get('/' + path)

class saltapi_monion(Resource):
    @cache.memoize(timeout=60 * 60)
    #@login_required
    def get(self, minion_id, path):
        target_node = Nodedb.query.filter_by(id=monion_id).first_or_404()
        t_api = getsaltapi(target_node)
        return t_api.req_get('/' + target_nodez.name + '/' + path)
    



api_wrap.add_resource(saltapi_get, '/<string:master_id>/<string:path>')
api_wrap.add_resource(saltapi_monion, '/nodes/<string:minion_id>/<string:path>')
