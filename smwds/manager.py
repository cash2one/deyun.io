import app
import pprint

from flask import Flask, current_app
from flask_script import Manager, prompt_choices, Server
from flask_script.commands import ShowUrls, Clean
from extensions import db
from user import User
from api import Masterdb, Nodedb,Location
from node import Perf
import uuid, random

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
def testdb():  
    """
    test database
    """
    print("User Count: " + str(User.get_count()))
    print("Master Count: " + str(Masterdb.get_count()))
    print("Node Count: " + str(Nodedb.get_count()))
    print("Perf Count: " + str(Perf.get_count()))
    print("Test Node 1 SA: " + str(Perf.get_perf('test node 1')))
    print("Test Node 2 SA: " + str(Perf.get_perf('test node 2')))

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
                password=u'123456'
                )
    demolocation = Location(
                id=u'647f1644-112d-44ca-b6c7-e56c986dd697',
                name=u'test'

                )
    demomaster = Masterdb(
                id=uuid.uuid4(),
                master_name=u'test api',
                master_ip=u'1.1.1.1',
                master_port=u'1111',
                master_api_url=u'http://salt.salt.com/api/',
                master_api_port=u'80',
                username=u'salt',
                password=u'',
                location=demolocation
                )
    demonode1 = Nodedb(
                id=uuid.uuid4(),
                node_name=u'test node 1',
                node_ip=u'1.1.2.1',
                bio=u'test descrption',
                location=demolocation,
                master=demomaster
                )
    demonode2 = Nodedb(
              id=uuid.uuid4(),
              node_name=u'test node 2' ,
              node_ip=u'1.1.2.2',
              bio=u'test descrption',
              location=demolocation,
              master=demomaster
              )
    for i in range(100):
        perf_demo1 = Perf(
                 node_id=demonode1.id,
                 node_name=demonode1.node_name,
                 service="sa",
                 result=True if random.random() > 0.5 else False,
                 value="This is test value",
                     )
        db.session.add(perf_demo1)
        perf_demo2 = Perf(
                 node_id=demonode2.id,
                 node_name=demonode2.node_name,
                 service="sa",
                 result=True if random.random() > 0.5 else False,
                 value="This is test value",
                     )
        db.session.add(perf_demo2)    
    
    db.session.add(demo)
    db.session.add(demomaster)
    db.session.add(demolocation)
    db.session.add(demonode1)
    db.session.add(demonode2)
    db.session.commit()
    print(demolocation.masters)
    print(demomaster.nodes)

if __name__ == "__main__":
    manager.run()
