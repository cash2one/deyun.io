#!/usr/bin/python #coding:utf-8
from datetime import timedelta
# Celery configuration

BROKER_URL = 'redis://localhost:6379/5'
CELERY_BACKEND = 'redis://localhost:6379/5'
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
BROKER_HEARTBEAT = 0
#Do not use json until all seriailzer has been deployed
#CELERY_TASK_SERIALIZER='json'
#CELERY_ACCEPT_CONTENT=['json']
#CELERY_RESULT_SERIALIZER='json'



CELERY_TIMEZONE = 'UTC'