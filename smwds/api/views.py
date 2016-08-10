
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify
from flask_login import login_user, current_user, logout_user
from flask_restful import Api, Resource
from extensions import cache
api = Blueprint('api', __name__, url_prefix='/api/v1')
#api = Blueprint('api', __name__)
api_wrap = Api(api,catch_all_404s=False,)


class TodoItem(Resource):
    
    def get(self, id):
        return {'task': 'Say "Hello, World!"'}

api_wrap.add_resource(TodoItem, '/todos/<int:id>')