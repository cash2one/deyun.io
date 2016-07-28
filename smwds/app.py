from flask import Flask,render_template
from flask_bootstrap import Bootstrap
from flask_script import Manager
from config import DefaultConfig
from utils import INSTANCE_FOLDER_PATH
import os

app = Flask(__name__)
bootstrap = Bootstrap(app)



def create_app(config=None, app_name=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = DefaultConfig.PROJECT

    app = Flask(  
        app_name, 
        instance_path=INSTANCE_FOLDER_PATH,
        instance_relative_config=True,
        static_url_path='/_static'
        )
    configure_blueprints(app)

    return app


def configure_blueprints(app):
    """Configure blueprints in vies."""

    #from user import user
    from frontend import frontend
    #from api import api

    #for bp in [user, frontend, api]:
    app.register_blueprint(frontend)


if __name__ == '__main__':
    server = create_app()
    server.run(debug=True)