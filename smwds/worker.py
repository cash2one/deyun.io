from app import create_app
from extensions import celery
from celery_task_socket import self_test
import eventlet

'''
Enable the monkey_patch if run into a socket issue
'''
eventlet.monkey_patch()

app = create_app()
celery.init_app(app)
celery.config_from_object('celery_socket_config')