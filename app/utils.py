# utils.py
from app.models import User

def get_user_dialect(user_id):
    # Replace this with your actual database query or logic
    user_dialect = User.query.filter_by(id=user_id).first().language  # Example for SQLAlchemy

    if user_dialect is None:
        print(f"No dialect found for user ID {user_id}")
        return "en_US"  # Default value if no dialect is found

    return user_dialect
