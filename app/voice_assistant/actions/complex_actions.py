import logging
import webbrowser

from flask_mail import Message
from flask import current_app
from app import mail
from app.models import Recipient
import re
from datetime import datetime

from urllib.parse import quote
import requests

# Specific command handlers
def handle_send_email(command):
    match = re.search(r"send email to (.+?) with subject (.+?) and body (.+)", command, re.IGNORECASE)
    if match:
        name, subject, body = match.groups()

        # Clean up input (trim whitespaces and handle case)
        name = name.strip().lower()  # Normalize the name
        logging.info(f"Received command to send email to '{name}' with subject '{subject}' and body '{body}'")

        try:
            # Lookup recipient in the database
            recipient = Recipient.query.filter_by(name=name).first()
            print(recipient)# Case-insensitive query
            if not recipient:
                # If recipient not found, return registration message and do not proceed with email sending
                #register_url = url_for('voice_assistant.register_recipient', _external=True)
                logging.error(f"Recipient '{name}' not found in the database.")
                return (f"No email found for {name}. Please register the recipient first. "
                        f"<a href='#' data-toggle='modal' data-target='#addRecipientModal'>Click here to register</a>")

            # If recipient found, send the email
            logging.info(f"Sending email to {recipient.name} at {recipient.email} with subject: {subject}")
            send_email(recipient.email, subject, body)  # Only called if recipient exists
            return f"Email sent to {recipient.name} ({recipient.email}) with subject: {subject}."

        except ValueError as ve:
            # Specific error for invalid email format or sending error
            logging.error(f"ValueError: {ve}")
            return f"Failed to send email. Error: {ve}"

        except Exception as e:
            # Catch all other exceptions
            logging.error(f"Error sending email: {e}")
            return "Failed to send email. Please check the email details and try again."

    # Command did not match the expected format
    return "Please provide email details in the format: 'send email to [name] with subject [subject] and body [body]'."


def handle_set_reminder(command):
    match = re.search(r"set reminder for (.+?) at (.+)", command, re.IGNORECASE)
    if match:
        reminder, time = match.groups()
        set_reminder(reminder, time)
        return f"Reminder set for {reminder} at {time}."
    return "Please provide reminder details in the format: 'set reminder for [event] at [time]'."


def send_email(recipient, subject, body):
    """Function to send an email using Flask-Mail."""
    if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient):
        raise ValueError("Invalid email address format.")
    msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=[recipient])
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        raise ValueError(f"Failed to send email. Error: {str(e)}")


def set_reminder(reminder, time):
    """Simulated function to set a reminder with time validation."""
    try:
        reminder_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        print(f"Setting reminder for '{reminder}' at '{reminder_time}'.")
    except ValueError:
        raise ValueError("Invalid time format. Use 'YYYY-MM-DD HH:MM:SS'.")

def handle_search_query(command):
    match = re.search(r"search (.+)", command, re.IGNORECASE)
    if match:
        search_term = match.group(1).strip()
        query_url = f"https://www.google.com/search?q={search_term}"
        webbrowser.open(query_url)
        return f"Searching Google for '{search_term}'."
    return "Please provide a search term in the format: 'search [term]'."


def handle_play_query(command):
    match = re.search(r"play (.+)", command, re.IGNORECASE)
    if match:
        query = match.group(1).strip()
        try:
            # Fetch the first YouTube video result
            search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
            response = requests.get(search_url).text

            # Extract video ID using regex
            video_id_match = re.search(r"\"videoId\":\"([^\"]+)\"", response)
            if video_id_match:
                video_id = video_id_match.group(1)
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(youtube_url)
                return f"Playing '{query}' on YouTube."
            else:
                return "No results found on YouTube."
        except Exception as e:
            return f"Failed to play music. Error: {str(e)}"
    return "Please provide a query in the format: 'play [query]'."
