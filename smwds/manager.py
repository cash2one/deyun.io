import app
import pprint

from flask import Flask, current_app
from flask_script import Manager, prompt_choices, Server
from flask_script.commands import ShowUrls, Clean
from extensions import db
from user import User
from api import Api
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

    return dict(app=app)


@manager.command
def initdb():
    """
    init DB
    """
    app.initdb()
    testdata()


def testdata():
    """
    Create test data
    """
    demo = User(
                id=uuid.uuid4(),
                name=u'demo',
                email=u'demo@example.com',
                #password=u'123456'
                password=u'123456'
                )
    db.session.add(demo)
    db.session.commit()

if __name__ == "__main__":
    manager.run()
