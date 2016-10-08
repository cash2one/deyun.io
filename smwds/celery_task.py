#!/usr/bin/python
#coding:utf-8

from celery import Celery, platforms
from flask import Flask
from extensions import db 
import random, time, json
from datetime import timedelta
from celery.schedules import crontab
from weblib.libpepper import Pepper
from weblib.indbapi import Indb



app = Flask(__name__)

app.config.from_pyfile('prod.py', silent=True)

indbapi = Indb(app.config[
                    'INDB_HOST'] + ':' + app.config['INDB_PORT'])

def make_celery(app):
    celery = Celery(app.__class__)
    platforms.C_FORCE_ROOT = True
    # load setting.py config
    celery.config_from_object('celery_config')

    #celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return (app,celery)

app, celery = make_celery(app)

@celery.task(name="tasks.add")
def add(x, y):
    return x + y

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
def sync_from_influxdb():
    return indbapi.test()


@celery.task
def sync_from_saltstack():
    pass 