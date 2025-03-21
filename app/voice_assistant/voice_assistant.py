import time
import logging
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user
from app.stt import transcribe_with_speech_recognition, convert_to_wav
from werkzeug.utils import secure_filename
import google.generativeai as genai
from markdown import markdown
import os
from gtts import gTTS
from flask import send_file
import tempfile
from langdetect import detect
import re
from app import mail, db
from app.models import Recipient
from .command_router import execute_complex_command

voice_assistant_bp = Blueprint('voice_assistant', __name__, template_folder='templates')

# Access the API key directly
gemini_api_key = os.getenv('GEMINI_KEY')

if not gemini_api_key:
    raise ValueError("GEMINI_KEY environment variable is not set. Please configure it.")

# Configure the Gemini API
genai.configure(api_key=gemini_api_key)

# Initialize the Gemini model globally
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Ensure the uploads folder exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

context = {
    "messages": [],  # List of messages
    "state": {}      # Key-value pairs for conversation flags
}

# Function to detect Roman Urdu
def is_roman_urdu(text):
    # A basic check for Roman Urdu words (you can add more patterns or words as needed)
    roman_urdu_keywords = ['kya', 'aap', 'hai', 'nahi', 'tum', 'main', 'kiya']
    # Check if the text contains any common Roman Urdu words
    for word in roman_urdu_keywords:
        if re.search(r'\b' + word + r'\b', text, re.IGNORECASE):
            return True
    return False

# Utility function to determine TTS settings
def determine_tts_settings(text):
    """Determine the appropriate TTS language and TLD based on detected language."""
    try:
        # First, check if the text is Roman Urdu
        if is_roman_urdu(text):
            detected_language = "ur"  # Treat Roman Urdu as Urdu
        else:
            # Detect language using langdetect
            detected_language = detect(text)

        print(detected_language)

        # Map detected languages to TTS settings
        if detected_language == "ur":
            return {"lang": "hi", "tld": "com.pk"}  # Fallback to Hindi for Urdu
        elif detected_language == "en":
            return {"lang": "en", "tld": "co.uk"}  # Use British English for localized accent
        else:
            return {"lang": "en", "tld": "com"}  # Default to generic English
    except Exception:
        # Default settings if detection fails
        return {"lang": "en", "tld": "com"}


@voice_assistant_bp.route('/api/tts', methods=['POST'])
def text_to_speech():
    text = request.json.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        # Determine TTS settings
        tts_settings = determine_tts_settings(text)
        lang = tts_settings["lang"]
        tld = tts_settings["tld"]
        print(lang)
        print(tld)

        # Generate TTS audio
        tts = gTTS(text, lang=lang, tld=tld)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file_path = temp_file.name
            tts.save(temp_file_path)  # Save the TTS output to temp file
            temp_file.close()  # Ensure the file is closed and no longer in use

            # Adding a slight delay to ensure the file is fully written and closed
            time.sleep(0.2)

            # Return the generated file
            return send_file(temp_file_path, mimetype='audio/mpeg', as_attachment=True,
                             download_name='response.mp3')
    except Exception as e:
        # Log the error and return a detailed response
        print(f"Error during TTS generation: {str(e)}")
        return jsonify({"error": "Error generating audio response. Please try again later."}), 500

def process_user_message(user_message):
    logging.debug(f"Processing user message: {user_message}")

    # Initialize context if not present
    if 'context' not in session:
        session['context'] = {"messages": [], "state": {}}

    # Update context with the user's message
    session['context']["messages"].append({"role": "user", "content": user_message})

    # Try to execute a complex command
    command_response = execute_complex_command(user_message)

    if command_response:
        # Recognized and executed a complex command
        formatted_response = markdown(command_response)
        session['context']["messages"].append({"role": "assistant", "content": formatted_response})
        session.modified = True
        return formatted_response

    # If no complex command was recognized, proceed with Gemini response
    logging.debug("Falling back to Gemini for response.")
    conversation_context = [
        f"{message['role']}: {message['content']}" for message in session['context']["messages"]
    ]
    context_string = "\n".join(conversation_context)

    # Use the full context with a concise instruction
    prompt = (
        f"You are a voice assistant. Your interface with users will be voice. You should use short and concise responses, "
        f"avoiding unpronounceable punctuation. Use the following conversation context to respond:\n"
        f"{context_string}\n\n"
        f"User: {user_message}"
    )

    # Generate response from Gemini
    response = model.generate_content(prompt)

    # Format the response as markdown and update context
    formatted_response = markdown(response.text)
    session['context']["messages"].append({"role": "assistant", "content": formatted_response})
    session.modified = True
    return formatted_response




