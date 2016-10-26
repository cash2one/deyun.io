from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_script import Manager
from flask_socketio import SocketIO

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from config import DefaultConfig
from utils import INSTANCE_FOLDER_PATH
from extensions import db, login_manager, cache, Anonymous, celery
from filters import format_date, pretty_date, nl2br
from user import User
from weblib.redissession import RedisSession
from celery import Celery
from socket_conn import Socket_conn
import eventlet 


import os

app = Flask(__name__)
bootstrap = Bootstrap(app)
socketio = SocketIO()
app_name = None

def create_app(config=None, app_name=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = DefaultConfig.PROJECT

    app = Flask(
        app_name,
        instance_path=INSTANCE_FOLDER_PATH,
        root_path=INSTANCE_FOLDER_PATH,
        instance_relative_config=True,
        static_url_path=None,
        static_folder=None
    )
    configure_app(app, config)
    
    configure_blueprints(app)
    configure_extensions(app)
    configure_logging(app)
    configure_template_filters(app)
    configure_error_handlers(app)
    configure_hook(app)
    celery.init_app(app)
    return app

def create_socket_celery(app=None):
    app = create_app()
    #celery.conf.update(app.config)
    app.app_context().push()


    # an Engine, which the Session will use for connection
    # resources
    celery_task = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

    # create a configured "Session" class
    Session = sessionmaker(bind=celery_task)
    
    # create a Session
    session = Session()
    return app , session

def create_celery_app(app=None):

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    #app = create_app()
    if app_name is None:
        app_name = DefaultConfig.PROJECT

    app = Flask(
        app_name,
        instance_path=INSTANCE_FOLDER_PATH,
        root_path=INSTANCE_FOLDER_PATH,
        instance_relative_config=True,
        static_url_path=None,
        static_folder=None
    )
    configure_app(app, config)
    
    configure_blueprints(app)
    configure_extensions(app)
    configure_logging(app)
    configure_template_filters(app)
    configure_error_handlers(app)
    configure_hook(app)

    celery = Celery(app.__class__)
    celery.config_from_object('celery_config')
    
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    #celery.conf.update(app.config)
    app.app_context().push()


    # an Engine, which the Session will use for connection
    # resources
    celery_task = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

    # create a configured "Session" class
    Session = sessionmaker(bind=celery_task)
    
    # create a Session
    session = Session()


    return celery , session



def configure_app(app, config=None):
    """Different ways of configurations."""

    # http://flask.pocoo.org/docs/api/#configuration
    app.config.from_object(DefaultConfig)

    # http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('prod.py', silent=True)

    if config:
        app.config.from_object(config)
        
    # Use instance folder instead of env variables to make deployment easier.
    #app.config.from_envvar('%s_APP_CONFIG' % DefaultConfig.PROJECT.upper(), silent=True)

    #Redis Cache
    cache_config = {
        'CACHE_TYPE': DefaultConfig.CACHE_TYPE,
        'CACHE_REDIS_HOST': DefaultConfig.CACHE_REDIS_HOST,
        'CACHE_REDIS_PORT': DefaultConfig.CACHE_REDIS_PORT,
        'CACHE_REDIS_DB': DefaultConfig.CACHE_REDIS_DB,
        'CACHE_REDIS_PASSWORD': DefaultConfig.CACHE_REDIS_PASSWORD
                    }

    cache.init_app(app, config=cache_config)
    RedisSession(app)
    socketio = SocketIO(app, async_mode='eventlet', message_queue=app.config['SOCKETIO_REDIS_URL'])  



def configure_extensions(app):
        # flask-sqlalchemy
    db.init_app(app)

    # Sentry
    if app.config['SENTRY_DSN']:
        sentry.init(app, dsn=app.config['SENTRY_DSN'])

    # flask-login
    login_manager.login_view = 'frontend.login'
    login_manager.refresh_view = 'frontend.login'
    login_manager.anonymous_user = Anonymous

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)
    login_manager.setup_app(app)


