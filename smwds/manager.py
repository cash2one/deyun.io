import app
import pprint

from flask import Flask, current_app
from flask_script import Manager, prompt_choices, Server
from flask_script.commands import ShowUrls, Clean
from extensions import db
from user import User
from api import Apidb, Location
import uuid

from werkzeug.security import generate_password_hash, check_password_hash


manager = Manager(app.create_app())
manager.add_command("server", Server())
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())


@manager.command
def dumpconfig():
    "Dumps config"
    pprint.pprint(current_app.config)


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
            in the context of the app
    """
    app.initdb()
    testdata()
    return dict(app=app)


@manager.command
def initdb():
    """
    init DB
    """
    app.initdb()
    

@manager.command
def testdata():
    """
    Create test data
    """
    app.initdb()
    demo = User(
                id=uuid.uuid4(),
                name=u'demo',
                email=u'demo@example.com',
                #password=u'123456'
                password=u'123456'
                )
    demolocation = Location(
                id=u'647f1644-112d-44ca-b6c7-e56c986dd697',
                name=u'test'

                )
    demoapi = Apidb(
                id=uuid.uuid4(),
                master_name=u'test api',
                master_ip=u'1.1.1.1',
                master_port=u'1111',
                master_api_url=u'http://api.com/api/',
                master_api_port=u'80',
                username=u'salt',
                password=u'',
                location=demolocation
                )
    
    db.session.add(demo)
    db.session.add(demoapi)
    db.session.add(demolocation)
    db.session.commit()
    print(demolocation.apis)

if __name__ == "__main__":
    manager.run()