@voice_assistant_bp.route('/api/audio-input', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']

    if audio_file:
        try:
            # Save the uploaded audio file
            filename = secure_filename(audio_file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            audio_file.save(file_path)

            # Convert to WAV format for compatibility
            wav_path = convert_to_wav(file_path)

            # Transcribe audio using SpeechRecognition
            accent = "en-UR"  # Default to Urdu accent, modify as needed
            transcription = transcribe_with_speech_recognition(wav_path, accent)

            # Logging transcription for debugging
            logging.debug(f"Transcription output: {transcription}")

            # Process the transcription with the shared function
            assistant_response = process_user_message(transcription)

            # Return both user and assistant messages
            return jsonify({
                "user_message": transcription,
                "assistant_response": assistant_response
            })

        except Exception as e:
            logging.error(f"Error processing audio: {str(e)}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid audio input"}), 400


# Function to generate response from Gemini
def gemini_response_internal(user_message, max_tokens=20):
    try:
        # Combine concise instruction with the user message
        prompt = (
            f"You are a voice assistant. Your interface with users will be voice. You should use short and concise responses, "
            f"avoiding unpronounceable punctuation. Respond concisely to the following input:\n"
            f"User: {user_message}"
        )

        # Generate content with Gemini
        response = model.generate_content(prompt)

        # Truncate the response to ensure it adheres to the max_tokens limit (if applicable)
        truncated_response = '. '.join(response.text.split('. ')[:3]) + '.'  # Limit to 3 sentences
        return markdown(truncated_response)
    except Exception as e:
        return f"Error generating response: {str(e)}"



# Route for rendering the chat page
@voice_assistant_bp.route('/chat', methods=['GET'])
def chat():
    return render_template('voice_assistant.html')


# API route for processing chat messages
@voice_assistant_bp.route('/api/gemini-response', methods=['POST'])
def gemini_response():
    user_message = request.json.get('message', '')
    logging.debug(f"User message: {user_message}")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Use the shared function for handling complex command checking and context-based response generation
        response = process_user_message(user_message)
        return jsonify({"response": response})

    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return jsonify({"error": f"Validation error: {str(ve)}"}), 400
    except KeyError as ke:
        logging.error(f"Missing data: {str(ke)}")
        return jsonify({"error": f"Missing data: {str(ke)}"}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

@voice_assistant_bp.route('/api/reset-context', methods=['POST'])
def reset_context():
    session['context'] = {"messages": [], "state": {}}
    session.modified = True
    logging.debug(f"Context after reset: {session.get('context')}")
    return jsonify({"message": "Context reset successfully!"})


@voice_assistant_bp.route('/api/get-context', methods=['GET'])
def get_context():
    # Fetch the current context from session
    current_context = session.get('context', {"messages": [], "state": {}})
    return jsonify({"context": current_context})


@voice_assistant_bp.route('/api/register-recipient', methods=['POST'])
def register_recipient():
    data = request.json
    name = data.get('name')
    nickname = data.get('nickname')
    email = data.get('email')

    if not name or not email:
        return jsonify({"error": "Name and email are required."}), 400

    try:
        print(f"Registering recipient: Name={name}, Nickname={nickname}, Email={email}")
        # Check for duplicate email
        if Recipient.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered."}), 400

        user_id = current_user.id  # Flask-Login example
        recipient = Recipient(name=name, nickname=nickname, email=email, user_id=user_id)
        db.session.add(recipient)
        db.session.commit()

        return jsonify({"message": f"Recipient {name} registered successfully!"}), 200
    except Exception as e:
        logging.error(f"Error registering recipient: {e}")
        return jsonify({"error": "Failed to register recipient. Please try again."}), 500
