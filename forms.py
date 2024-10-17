from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, URL, Email, Regexp, EqualTo
from flask_ckeditor import CKEditorField
from app.models import User


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Please enter a valid email address.")])
    password = PasswordField("Password", validators=[DataRequired(), Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            message="Password must be at least 8 characters long, contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character."
        )])
    show_password = BooleanField('Show Password')
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Please enter a valid email address.")])
    password = PasswordField("Password", validators=[DataRequired()])
    show_password = BooleanField('Show Password')
    submit = SubmitField("Let Me In!")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")

# Forgot Password Form
class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Please enter a valid email address.")])
    submit = SubmitField("Send Reset Link")


# Reset Password Form
class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[
        DataRequired(),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
               message="Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character.")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    show_password = BooleanField('Show Password')
    submit = SubmitField("Reset Password")


class AssignRoleForm(FlaskForm):
    user = SelectField('Select User', choices=[], coerce=int, validators=[DataRequired()])
    role = SelectField('Assign Role', choices=[('user', 'User'), ('admin', 'Admin'), ('guest', 'Guest')], validators=[DataRequired()])
    submit = SubmitField('Update Role')

    def __init__(self, *args, **kwargs):
        super(AssignRoleForm, self).__init__(*args, **kwargs)
        self.user.choices = [(user.id, user.email) for user in User.query.all()]  # Fetch user list
