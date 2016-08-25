from flask import Blueprint, render_template, current_app, request, flash, \
    url_for, redirect, session, abort, g
from flask_login import login_user, logout_user, current_user, login_required
from frontend.form import LoginForm
from user import User
from extensions import cache
import uuid, hashlib

frontend = Blueprint('frontend', __name__, template_folder='../templates')

#frontend = Blueprint('frontend', __name__)



@frontend.before_request
def frontend_before_request():
    current_app.logger.info(str(current_user.name) + "@uid:" + str(current_user.id)+ " @session:"+ session.session_id + " @request_url:" + request.url + " @IP:" + ret_ip())
    g.user = current_user



@frontend.teardown_request
def frontend_teardown_request(extensions):
    pass

@frontend.route('/testcache')
@cache.memoize(timeout=60*2)
def testcache():
  name = 'mink'
  return name + " " + str(cache.get('testcache'))


def ret_ip():
  if request.headers.getlist("X-Forwarded-For"):
    t_ip = request.headers.getlist("X-Forwarded-For")[0]
  else:
    t_ip = request.remote_addr
  return t_ip

def ret_index():

  index_data = {
                'user': {
                    'name': session['username'],
                    'remember_me': session['remember_me'],
                    'ip':ret_ip()
                        },
                'text': 'Bootstrap is beautiful, and Flask is cool!'
                }
  return index_data


@frontend.route('/')
@frontend.route('/index')
@login_required
@cache.memoize(timeout=60)
def index():
    #if session_id: 
    #    if g.user.session['sid'] == session_id :
    #        return render_template('index.html', index_data=ret_index())
    #    else :
    #        return redirect(url_for('frontend.login')) 
    s_id = request.args.get('s_id')
    check_id = hashlib.md5(str(session['uid']).encode('utf-8')).hexdigest()
    if s_id == check_id:
        return render_template('index.html', index_data=ret_index())
    else :
        current_app.logger.warning("Session invaild : " + s_id + ' != ' + check_id)
        return redirect(url_for('frontend.logout'))


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    #if g.user is not None and g.user.is_authenticated:
    #    return redirect(url_for('frontend.index'))

    form = LoginForm()

    if form.validate_on_submit():

        session['remember_me'] = form.remember_me.data
        #user = User.query.filter_by(name=form.name.data.lower()).first()
        user,auth = User.authenticate(form.name.data,form.password.data)
        if user and auth:
            current_app.logger.info( form.name.data + ' checked in with data: ' + str(form.remember_me.data))
            session['username'] = form.name.data
            session['log in'] = True
            session['uid'] = str(user.id)
            session['sid'] = hashlib.md5(str(user.id).encode('utf-8')).hexdigest()
            login_user(user, remember=session['remember_me'])
            current_app.logger.info(str(session))
            return redirect(url_for('frontend.index',s_id=session['sid']))
        else:
            current_app.logger.warning(
                'user ' + form.name.data + ' failed with authentication')
            return render_template('login.html', form=form, failed_auth=True)

    return render_template('login.html', form=form)


@frontend.route('/logout')
def logout():

    logout_user()
    return redirect(url_for('frontend.login'))



@frontend.route('/closed')
@login_required
def closed():

    return render_template('closed.html', index_data=ret_index())
