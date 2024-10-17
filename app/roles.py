# app/roles.py
from flask import Blueprint, render_template, flash, redirect, url_for
from forms import AssignRoleForm
from app import db
from .auth import admin_only
from .models import User

roles_bp = Blueprint('roles', __name__)


@roles_bp.route('/assign-role', methods=["GET", "POST"])
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

        return redirect(url_for('roles.assign_role'))

    return render_template('assign_role.html', form=form)
