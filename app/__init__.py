# app/__init__.py
from flask import Flask
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_gravatar import Gravatar
import os

from sqlalchemy.orm import DeclarativeBase

from config import Config


# Base declaration for models
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
ckeditor = CKEditor()
bootstrap = Bootstrap5()
login_manager = LoginManager()
mail = Mail()
oauth = OAuth()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    ckeditor.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)

    # Gravatar
    gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

    # Blueprint registration (for modular routing)
    from .auth import auth_bp
    from .oauth import oauth_bp
    from .email import email_bp
    from .roles import roles_bp
    from .routes import routes_bp
    from .blog import blog_bp
    from app.stt import stt_bp
    from .tts import tts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(stt_bp, url_prefix='/stt')
    app.register_blueprint(tts_bp)

    return app
