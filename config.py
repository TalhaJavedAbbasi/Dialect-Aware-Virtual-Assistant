# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('FLASK_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URI", "sqlite:///posts.db")
    # Flask-Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'  # Use your email provider
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'talhaabbasi568@gmail.com'  # Your email
    MAIL_PASSWORD = 'tcum ilkt fyjl wesy'  # Your email password
    MAIL_DEFAULT_SENDER = 'talhaabbasi568@gmail.com'
