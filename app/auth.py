# app/auth.py
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from forms import RegisterForm, LoginForm
from app import login_manager, db
from .email import send_verification_email
import jwt

auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                return abort(403)  # Forbidden if the role doesn't match
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/register', methods=["GET", "POST"])
def register():
    user_form = RegisterForm()

    if user_form.validate_on_submit():
        user_email = user_form.email.data
        user_password = user_form.password.data
        user_name = user_form.name.data
        role = 'user'

        # Check if the user already exists
        result = db.session.execute(db.select(User).where(User.email == user_email))
        user = result.scalar()

        if user:
            if not user.is_verified:
                send_verification_email(user)
                return redirect(url_for('auth.verification_page', email=user.email))
            else:
                flash(f"{user.name}! your email is already verified! Please log in.", 'warning')
            return redirect(url_for('auth.login'))

        # If the user doesn't exist, create a new user with is_verified=False
        new_user = User(
            email=user_email,
            password=generate_password_hash(user_password, method='pbkdf2:sha256:600000', salt_length=8),
            name=user_name,
            is_verified=False  # Email verification is required
        )
        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user)

        #flash('Registration successful! A verification email has been sent.', 'success')
        return redirect(url_for('auth.verification_page', email=new_user.email))

    return render_template("register.html", form=user_form, current_user=current_user)


@auth_bp.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again or signup.", 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_verified:
            flash('Please verify your email before logging in.', 'danger')
            return redirect(url_for('auth.verification_page', email=email))

        # Check if the user signed up via Google
        elif user.google_registered:
            flash(f'{user.name} You registered using Google sign-in. Please use Google to log in.', 'info')
            return redirect(url_for('auth.login'))

        # Password check for non-Google users
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.', 'danger')
            return redirect(url_for('auth.login'))
        else:
            login_user(user)
            flash(f'Welcome back {user.name}!', 'success')
            return redirect(url_for('blog.get_all_posts'))

    return render_template("login.html", form=form, current_user=current_user)


@auth_bp.route('/verify_email/<token>')
def verify_email(token):
    try:
        # Decode the token to get the user ID
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']

        user = db.session.get(User, user_id)  # Assuming User is your user model
        if user:
            if user.is_verified:
                flash('Your email is already verified!', 'info')
            else:
                # Mark the user as verified
                user.is_verified = True
                db.session.commit()
                login_user(user)
                flash(f'Welcome {user.name}! Your email has been verified!', 'success')
        else:
            flash('Verification link is invalid or has expired.', 'danger')

    except jwt.ExpiredSignatureError:
        flash('The verification link has expired. Please sign up again.', 'danger')
    except jwt.InvalidTokenError:
        flash('Invalid verification link. Please try again.', 'danger')

    return redirect(url_for('auth.login'))  # Redirect to login page after verification


@auth_bp.route('/resend_verification/<email>', methods=["POST"])
def resend_verification(email):
    # Fetch the user by email
    result = db.session.execute(db.select(User).where(User.email == email))
    user = result.scalar()

    if user and not user.is_verified:
        send_verification_email(user)
    else:
        flash("This email is already verified or does not exist.", 'warning')

    return redirect(url_for('auth.verification_page', email=user.email))

@auth_bp.route('/verification')
def verification_page():
    user_email = request.args.get('email')
    return render_template('verification.html', email=user_email)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash("You have successfully logged out.", "success")
    return redirect(url_for('auth.login'))

# Admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

