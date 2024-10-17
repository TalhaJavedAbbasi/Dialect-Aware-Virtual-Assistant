# app/oauth.py
from flask import Blueprint, redirect, url_for, flash
from flask_login import login_user
from werkzeug.security import generate_password_hash
from app import oauth, db
from .models import User
import os

oauth_bp = Blueprint('oauth', __name__)


google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    client_kwargs={
        'scope': 'email profile',
    },
)


@oauth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('oauth.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@oauth_bp.route('/authorize')
def authorize():
    try:
        # Retrieve the token from the OAuth callback
        token = google.authorize_access_token()

        if not token:
            flash("Authorization failed.", 'danger')
            return redirect(url_for('auth.login'))

        # Fetch user info from Google's userinfo endpoint
        user_info_response = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = user_info_response.json()
        print("User info received:", user_info)

        user_email = user_info.get('email')

        # Example logic to check if user exists in the database
        result = db.session.execute(db.select(User).where(User.email == user_email))
        user = result.scalar()

        if user:
            # If the user exists, check if they are registered via Google
            if not user.google_registered:  # Check if the user is already registered via Google
                user.google_registered = True  # Update the field
                user.is_verified = True
                print(f"Updating user {user.email} to have google_registered = True")
                db.session.commit()  # Save changes
                flash(f"Welcome {user.name}! You have successfully registered using Google!", 'success')
            else:
                login_user(user)
                print(f"User {user.email} is already registered with Google.")
                flash(f"Welcome back {user.name}! You have successfully logged in using Google!", 'success')
        else:
            # Register a new user if they do not exist
            new_user = User(
                email=user_email,
                name=user_info.get('name'),
                password=generate_password_hash('default_password', method='pbkdf2:sha256:600000', salt_length=8),
                google_registered = True,
                is_verified= True
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("You have successfully signed up using Google!", 'success')
        return redirect(url_for('blog.get_all_posts'))

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')
        return redirect(url_for('auth.login'))

