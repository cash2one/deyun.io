from flask import Blueprint, render_template, current_app, request, flash, \
    url_for, redirect, session, abort, g
from flask_login import login_user, logout_user, current_user, login_required
from frontend.form import LoginForm
from user import User
from extensions import cache

frontend = Blueprint('frontend', __name__, template_folder='../templates')

#frontend = Blueprint('frontend', __name__)



@frontend.before_request
def frontend_before_request():
    g.user = current_user

@frontend.route('/testcache')
@cache.memoize(timeout=60*2)
def testcache():
  name = 'mink'
  return name + " " + str(cache.get('testcache'))



@frontend.route('/')
@frontend.route('/index')
@login_required
def index():
    index_data = {
                  'user': {
                      'name': session['username'],
                      'remember_me': session['remember_me'],
                      'ip':request.remote_addr

                          },
                  'text': 'Bootstrap is beautiful, and Flask is cool!'
                  }
    return render_template('index.html', index_data=index_data)


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('frontend.index'))

    form = LoginForm()

    if form.validate_on_submit():

        session['remember_me'] = form.remember_me.data
        #user = User.query.filter_by(name=form.name.data.lower()).first()
        user,auth = User.authenticate(form.name.data,form.password.data)
        if user and auth:
            current_app.logger.info( form.name.data + ' checked in with data: ' + str(form.remember_me.data))
            session['username'] = form.name.data
            session['uid'] = user.id
            login_user(user, remember=session['remember_me'])
            return redirect(url_for('frontend.index'))
        else:
            current_app.logger.warning(
                'user ' + form.name.data + ' failed with authentication')
            return render_template('login.html', form=form, failed_auth=True)

    return render_template('login.html', form=form)


@frontend.route('/logout')
def logout():

    logout_user()
    return redirect(url_for('frontend.index'))



@frontend.route('/closed')
@login_required
def closed():

    return render_template('closed.html')
