import time
import logging
from flask import Blueprint, render_template, request, jsonify, session
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

voice_assistant_bp = Blueprint('voice_assistant', __name__, template_folder='templates')

# Configure the Gemini API
os.environ["GEMINI_API_KEY"] = "AIzaSyDc50TUT66SRytWkQS77MOSvjgAx87m-_A"  # Replace <YOUR_API_KEY> with your actual API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

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

            # Generate response using Gemini
            gemini_response = gemini_response_internal(transcription)

            # Return both transcription and Gemini response
            return jsonify({"response": transcription, "gemini_response": gemini_response})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid audio input"}), 400

# Function to generate response from Gemini
def gemini_response_internal(user_message, max_tokens=20):
    try:
        # Explicitly instruct the model to be concise
        prompt = f"Respond in fewer than {max_tokens} tokens: {user_message}"
        response = model.generate_content(prompt)

        # Post-process response to enforce token limit
        truncated_response = ' '.join(response.text.split()[:max_tokens])
        formatted_response = markdown(truncated_response)

        return formatted_response
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

    # Initialize context in session if not present
    if 'context' not in session:
        session['context'] = {"messages": [], "state": {}}

    # Update context with the user's message
    session['context']["messages"].append({"role": "user", "content": user_message})

    # Generate response using full conversation context
    try:
        # Prepare context for Gemini
        conversation_context = [
            f"{message['role']}: {message['content']}" for message in session['context']["messages"]
        ]
        context_string = "\n".join(conversation_context)
        # Generate response
        response = model.generate_content(context_string)
        formatted_response = markdown(response.text)
        print(response)

        # Update context with the assistant's response
        session['context']["messages"].append({"role": "assistant", "content": formatted_response})
        session.modified = True  # Save changes to the session

        return jsonify({"response": formatted_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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

