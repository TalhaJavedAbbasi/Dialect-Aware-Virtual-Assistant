from flask import Blueprint, render_template
from flask_login import current_user
from app import db

# Assuming you already have other imports and initializations
routes_bp = Blueprint('routes', __name__)


@routes_bp.before_app_request
def create_tables():
    db.create_all()


@routes_bp.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@routes_bp.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)
