from flask import Blueprint, render_template, jsonify
from flask_login import current_user
from app.models import UserMood
from datetime import datetime, timedelta
from collections import Counter
import random
from app import db

tone_dashboard_bp = Blueprint('tone_dashboard', __name__, template_folder='templates')

@tone_dashboard_bp.route('/tone-overview')
def tone_overview():
    """Render the tone overview page."""
    return render_template('tone_overview.html')

@tone_dashboard_bp.route('/api/mood-trends')
def get_mood_trends():
    """Fetch mood trend data for visualization."""

    if not current_user.is_authenticated:
        return jsonify({"error": "User not logged in."}), 403

    today = datetime.utcnow().date()
    last_week = today - timedelta(days=7)

    # Fetch mood data for the past 7 days
    moods = UserMood.query.filter(
        UserMood.user_id == current_user.id,
        UserMood.timestamp >= datetime.combine(last_week, datetime.min.time())
    ).order_by(UserMood.timestamp.asc()).all()

    if not moods:
        return jsonify({"message": "No mood data available for analysis."})

    # Count moods per day
    mood_counts = {}
    all_moods = []
    for mood_entry in moods:
        day = mood_entry.timestamp.strftime('%Y-%m-%d')
        if day not in mood_counts:
            mood_counts[day] = {"Happy": 0, "Sad": 0, "Frustrated": 0}
        mood_counts[day][mood_entry.mood] += 1
        all_moods.append(mood_entry.mood)

    # Analyze dominant mood of the week
    dominant_mood = Counter(all_moods).most_common(1)[0][0] if all_moods else "Unknown"

    return jsonify({
        "mood_trends": mood_counts,
        "dominant_mood": dominant_mood,
    })

def insert_sample_moods(user_id):
    moods = ['Happy', 'Sad', 'Frustrated']
    now = datetime.utcnow()
    entries = []

    for i in range(7):  # Last 7 days
        day = now - timedelta(days=i)
        for _ in range(random.randint(2, 4)):  # 2-4 moods per day
            mood = UserMood(
                user_id=user_id,
                mood=random.choice(moods),
                timestamp=day.replace(
                    hour=random.randint(9, 20),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
            )
            entries.append(mood)

    db.session.bulk_save_objects(entries)
    db.session.commit()
    print(f"✅ Inserted {len(entries)} sample mood records for user_id={user_id}")