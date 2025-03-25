from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, func
from app import db


# BlogPost Model
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="uncategorized")  # Add this field
    comments = relationship("Comment", back_populates="parent_post")


# User Model
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    google_registered: Mapped[bool] = mapped_column(db.Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(db.Boolean, default=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='user')
    language: Mapped[str] = mapped_column(String(5), default='en')  # Default to English
    theme: Mapped[str] = mapped_column(String(10), default='light')
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    recipients = relationship("Recipient", back_populates="user", cascade="all, delete-orphan")


class UserMood(db.Model):
    __tablename__ = "user_moods"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    mood: Mapped[str] = mapped_column(String(50), nullable=False)  # Happy, Sad, Frustrated
    timestamp: Mapped[DateTime] = mapped_column(DateTime, default=func.now())  # Auto timestamp

    user = relationship("User", back_populates="moods")


User.moods = relationship("UserMood", back_populates="user", cascade="all, delete-orphan")


class CustomCommand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    command_name = db.Column(db.String(100), nullable=False)
    trigger_phrase = db.Column(db.String(255), nullable=False, unique=True)
    action_type = db.Column(db.String(50), nullable=False)
    parameters = db.Column(db.JSON, nullable=True)
    status = db.Column(db.Boolean, default=True)
    activation_schedule = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<CustomCommand {self.command_name}>"


class CommandShortcut(db.Model):
    __tablename__ = "command_shortcuts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    shortcut_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)

    # Relationship to associate multiple commands with a shortcut
    commands = db.relationship("CustomCommand", secondary="shortcut_command_association", backref="shortcuts")


# Association table for many-to-many relationship
shortcut_command_association = db.Table(
    "shortcut_command_association",
    db.Column("shortcut_id", db.Integer, db.ForeignKey("command_shortcuts.id"), primary_key=True),
    db.Column("command_id", db.Integer, db.ForeignKey("custom_command.id"), primary_key=True),
)


class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=False, nullable=False)  # No longer unique globally
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="recipients")

# Comment Model
class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
