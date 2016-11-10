#!/usr/bin/python #coding:utf-8
from datetime import timedelta
# Celery configuration

BROKER_URL = 'redis://localhost:6379/5'
CELERY_BACKEND = 'redis://localhost:6379/5'

#Do not use json until all seriailzer has been deployed
#CELERY_TASK_SERIALIZER='json'
#CELERY_ACCEPT_CONTENT=['json']
#CELERY_RESULT_SERIALIZER='json'

# Celery task to sync between CMDB and monitor DB
CELERYBEAT_SCHEDULE = {
    'statistics_sync_30_seconds': {
        'task': 'celery_task_socket.statistics_sync',
#        'task': 'celery_task_socket.statistics_update',
#        'task': 'celery_task_socket.salt_minion_status',
#        'task': 'celery_task_socket.salt_nodes_sync',
        'schedule': timedelta(seconds=30)
    },
    'update_master_status_30_seconds': {
        'task': 'celery_task_socket.update_master_status',
        'schedule': timedelta(seconds=30)
        }
#    'add-every-3600-seconds': {
#        'task': 'celery_task_socket.salt_nodes_sync',
#        'task': 'celery_task_socket.sync_cpu_from_influxdb',
#        'task': 'celery_task_socket.sync_mem_from_influxdb',
#        'task': 'celery_task_socket.sync_tcp_from_influxdb',
#        'task': 'celery_task_socket.sync_disk_from_influxdb',
#        'task': 'celery_task_socket.sync_load_from_influxdb',
#        'task': 'celery_task_socket.sync_socket_from_influxdb',
#        'task': 'celery_task_socket.sync_process_from_influxdb',
#        'task': 'celery_task_socket.sync_netif_from_influxdb',
#        'task': 'celery_task_socket.sync_ping_from_influxdb',
#        'schedule': timedelta(seconds=3600)}
    
}

CELERY_TIMEZONE = 'UTC'