def configure_hook(app):
    from flask_sqlalchemy import get_debug_queries
    import logging


    sql_logger = logging.getLogger('query')

    @app.before_request
    def before_request():
        pass

    @app.after_request
    def query_log(resp):
        if app.config['SQLALCHEMY_RECORD_QUERIES'] == False:
            pass
        for query in get_debug_queries():
            if query.duration >= app.config['DB_QUERY_TIMEOUT']:
                sql_logger.warn(
                            ('Context:{}\nSLOW QUERY: {}\nParameters: {}\n'
                                'Duration: {}\n').format(query.context, query.statement, 
                                query.parameters, query.duration))
        return resp




def configure_blueprints(app):
    """Configure blueprints in vies."""

    from user import user
    from frontend import frontend
    from api import api

    for bp in [user, frontend, api]:
        app.register_blueprint(bp)


def configure_template_filters(app):
    """Configure filters."""

    app.jinja_env.filters["pretty_date"] = pretty_date
    app.jinja_env.filters["format_date"] = format_date
    app.jinja_env.filters["nl2br"] = nl2br


def configure_logging(app):
    """Configure file(info) and email(error) logging."""

    # if app.debug or app.testing:
    # Skip debug and test mode. Just check standard output.
    # return

    import logging
    import os
    from logging.handlers import SMTPHandler
    from logging import getLogger

    # Set info level on logger, which might be overwritten by handers.
    # Suppress DEBUG messages.
    app.logger.setLevel(logging.INFO)

    #info_log
    info_log = os.path.join(app.config['LOG_FOLDER'], 'info.log')
    info_file_handler = logging.handlers.RotatingFileHandler(
        info_log, maxBytes=100000, backupCount=10)
    info_file_handler.setLevel(logging.DEBUG)
    info_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(info_file_handler)

    #query log
    sql_logger = getLogger(name='query')
    sql_log = os.path.join(app.config['LOG_FOLDER'], 'query.log')
    sql_log_handler = logging.handlers.RotatingFileHandler(
        sql_log, maxBytes=100000, backupCount=10)
    sql_log_handler.setLevel(logging.INFO)
    sql_log_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    sql_logger.addHandler(sql_log_handler)

    #api log
    api_logger = getLogger(name='api')
    api_log = os.path.join(app.config['LOG_FOLDER'], 'api.log')
    api_log_handler = logging.handlers.RotatingFileHandler(
        api_log, maxBytes=100000, backupCount=10)
    #api_log_handler.setLevel()
    api_log_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    api_logger.addHandler(api_log_handler)

    #task log
    task_logger = getLogger(name='task')
    task_log = os.path.join(app.config['LOG_FOLDER'], 'task.log')
    task_log_handler = logging.handlers.RotatingFileHandler(
        task_log, maxBytes=100000, backupCount=10)
    task_log_handler.setLevel(logging.INFO)
    task_log_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    task_logger.addHandler(task_log_handler)

    # Testing
    #app.logger.info("testing info.")
    #
    # mail_handler = SMTPHandler(app.config['MAIL_SERVER'],
    #                            app.config['MAIL_USERNAME'],
    #                            app.config['ADMINS'],
    #                            'Your Application Failed!',
    #                            (app.config['MAIL_USERNAME'],
    #                            app.config['MAIL_PASSWORD']))
    # mail_handler.setLevel(logging.ERROR)
    # mail_handler.setFormatter(logging.Formatter(
    #    '%(asctime)s %(levelname)s: %(message)s '
    #    '[in %(pathname)s:%(lineno)d]')
    #)
    # app.logger.addHandler(mail_handler)


def configure_error_handlers(app):

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html", e=error), 404


def initdb():
    db.drop_all()
    db.create_all()



if __name__ == '__main__':
    server = create_app()
    server.run(debug=True)
