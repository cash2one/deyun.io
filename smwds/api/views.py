
# -*- coding: utf-8 -*-

import time
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_restful import Api, Resource
from extensions import cache, db
from api.libpepper import Pepper
from api.models import Apidb


saltapi = Pepper()
api = Blueprint('api', __name__, url_prefix='/api/v1')
#api = Blueprint('api', __name__)
api_wrap = Api(api, catch_all_404s=False)


def getsaltapi(target):
    sapi = Pepper(target.ret_api())
    if ((time.time() - target.token_expire) >= 0.0):
        ret = sapi.login(target.username, target.password, 'pam')
        target.token = ret['token']
        target.token_expire = ret['expire']
        db.session.add(target)
        db.session.commit()
    else:
        sapi.auth['token'] = target.token
    return sapi


class saltapi_get(Resource):

    @cache.memoize(timeout=60 * 60)
    #@login_required
    def get(self, master_id, path):
        target = Apidb.query.filter_by(id=master_id).first_or_404()
        t_api = getsaltapi(target)
        return t_api.req_get('/' + path)

class saltapi_monion(Resource):
    @cache.memoize(timeout=60 * 60)
    #@login_required
    def get(self, minion_id, path):
        target = Apidb.query.filter_by(id=monion_id).first_or_404()
        t_api = getsaltapi(target)
        return t_api.req_get('/' + path)
    



api_wrap.add_resource(saltapi_get, '/<string:master_id>/<string:path>')
api_wrap.add_resource(saltapi_monion, '/<string:minion_id>/<string:path>')
