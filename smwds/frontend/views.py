from flask import Blueprint, render_template, current_app, request, flash, \
    url_for, redirect, session, abort, g
from flask_login import login_user, logout_user, current_user, login_required
from frontend.form import LoginForm
from user import User

frontend = Blueprint('frontend', __name__, template_folder='../templates')

#frontend = Blueprint('frontend', __name__)
STATIC_URL_ROOT = '//127.0.0.1/static/'

@frontend.before_request
def frontend_before_request():
    g.user = current_user


@frontend.route('/')
@frontend.route('/index')
@login_required
def index():
    index_data = [{ 
                  'user': {
                              'name': session['username'],
                              'remember_me': session['remember_me']
                            }, 
                  'text': 'Bootstrap is beautiful, and Flask is cool!' 
                  }]
    return render_template('index.html',index_data=index_data)


  


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
       return redirect(url_for('frontend.index'))
   

    form = LoginForm()
    
    if form.validate_on_submit():
        
        session['remember_me'] = form.remember_me.data
        user =  User.query.filter_by(name=form.name.data.lower()).first()
        if user and user.check_password(form.password.data):
            current_app.logger.error('user checked')
            session['username'] = form.name.data
            login_user(user,remember=session['remember_me'])
            return redirect(url_for('frontend.index'))
        else:
            current_app.logger.info( 'user '+ form.name.data +' failed with authentication')
            return render_template('login.html',form=form,failed_auth=True)
           

    return render_template('login.html',form=form)


@frontend.route('/logout')
def logout():

    logout_user()
    return redirect(url_for('frontend.index'))
