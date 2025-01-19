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
NAME_MAPPING = {
    "سامی": "sami",
    "علی": "ali",
    "احمد": "ahmed",
    "فرحان": "farhan",
    "طلحہ": "talha",
    "حمزہ": "hamza",
    "حسن": "hassan",
    "حسین": "hussain",
    "فیصل": "faisal",
    "زید": "zaid",
    "ریحان": "rehan",
    "کاشف": "kashif",
    "عرفان": "irfan",
    "عمران": "imran",
    "نعمان": "numan",
    "شعیب": "shoaib",
    "راشد": "rashid",
    "کامران": "kamran",
    "عامر": "aamir",
    "ارسلان": "arslan",
    "حمید": "hameed",
    "شبیر": "shabbir",
    "یوسف": "yousuf",
    "وقار": "waqar",
    "منصور": "mansoor",
    "مہتاب": "mehtab",
    "ابرار": "abrar",
    "سلمان": "salman",
    "ذیشان": "zeeshan",
    "مظفر": "muzaffar",
    "مدثر": "mudassir",
    "ناصر": "nasir",
    "جاوید": "javed",
    "تنویر": "tanveer",
    "شمریز": "shamrez",
    "رضوان": "rizwan",
    "رفیق": "rafiq",
    "آصف": "asif",
    "بابر": "babar",
    "عارف": "arif",
    "شفیق": "shafiq",
    "سجاد": "sajjad",
    "ادریس": "idrees",
    "فہد": "fahad",
    "صدیق": "siddiq",
    "محبوب": "mehboob",
    "انیس": "anees",
    "عبید": "obaid",
    "رافع": "rafeh",
    "شاہد": "shahid",
    "عابد": "abid",
    "شہزاد": "shehzad",
    "نواز": "nawaz",
    "عاصم": "asim",
    "طاہر": "tahir",
    "نوید": "naveed",
    "سہیل": "sohail",
    "بشیر": "basheer",
    "خالد": "khalid",
    "طارق": "tariq",
    "فاروق": "farooq",
    "مشتاق": "mushtaq",
    "یونس": "younis",
    "لطیف": "lateef",
    "ہمایوں": "humayun",
    "ضیاء": "zia",
    "ابرہیم": "ibrahim",
    "شاکر": "shakir",
    "ندیم": "nadeem",
    "عزیز": "aziz",
    "سلیم": "saleem",
    "قیصر": "qaiser",
    "شفقت": "shafqat",
    "زبیر": "zubair",
}


def transliterate_urdu_to_english(text):
    """Simple mapping-based transliteration from Urdu to English."""
    return NAME_MAPPING.get(text.strip(), text.strip().lower())  # Default to lower-case if no match

def handle_send_email(command):
    print(command)
    match = re.search(
        r"(?:to|کو)\s+(.+?)\s+(?:with\s+subject|کا\s+عنوان)\s+(.+?)\s+(?:and\s+body|اور\s+پیغام)\s+(.+)",
        command,
        re.IGNORECASE
    )

    if match:
        name_urdu, subject, body = match.groups()

        # Convert Urdu name to English using mapping
        name = transliterate_urdu_to_english(name_urdu.strip())

        logging.info(f"Received command to send email to '{name}' with subject '{subject}' and body '{body}'")

        try:
            # Lookup recipient in the database
            recipient = Recipient.query.filter_by(name=name).first()
            if not recipient:
                logging.error(f"Recipient '{name}' not found in the database.")
                return f"No email found for {name}. Please register the recipient first. " \
                       f"<a href='#' data-toggle='modal' data-target='#addRecipientModal'>Click here to register</a>"

            logging.info(f"Sending email to {recipient.name} at {recipient.email} with subject: {subject}")
            send_email(recipient.email, subject, body)
            return f"Email sent to {recipient.name} ({recipient.email}) with subject: {subject}."

        except ValueError as ve:
            logging.error(f"ValueError: {ve}")
            return f"Failed to send email. Error: {ve}"

        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return "Failed to send email. Please check the email details and try again."

    return "براہ کرم ای میل کی تفصیلات درج کریں: 'کو [نام] کا عنوان [عنوان] اور پیغام [پیغام]' یا 'send email to [name] with subject [subject] and body [body]'."

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


def handle_search_query(query):
    if query.strip():
        query_url = f"https://www.google.com/search?q={quote(query.strip())}"
        webbrowser.open(query_url)
        logging.debug(f"[DEBUG] Searching Google for: {query.strip()}")
        return f"گوگل پر تلاش ہو رہی ہے '{query.strip()}'."
    return "براہ کرم تلاش کی اصطلاح فراہم کریں۔"


def handle_play_query(query):
    if query.strip():
        try:
            search_url = f"https://www.youtube.com/results?search_query={quote(query.strip())}"
            response = requests.get(search_url).text

            video_id_match = re.search(r"\"videoId\":\"([^\"]+)\"", response)
            if video_id_match:
                video_id = video_id_match.group(1)
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(youtube_url)
                return f"یوٹیوب پر '{query.strip()}' چل رہا ہے۔"
            return "یوٹیوب پر کچھ نہیں ملا۔"
        except Exception as e:
            return f"یوٹیوب پر تلاش ناکام رہی۔ غلطی: {str(e)}"

    return "براہ کرم گانے کا نام فراہم کریں۔"
