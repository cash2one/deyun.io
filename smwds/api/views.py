
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_restful import Api, Resource
from extensions import cache
from api.libpepper import Pepper


saltapi = Pepper()
api = Blueprint('api', __name__, url_prefix='/api/v1')
#api = Blueprint('api', __name__)
api_wrap = Api(api, catch_all_404s=False)


class saltapi(Resource):

    @cache.memoize(timeout=60 * 60)
    @login_required
    def get(self, id):
        return {'task': 'Say "Hello, World!"'}


api_wrap.add_resource(saltapi, '/todos/<int:id>')
