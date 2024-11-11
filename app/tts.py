import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from gtts import gTTS

tts_bp = Blueprint('tts', __name__)

@tts_bp.route('/synthesize', methods=['POST'])
def synthesize():
    text = request.json.get('text')
    accent = request.json.get('voice')

    accent_mapping = {
        "en_US": "en",
        "en_UK": "en-uk",
        "en_AU": "en-au",
        "ur_PK": "ur",
    }

    language = accent_mapping.get(accent, "en")

    # Define the custom directory for storing audio files
    audio_dir = os.path.join(os.getcwd(), 'audio_files')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    # Define the audio file path
    audio_file_path = os.path.join(audio_dir, "output.mp3")

    try:
        # Generate audio using gTTS and save it to the custom directory
        tts = gTTS(text=text, lang=language)
        tts.save(audio_file_path)

        # Log file creation
        print(f"Audio file created at: {audio_file_path}")

        return jsonify({"audio_url": "/audio/output.mp3"})
    except Exception as e:
        print(f"Error generating audio: {e}")
        return jsonify({"error": "Failed to generate audio."}), 500


@tts_bp.route('/audio/<filename>')
def get_audio(filename):
    audio_dir = os.path.join(os.getcwd(), 'audio_files')
    return send_from_directory(audio_dir, filename)
