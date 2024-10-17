from datetime import date, datetime, timedelta, timezone
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from authlib.integrations.flask_client import OAuth
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import login_user, LoginManager, current_user, logout_user
from models import BlogPost, User, Comment, db
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, LoginForm, RegisterForm, CommentForm, ResetPasswordForm, ForgotPasswordForm, \
    AssignRoleForm
from flask_mail import Mail, Message
import jwt
import os

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Google OAuth configuration
oauth = OAuth(app)

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

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your email provider
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'talhaabbasi568@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'tcum ilkt fyjl wesy'  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = 'talhaabbasi568@gmail.com'

mail = Mail(app)


def send_verification_email(user):
    SECRET_KEY = app.config['SECRET_KEY']

    try:
        # Create JWT token with 1 hour expiration
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
            SECRET_KEY,
            algorithm='HS256'
        )

        # Use url_for with _external=True to generate the full URL for email verification
        verification_link = url_for('verify_email', token=token, _external=True)


        # Create the email message
        msg = Message('Email Verification', recipients=[user.email])
        msg.body = f'Click the link to verify your email: {verification_link}'

        # Send the email
        mail.send(msg)
        print(f'Verification email sent to {user.email}')

    except Exception as e:
        print(f"Error sending verification email: {str(e)}")


@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        # Decode the token to get the user ID
        SECRET_KEY = app.config['SECRET_KEY']
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
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
                flash('Your email has been verified!', 'success')
        else:
            flash('Verification link is invalid or has expired.', 'danger')

    except jwt.ExpiredSignatureError:
        flash('The verification link has expired. Please sign up again.', 'danger')
    except jwt.InvalidTokenError:
        flash('Invalid verification link. Please try again.', 'danger')

    return redirect(url_for('login'))  # Redirect to login page after verification


@app.route('/resend_verification/<email>', methods=["POST"])
def resend_verification(email):
    # Fetch the user by email
    result = db.session.execute(db.select(User).where(User.email == email))
    user = result.scalar()

    if user and not user.is_verified:
        send_verification_email(user)
    else:
        flash("This email is already verified or does not exist.", 'warning')

    return redirect(url_for('verification_page', email=user.email))

@app.route('/verification')
def verification_page():
    user_email = request.args.get('email')
    return render_template('verification.html', email=user_email)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                return abort(403)  # Forbidden if the role doesn't match
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db.init_app(app)


with app.app_context():
    db.create_all()

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@app.route('/register', methods=["GET", "POST"])
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
                flash("A verification email has been sent to your email address. Please check your inbox.", 'info')
                # You could add logic here to resend the verification email if needed
            else:
                flash("Your email is already verified! Please log in.", 'warning')
            return redirect(url_for('login'))

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

        flash('Registration successful! A verification email has been sent.', 'success')
        return redirect(url_for('verification_page', email=new_user.email))

    return render_template("register.html", form=user_form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again or signup.", 'danger')
            return redirect(url_for('login'))

        if not user.is_verified:
            flash('Please verify your email before logging in.', 'danger')
            return redirect(url_for('verification_page', email=email))

        # Check if the user signed up via Google
        elif user.google_registered:
            flash('You registered using Google sign-in. Please use Google to log in.', 'info')
            return redirect(url_for('login'))

        # Password check for non-Google users
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.', 'danger')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form, current_user=current_user)

def generate_reset_token(user, expires_in=3600):  # Token expires in 1 hour
    return jwt.encode(
        {'reset_password': user.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in)},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )


def send_reset_password_email(user):
    token = generate_reset_token(user)
    reset_link = url_for('reset_password', token=token, _external=True)

    msg = Message('Password Reset Request', recipients=[user.email])
    msg.body = f'''To reset your password, click the following link:
{reset_link}

If you did not make this request, please ignore this email.
'''
    mail.send(msg)
    print(f"Password reset email sent to {user.email}")


@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if user:
            send_reset_password_email(user)  # Send password reset email
            flash("An email has been sent with instructions to reset your password.", "info")
        else:
            flash("No account found with that email.", "warning")

        return redirect(url_for('login'))

    return render_template('forgot_password.html', form=form)


@app.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    try:
        SECRET_KEY = app.config['SECRET_KEY']
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = data['reset_password']
        user = db.session.get(User, user_id)

        form = ResetPasswordForm()

        if form.validate_on_submit():
            new_password = form.password.data
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256:600000', salt_length=8)
            db.session.commit()
            flash("Your password has been reset!", "success")
            return redirect(url_for('login'))

        return render_template('reset_password.html', form=form, token=token)

    except jwt.ExpiredSignatureError:
        flash("The password reset link has expired.", "danger")
        return redirect(url_for('forgot_password'))
    except jwt.InvalidTokenError:
        flash("Invalid password reset link.", "danger")
        return redirect(url_for('forgot_password'))


@app.route('/assign-role', methods=["GET", "POST"])
@admin_only  # Ensure only admin users can access
def assign_role():
    form = AssignRoleForm()

    if form.validate_on_submit():
        user_id = form.user.data
        selected_role = form.role.data

        # Fetch the user from the database
        user = User.query.get(user_id)
        if user:
            # Update the role
            user.role = selected_role
            db.session.commit()  # Save changes to the database
            flash(f'Role for {user.email} updated to {selected_role}!', 'success')
        else:
            flash('User not found', 'danger')

        return redirect(url_for('assign_role'))

    return render_template('assign_role.html', form=form)


# Google OAuth login route
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


# callback route to handle Google OAuth login
@app.route('/authorize')
def authorize():
    try:
        # Retrieve the token from the OAuth callback
        token = google.authorize_access_token()

        if not token:
            flash("Authorization failed.", 'danger')
            return redirect(url_for('login'))

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
                flash("You have successfully registered using Google!", 'success')
            else:
                login_user(user)
                print(f"User {user.email} is already registered with Google.")
                flash("You have successfully logged in using Google!", 'success')
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
        return redirect(url_for('get_all_posts'))

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    logout_user()
    flash("You have successfully logged out.","success")
    return redirect(url_for('get_all_posts'))

@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.", "danger")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


if __name__ == "__main__":
    app.run(debug=True)
