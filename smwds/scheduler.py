from app import create_app
from extensions import celery_s
from celery_task import self_test
import eventlet

'''
Enable the monkey_patch if run into a socket issue
'''
#eventlet.monkey_patch()

app = create_app()
celery_s.init_app(app)
celery_s.config_from_object('celery_config')