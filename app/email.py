# app/email.py
from flask_mail import Message
from flask import Blueprint, url_for, flash, render_template, redirect, current_app
from .models import User
from app import mail, db
import jwt
from datetime import datetime, timedelta, timezone
from forms import ResetPasswordForm, ForgotPasswordForm
from werkzeug.security import generate_password_hash

email_bp = Blueprint('email', __name__)


def send_verification_email(user):
    SECRET_KEY = current_app.config['SECRET_KEY']

    try:
        # Create JWT token with 1 hour expiration
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
            SECRET_KEY,
            algorithm='HS256'
        )

        # Use url_for with _external=True to generate the full URL for email verification
        verification_link = url_for('auth.verify_email', token=token, _external=True)


        # Create the email message
        msg = Message('Email Verification', recipients=[user.email])
        msg.body = f'Click the link to verify your email: {verification_link}'

        # Send the email
        mail.send(msg)
        print(f'Verification email sent to {user.email}')

    except Exception as e:
        print(f"Error sending verification email: {str(e)}")


def generate_reset_token(user, expires_in=3600):  # Token expires in 1 hour
    return jwt.encode(
        {'reset_password': user.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in)},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )


def send_reset_password_email(user):
    token = generate_reset_token(user)
    reset_link = url_for('email.reset_password', token=token, _external=True)

    msg = Message('Password Reset Request', recipients=[user.email])
    msg.body = f'''To reset your password, click the following link:
{reset_link}

If you did not make this request, please ignore this email.
'''
    mail.send(msg)
    print(f"Password reset email sent to {user.email}")

@email_bp.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if user:
            send_reset_password_email(user)  # Send password reset email
            flash("An email has been sent with instructions to reset your password.Please check your inbox.", "info")
        else:
            flash("No account found with that email.", "warning")

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html', form=form)


@email_bp.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    try:
        SECRET_KEY = current_app.config['SECRET_KEY']
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = data['reset_password']
        user = db.session.get(User, user_id)

        form = ResetPasswordForm()

        if form.validate_on_submit():
            new_password = form.password.data
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256:600000', salt_length=8)
            db.session.commit()
            flash("Your password has been reset!", "success")
            return redirect(url_for('auth.login'))

        return render_template('reset_password.html', form=form, token=token)

    except jwt.ExpiredSignatureError:
        flash("The password reset link has expired.", "danger")
        return redirect(url_for('email.forgot_password'))
    except jwt.InvalidTokenError:
        flash("Invalid password reset link.", "danger")
        return redirect(url_for('email.forgot_password'))

