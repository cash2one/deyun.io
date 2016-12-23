#!/usr/bin/python #coding:utf-8
from datetime import timedelta
# Celery configuration

BROKER_URL = 'redis://localhost:6379/5'
CELERY_BACKEND = 'redis://localhost:6379/5'
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
#Do not use json until all seriailzer has been deployed
#CELERY_TASK_SERIALIZER='json'
#CELERY_ACCEPT_CONTENT=['json']
#CELERY_RESULT_SERIALIZER='json'

# Celery task to sync between CMDB and monitor DB
CELERYBEAT_SCHEDULE = {
    'redis_salt_event_sync': {
        'task': 'celery_task.redis_salt_event_sync',
        'schedule': timedelta(seconds=3200)
        },
    'redis_salt_task_sync': {
        'task': 'celery_task.redis_salt_task_sync',
        'schedule': timedelta(seconds=3002)
        },
    'redis_statistics_update': {
        'task': 'celery_task.redis_statistics_update',
        'schedule': timedelta(seconds=120)
        },
    'db_statistics_sync': {
        'task': 'celery_task.db_statistics_sync',
        'schedule': timedelta(seconds=60 * 60 * 6)
        },
#    'sync_ping_from_influxdb': {
#        'task': 'celery_task.sync_ping_from_influxdb',
#        'schedule': timedelta(seconds=300)
#        },
#    'sync_netif_from_influxdb': {
#        'task': 'celery_task.sync_netif_from_influxdb',
#        'schedule': timedelta(seconds=305)
#        },
#    'sync_process_from_influxdb': {
#        'task': 'celery_task.sync_process_from_influxdb',
#        'schedule': timedelta(seconds=322)
#        },
#    'sync_socket_from_influxdb': {
#        'task': 'celery_task.sync_socket_from_influxdb',
#        'schedule': timedelta(seconds=373)
#        },
#    'sync_load_from_influxdb': {
#        'task': 'celery_task.sync_load_from_influxdb',
#        'schedule': timedelta(seconds=323)
#        },
#    'sync_disk_from_influxdb': {
#        'task': 'celery_task.sync_disk_from_influxdb',
#        'schedule': timedelta(seconds=334)
#        },
#    'sync_tcp_from_influxdb': {
#        'task': 'celery_task.sync_tcp_from_influxdb',
#        'schedule': timedelta(seconds=363)
#        },
#    'sync_mem_from_influxdb': {
#       'task': 'celery_task.sync_mem_from_influxdb',
#        'schedule': timedelta(seconds=350)
#        },
#    'sync_cpu_from_influxdb': {
#        'task': 'celery_task.sync_cpu_from_influxdb',
#        'schedule': timedelta(seconds=334)
#        },
#    'sync_node_from_influxdb': {
#        'task': 'celery_task.sync_node_from_influxdb',
#        'schedule': timedelta(seconds=376)
#        },
    'redis_salt_minion_status_update': {
        'task': 'celery_task.redis_salt_minion_status_update',
       'schedule': timedelta(seconds=60)
        },
    'redis_master_status_update': {
        'task': 'celery_task.redis_master_status_update',
        'schedule': timedelta(seconds=60)
        },
    'redis_update_nodelist': {
        'task': 'celery_task.redis_update_nodelist',
        'schedule': timedelta(seconds=60)
        }
}

CELERY_TIMEZONE = 'UTC'