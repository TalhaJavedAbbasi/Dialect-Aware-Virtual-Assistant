from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, ValidationError
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, URL, Email, Regexp, EqualTo, Length
from flask_ckeditor import CKEditorField
from app.models import User
import re


# Custom email validator function
def validate_email_format(form, field):
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_pattern, field.data) or '.com.com' in field.data:
        raise ValidationError("Please enter a valid email without repeated domains.")


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    category = SelectField(
        "Category",
        choices=[
            ("dialect_origins", "Dialect Origins"),
            ("pronunciation_tips", "Pronunciation Tips"),
            ("common_expressions", "Common Expressions"),
            ("cultural_insights", "Cultural Insights"),
            ("learning_resources", "Learning Resources"),
            ("linguistic_comparisons", "Linguistic Comparisons"),
            ("community_stories", "Community Stories"),
            ("preservation_efforts", "Preservation Efforts"),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            validate_email_format
        ]
    )
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long."),
        Regexp(r'.*[A-Z].*', message="Password must contain at least 1 uppercase letter."),
        Regexp(r'.*[a-z].*', message="Password must contain at least 1 lowercase letter."),
        Regexp(r'.*\d.*', message="Password must contain at least 1 number."),
        Regexp(r'.*[@$!%*?&#].*', message="Password must contain at least 1 special character.")
    ])
    show_password = BooleanField('Show Password')
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Please enter a valid email address."), validate_email_format])
    password = PasswordField("Password", validators=[DataRequired()])
    show_password = BooleanField('Show Password')
    submit = SubmitField("Let Me In!")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


# Forgot Password Form
class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Please enter a valid email address."), validate_email_format])
    submit = SubmitField("Send Reset Link")


# Reset Password Form
class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long."),
        Regexp(r'.*[A-Z].*', message="Password must contain at least 1 uppercase letter."),
        Regexp(r'.*[a-z].*', message="Password must contain at least 1 lowercase letter."),
        Regexp(r'.*\d.*', message="Password must contain at least 1 number."),
        Regexp(r'.*[@$!%*?&#].*', message="Password must contain at least 1 special character.")
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


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(),
            validate_email_format
        ]
    )
    language = SelectField('Preferred Language', choices=[('en', 'English'), ('ur', 'Urdu'), ('pn', 'Punjabi')], validators=[DataRequired()])
    theme = SelectField('Theme', choices=[('light', 'Light'), ('dark', 'Dark')], validators=[DataRequired()])
    submit = SubmitField('Save Changes')
