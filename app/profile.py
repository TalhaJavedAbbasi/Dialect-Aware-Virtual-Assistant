from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from forms import ProfileForm
from app.models import User
from app import db

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.get(current_user.id)
        user.name = form.name.data
        user.email = form.email.data
        user.language = form.language.data
        user.theme = form.theme.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.profile'))
    # Pre-fill the form with current user data
    form.name.data = current_user.name  #
    form.email.data = current_user.email
    form.language.data = current_user.language
    form.theme.data = current_user.theme
    return render_template('profile.html', form=form)


@profile_bp.route('/save-theme', methods=['POST'])
@login_required
def save_theme():
    if request.is_json:
        data = request.get_json()
        theme = data.get('theme')
        if theme and theme in ['light', 'dark']:
            user = User.query.get(current_user.id)
            user.theme = theme
            db.session.commit()
            return {'message': 'Theme updated successfully'}, 200
    return {'message': 'Invalid request'}, 400