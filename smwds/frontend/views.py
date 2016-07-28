from flask import Blueprint, render_template, current_app, request, flash, \
    url_for, redirect, session, abort


frontend = Blueprint('frontend', __name__, template_folder='../templates')

#frontend = Blueprint('frontend', __name__)
STATIC_URL_ROOT = '//127.0.0.1/static/'

@frontend.route('/')
def index():
    return render_template('/login.html')


@frontend.route('/login')
def login():
    return render_template('/login.html')


@frontend.context_processor
def override_url_for():
    return dict(url_for=static_url_for)

def static_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
              file_path = STATIC_URL_ROOT + filename
              return file_path
    else:
        return url_for(endpoint, **values)
