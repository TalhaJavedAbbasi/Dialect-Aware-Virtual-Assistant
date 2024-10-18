# config.py
import os


class Config:
    SECRET_KEY = os.environ.get('FLASK_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URI", "sqlite:///posts.db")
    # Flask-Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'  # Use your email provider
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Your email. Environment variable mein ja kr edit karo
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # Your email password. Environment variable mein ja kr edit karo
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
