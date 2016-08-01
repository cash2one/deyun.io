from flask_wtf import Form
from wtforms import ValidationError, HiddenField, BooleanField, StringField, \
                PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from flask_wtf.html5 import EmailField

from user import User
from constants import USERNAME_LEN_MIN, USERNAME_LEN_MAX, USERNAME_TIP, \
                    PASSWORD_LEN_MIN, PASSWORD_LEN_MAX, PASSWORD_TIP, \
                    EMAIL_LEN_MIN, EMAIL_LEN_MAX, EMAIL_TIP, \
                    AGREE_TIP


class LoginForm(Form):
    name = StringField('Username', validators=[DataRequired("Please enter your name.")])
    password = PasswordField('Password', validators=[DataRequired("Please enter a password.")])
    remember_me = BooleanField('remember_me', default=False)