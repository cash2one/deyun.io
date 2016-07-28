from flask import Flask,render_template
from flask_bootstrap import Bootstrap
from flask_script import Manager
from datetime import datetime

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route('/')
def index():
  return '<h1>test</h1>'

if __name__ == '__main__':
  app.run(debug=True)