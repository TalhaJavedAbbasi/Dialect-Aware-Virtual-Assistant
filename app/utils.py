# utils.py
from app.models import User

import pytz

def format_reminder(reminder, tz_name="Asia/Karachi"):
    """
    Convert a reminder SQLAlchemy object to a JSON-serializable dict,
    with time converted to the specified timezone.
    """
    tz = pytz.timezone(tz_name)
    local_time = reminder.remind_at.replace(tzinfo=pytz.utc).astimezone(tz)

    return {
        "id": reminder.id,
        "message": reminder.message,
        "remind_at": local_time.strftime('%Y-%m-%d %H:%M:%S'),
        "priority": reminder.priority,
        "is_seen": reminder.is_seen,
        "is_muted": reminder.is_muted
    }


def get_user_dialect(user_id):
    # Replace this with your actual database query or logic
    user_dialect = User.query.filter_by(id=user_id).first().language  # Example for SQLAlchemy

    if user_dialect is None:
        print(f"No dialect found for user ID {user_id}")
        return "en_US"  # Default value if no dialect is found

    return user_dialect
