from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FileField
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired, length,EqualTo, ValidationError, Email
from VolunTier.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), length(min=2, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password =  PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign up')

    def validate_username(self, username):

        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is taken')

    def validate_email(self, email):

        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is taken')
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password =  PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class ProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    skills_needed = StringField('Skills Needed', validators=[DataRequired()])
    submit = SubmitField('Create Project')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    skills_needed = StringField('Skills Needed', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    tags = StringField('Tags', validators=[DataRequired()])
    submit = SubmitField('Post')

class AccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), length(min=2, max=15)])
    skills = StringField('Skills', validators=[DataRequired()])
    contact_info = StringField('Contact Info', validators=[DataRequired()])
    picture = FileField('Update profile picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class ApplicationForm(FlaskForm):
    content = TextAreaField('Application Content', validators=[DataRequired()])
    skills = StringField('Skills', validators=[DataRequired()])
    submit = SubmitField('Apply')