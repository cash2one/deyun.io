from flask import Blueprint, render_template, current_app, request, flash, \
    url_for, redirect, session, abort, g
from flask_login import login_user, logout_user, current_user, login_required
from frontend.form import LoginForm
from user import User

frontend = Blueprint('frontend', __name__, template_folder='../templates')

#frontend = Blueprint('frontend', __name__)
STATIC_URL_ROOT = '//127.0.0.1/static/'


@frontend.route('/')
def index():
    return render_template('/index.html')


  


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    #if g.user is not None and g.user.is_authenticated():
    #    return redirect(url_for('index'))


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


