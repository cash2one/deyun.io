from app import create_app
from extensions import celery

#from celery_task_socket import self_test

app = create_app()
celery.init(app)
celery.config_from_object('celery_socket_config')