from flask import Blueprint, render_template
from flask_login import current_user
from .utils import get_user_dialect
from app import db

# Assuming you already have other imports and initializations
routes_bp = Blueprint('routes', __name__)


@routes_bp.route('/stt')
def stt():
    return render_template('stt.html')


@routes_bp.route('/tts-page', methods=['GET'])
def tts_page():
    # Replace `user_id` with the actual logic to get the user ID
    user_language = get_user_dialect(current_user.id)  # Use current_user.id if using Flask-Login
    print(f"User language: {user_language}")
    return render_template('tts.html', user_language=user_language)



@routes_bp.before_app_request
def create_tables():
    db.create_all()


@routes_bp.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@routes_bp.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)
