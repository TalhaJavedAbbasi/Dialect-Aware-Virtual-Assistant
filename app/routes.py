from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from .utils import get_user_dialect, format_reminder
from app import db, mail
from app.models import Notification  # adjust import path as needed
import csv
from io import StringIO
from flask_mail import Message

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



@routes_bp.route('/api/add-reminder', methods=['POST'])
@login_required
def add_reminder():
    try:
        data = request.get_json()
        message = data.get('message')
        remind_at = datetime.strptime(data.get('remind_at'), '%Y-%m-%d %H:%M:%S')
        priority = data.get('priority', 'normal')

        if not message or not remind_at:
            return jsonify({"error": "Message and remind_at are required."}), 400

        reminder = Notification(
            user_id=current_user.id,
            message=message,
            remind_at=remind_at,
            priority=priority
        )

        db.session.add(reminder)
        db.session.commit()

        return jsonify({"message": "Reminder added successfully."}), 200
    except Exception as e:
        print("Error in /api/add-reminder:", str(e))
        return jsonify({"error": "Failed to add reminder."}), 500



@routes_bp.route('/api/check-reminders')
@login_required
def check_reminders():
    now = datetime.utcnow()
    print("🔍 Checking reminders at:", now)

    due_reminders = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.remind_at <= now,
        Notification.is_seen == False,
        Notification.is_muted == False
    ).all()

    reminders_list = []

    for r in due_reminders:
        r.is_seen = True
        reminders_list.append(format_reminder(r))

        # ✅ Send email
        try:
            formatted = format_reminder(r)

            msg = Message(
                subject="🔔 Reminder: " + r.message[:30],
                recipients=[current_user.email],
                html = render_template("emails/reminder_due.html", reminder=formatted, user=current_user)
            )
            mail.send(msg)
            print(f"📧 Email sent for: {r.message}")
        except Exception as e:
            print("❌ Failed to send email reminder:", e)

    db.session.commit()
    return jsonify({"reminders": reminders_list})


@routes_bp.route('/api/reminder-history')
@login_required
def reminder_history():
    priority = request.args.get('priority')
    muted = request.args.get('muted')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Notification.query.filter_by(user_id=current_user.id)

    if priority:
        query = query.filter_by(priority=priority)

    if muted == "true":
        query = query.filter_by(is_muted=True)
    elif muted == "false":
        query = query.filter_by(is_muted=False)

    # Apply date filter (convert to datetime)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Notification.remind_at >= start_dt)
        except ValueError:
            pass  # ignore invalid date

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # include the whole end date (e.g., 2025-05-19 23:59:59)
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Notification.remind_at <= end_dt)
        except ValueError:
            pass

    search = request.args.get('search')
    if search:
        query = query.filter(Notification.message.ilike(f"%{search}%"))

    reminders = query.order_by(Notification.remind_at.desc()).all()

    history = [format_reminder(r) for r in reminders]

    return jsonify({"reminders": history})


@routes_bp.route('/api/toggle-mute/<int:reminder_id>', methods=['POST'])
@login_required
def toggle_mute(reminder_id):
    reminder = Notification.query.filter_by(id=reminder_id, user_id=current_user.id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    reminder.is_muted = not reminder.is_muted
    db.session.commit()

    return jsonify({
        "message": "Reminder muted" if reminder.is_muted else "Reminder unmuted",
        "is_muted": reminder.is_muted
    })

@routes_bp.route('/api/delete-reminder/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder(reminder_id):
    reminder = Notification.query.filter_by(id=reminder_id, user_id=current_user.id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    db.session.delete(reminder)
    db.session.commit()

    return jsonify({"message": "Reminder deleted successfully."}), 200


@routes_bp.route('/api/reminders/mark-all-seen', methods=['POST'])
@login_required
def mark_all_seen():
    Notification.query.filter_by(user_id=current_user.id).update({Notification.is_seen: True})
    db.session.commit()
    return jsonify({"message": "All reminders marked as seen."})


@routes_bp.route('/api/reminders/mark-all-unseen', methods=['POST'])
@login_required
def mark_all_unseen():
    Notification.query.filter_by(user_id=current_user.id).update({Notification.is_seen: False})
    db.session.commit()
    return jsonify({"message": "All reminders marked as unseen."})


@routes_bp.route('/reminders')
@login_required
def reminders_page():
    return render_template("reminder_history.html", current_user=current_user)


@routes_bp.route('/api/reminder-history/export')
@login_required
def export_reminders_to_csv():

    reminders = get_filtered_reminders(current_user.id)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Message', 'Remind At', 'Priority', 'Seen', 'Muted'])

    for r in reminders:
        f = format_reminder(r)
        writer.writerow([
            f["message"],
            f["remind_at"],
            f["priority"],
            'Yes' if f["is_seen"] else 'No',
            'Yes' if f["is_muted"] else 'No'
        ])


    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={"Content-Disposition": "attachment; filename=reminder_history.csv"})



@routes_bp.route('/api/reminders/email-summary', methods=['POST'])
@login_required
def email_reminder_summary():
    reminders = get_filtered_reminders(current_user.id)

    if not reminders:
        return jsonify({"error": "No reminders to email."}), 400

    # Generate HTML for email
    formatted = [format_reminder(r) for r in reminders]
    html_body = render_template("emails/reminder_summary.html", reminders=formatted, user=current_user)

    # Send email
    msg = Message(subject="Your Reminder Summary",
                  recipients=[current_user.email],
                  html=html_body)

    try:
        mail.send(msg)
        return jsonify({"message": "Summary emailed successfully!"}), 200
    except Exception as e:
        print("Email error:", e)
        return jsonify({"error": "Failed to send email."}), 500


def get_filtered_reminders(user_id):
    priority = request.args.get('priority')
    muted = request.args.get('muted')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Notification.query.filter_by(user_id=user_id)

    if priority:
        query = query.filter_by(priority=priority)
    if muted == "true":
        query = query.filter_by(is_muted=True)
    elif muted == "false":
        query = query.filter_by(is_muted=False)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Notification.remind_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(Notification.remind_at <= end_dt)
        except ValueError:
            pass

    search = request.args.get('search')
    if search:
        query = query.filter(Notification.message.ilike(f"%{search}%"))

    return query.order_by(Notification.remind_at.desc()).all()
