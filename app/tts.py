import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from gtts import gTTS
from datetime import datetime

tts_bp = Blueprint('tts', __name__)


@tts_bp.route('/synthesize', methods=['POST'])
def synthesize():
    text = request.json.get('text')
    accent = request.json.get('voice')

    # Error handling for empty text input
    if not text:
        return jsonify({"error": "Text cannot be empty."}), 400

    # Mapping accents to language and TLD values for customization
    accent_mapping = {
        "en_US": {"lang": "en", "tld": "com"},       # English (US)
        "en_UK": {"lang": "en", "tld": "co.uk"},     # English (UK)
        "en_AU": {"lang": "en", "tld": "com.au"},    # English (Australia)
        "en_IN": {"lang": "en", "tld": "co.in"},     # English (India)
        "ur_PK": {"lang": "ur", "tld": "com.pk"},    # Urdu (Pakistan)
    }

    # Retrieve accent config or default to US English if accent not found
    selected_accent = accent_mapping.get(accent, {"lang": "en", "tld": "com"})
    language = selected_accent["lang"]
    tld = selected_accent["tld"]

    # Define audio directory and generate a unique filename with a timestamp
    audio_dir = os.path.join(os.getcwd(), 'audio_files')
    os.makedirs(audio_dir, exist_ok=True)
    audio_file_name = f"{accent}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
    audio_file_path = os.path.join(audio_dir, audio_file_name)

    try:
        # Generate audio using gTTS
        tts = gTTS(text=text, lang=language, tld=tld)
        tts.save(audio_file_path)

        # Log file creation
        print(f"Audio file created at: {audio_file_path}")

        return jsonify({"audio_url": f"/audio/{audio_file_name}"})
    except Exception as e:
        print(f"Error generating audio: {e}")
        return jsonify({"error": "Failed to generate audio."}), 500

@tts_bp.route('/audio/<filename>')
def get_audio(filename):
    audio_dir = os.path.join(os.getcwd(), 'audio_files')
    return send_from_directory(audio_dir, filename)
