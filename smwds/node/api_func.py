import time, json
import requests
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from flask_restful import Api, Resource
from extensions import cache, db
from weblib.libpepper import Pepper
from weblib.indbapi import Indb

class Indb_func(object):

  @staticmethod
  @cache.memoize(timeout=50)
  def monitor_data(table,db,node):
      indbapi = Indb(current_app.config['INDB_HOST'] + ':' + current_app.config['INDB_PORT'])
      ret = indbapi.ret_point_24h(table=table, db=db, host=node)
      return json.dumps(ret)

  