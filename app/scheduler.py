from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template
from flask_mail import Message
from app import create_app, db, mail
from app.models import User, Notification
from datetime import datetime

scheduler = BackgroundScheduler()
app = create_app()

def send_daily_reminder_summaries():
    with app.app_context():
        users = User.query.filter(User.is_verified == True).all()

        for user in users:
            reminders = Notification.query.filter_by(user_id=user.id).order_by(Notification.remind_at.desc()).all()
            if not reminders:
                continue

            html_body = render_template("emails/reminder_summary.html", user=user, reminders=reminders)

            msg = Message(subject="📋 Your Daily Reminder Summary",
                          recipients=[user.email],
                          html=html_body)

            try:
                mail.send(msg)
                print(f"✅ Sent summary to {user.email}")
            except Exception as e:
                print(f"❌ Failed to send to {user.email}: {e}")


# Schedule daily at 8 AM
scheduler.add_job(func=send_daily_reminder_summaries, trigger='cron', hour=8)

#scheduler.add_job(func=send_daily_reminder_summaries, trigger='interval', seconds=30)
