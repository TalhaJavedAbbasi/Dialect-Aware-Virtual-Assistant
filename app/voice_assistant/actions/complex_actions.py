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
    "ندیم کھوکھر": "nadeem khokhar",
    "غفار": "ghaffar",
    "سمرا": "samra",
    "سائرہ": "saira",
    "اویس": "awais",
    "ایاز": "ayyaz",
}


def transliterate_urdu_to_english(text):
    """Simple mapping-based transliteration from Urdu to English."""
    return NAME_MAPPING.get(text.strip(), text.strip().lower())  # Default to lower-case if no match

from langdetect import detect

def detect_language(text):
    """Detect language of the input text with better error handling and manual fallback."""
    try:
        # Detect language using langdetect
        lang = detect(text)
        logging.info(f"Detected language: {lang}")
        if lang in ["en", "ur"]:
            return lang
    except Exception as e:
        logging.error(f"Language detection failed: {e}")

    # Manual check for Urdu characters if langdetect fails
    if re.search(r'[\u0600-\u06FF]', text):
        logging.info("Fallback: Detected Urdu based on character presence")
        return "ur"

    return "en"



def get_response_in_language(lang, urdu_msg, english_msg):
    """Return appropriate response based on detected language."""
    logging.info(f"Returning response in language: {lang}")
    return urdu_msg if lang == 'ur' else english_msg


def handle_send_email(command):
    logging.info(f"Received command: {command}")
    lang = detect_language(command)

    match = re.search(
        r"(?:to|ای میل\s+بھیجیں)\s+(.+?)\s+(?:with subject|کو\s+جس\s+کا\s+عنوان)\s+(.+?)\s+(?:and body|اور\s+پیغام)\s+(.+)",
        command,
        re.IGNORECASE
    )

    if match:
        name_urdu, subject, body = match.groups()
        name = transliterate_urdu_to_english(name_urdu.strip())

        logging.info(f"Processed recipient name: {name}")

        try:
            recipient = Recipient.query.filter_by(name=name).first()
            if not recipient:
                logging.error(f"Recipient '{name}' not found in the database.")
                return get_response_in_language(
                    lang,
                    f"کوئی ای میل {name} کے لئے نہیں ملی۔ براہ کرم پہلے وصول کنندہ کو رجسٹر کریں۔ "
                    f"<a href='#' data-toggle='modal' data-target='#addRecipientModal'>یہاں رجسٹر کریں</a>",
                    f"No email found for {name}. Please register the recipient first. "
                    f"<a href='#' data-toggle='modal' data-target='#addRecipientModal'>Click here to register</a>"
                )

            logging.info(f"Sending email to {recipient.name} at {recipient.email} with subject: {subject}")
            send_email(recipient.email, subject, body)
            return get_response_in_language(
                lang,
                f"{recipient.name} ({recipient.email}) کو ای میل بھیج دی گئی۔",
                f"Email sent to {recipient.name} ({recipient.email}) with subject: {subject}."
            )

        except ValueError as ve:
            logging.error(f"ValueError: {ve}")
            return get_response_in_language(
                lang,
                f"ای میل بھیجنے میں ناکامی۔ خرابی: {ve}",
                f"Failed to send email. Error: {ve}"
            )

        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return get_response_in_language(
                lang,
                "ای میل بھیجنے میں ناکامی۔ براہ کرم تفصیلات چیک کریں اور دوبارہ کوشش کریں۔",
                "Failed to send email. Please check the email details and try again."
            )

    # Format error message with correct language response
    return get_response_in_language(
        lang,
        "براہ کرم ای میل کی تفصیلات اس فارمیٹ میں درج کریں: ' ای میل بھیجیں [نام] کو جس کا عنوان [عنوان] اور پیغام [پیغام]'",
        "Please provide email details in the format: 'send email to [name] with subject [subject] and body [body]'."
    )


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
    lang = detect_language(query)
    if query.strip():
        query_url = f"https://www.google.com/search?q={quote(query.strip())}"
        webbrowser.open(query_url)
        logging.debug(f"[DEBUG] Searching Google for: {query.strip()}")
        return get_response_in_language(
            lang,
            f"گوگل پر '{query.strip()}' کے لئے تلاش کی جا رہی ہے۔",
            f"Searching Google for '{query.strip()}'."
        )

    return get_response_in_language(
        lang,
        "براہ کرم تلاش کی اصطلاح فراہم کریں۔",
        "Please provide a search term."
    )


def handle_play_query(query):
    lang = detect_language(query)

    if query.strip():
        try:
            search_url = f"https://www.youtube.com/results?search_query={quote(query.strip())}"
            response = requests.get(search_url).text

            video_id_match = re.search(r"\"videoId\":\"([^\"]+)\"", response)
            if video_id_match:
                video_id = video_id_match.group(1)
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(youtube_url)
                return get_response_in_language(
                    lang,
                    f"یوٹیوب پر '{query.strip()}' چلایا جا رہا ہے۔",
                    f"Playing '{query.strip()}' on YouTube."
                )

            return get_response_in_language(
                lang,
                "یوٹیوب پر کچھ نہیں ملا۔",
                "No results found on YouTube."
            )
        except Exception as e:
            return get_response_in_language(
                lang,
                f"یوٹیوب پر تلاش ناکام رہی۔ غلطی: {str(e)}",
                f"Failed to search on YouTube. Error: {str(e)}"
            )

    return get_response_in_language(
        lang,
        "براہ کرم گانے کا نام فراہم کریں۔",
        "Please provide the song name."
    )


