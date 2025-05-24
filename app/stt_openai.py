import logging

from flask import Blueprint, request, jsonify
import os
import openai
from pydub import AudioSegment
from werkzeug.utils import secure_filename

# Set up the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("OpenAIAPI key is not set. Please configure it.")
else:
    try:
        openai.api_key = api_key
        response = openai.Engine.list()  # Make a basic API request
        print("API key is working correctly. Available engines:", [engine.id for engine in response['data']])
    except Exception as e:
        print("API key is set but not working:", str(e))

# Blueprint for OpenAI STT routes
stt_openai_bp = Blueprint('stt_openai', __name__)

# Function to calculate audio duration and cost
def get_audio_duration_and_cost(audio_path):
    audio = AudioSegment.from_file(audio_path)
    duration_in_sec = len(audio) / 1000  # Convert milliseconds to seconds
    duration_in_min = duration_in_sec / 60  # Convert seconds to minutes
    cost = duration_in_min * 0.006  # OpenAI Whisper cost per minute

    return duration_in_sec, cost

# Convert audio to WAV format if not already
def convert_to_wav(audio_path):
    audio = AudioSegment.from_file(audio_path)
    wav_path = audio_path.rsplit(".", 1)[0] + ".wav"
    audio.export(wav_path, format="wav")
    return wav_path

def transcribe_with_openai(audio_path, language=None):
    duration, estimated_cost = get_audio_duration_and_cost(audio_path)
    print(f"Audio Duration: {duration:.2f} seconds")
    print(f"Estimated Cost: ${estimated_cost:.4f}")

    try:
        logging.info(f"Transcribing audio file: {audio_path}")
        with open(audio_path, "rb") as audio_file:
            if language:
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            else:
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file
                    # 👈 no language passed = auto-detect
                )
        print(f"📢 Whisper detected language: {response.get('language')}")
        return response.get("text", "Transcription failed.")
    except Exception as e:
        return f"Error: {str(e)}"



@stt_openai_bp.route('/transcribe_audio_openai', methods=['POST'])
def transcribe_audio_openai():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio data found"}), 400

    audio_file = request.files['audio']
    filename = secure_filename(audio_file.filename)
    audio_dir = os.path.join('instance', 'audio')
    os.makedirs(audio_dir, exist_ok=True)

    logging.info(f"Received audio file: {filename} for transcription")

    file_path = os.path.join(audio_dir, filename)
    audio_file.save(file_path)

    # Convert to WAV format if needed
    if not file_path.lower().endswith('.wav'):
        file_path = convert_to_wav(file_path)

    # Calculate audio duration and estimated cost
    duration, estimated_cost = get_audio_duration_and_cost(file_path)
    logging.info(f"Audio Duration: {duration:.2f} seconds")
    logging.info(f"Estimated Cost: ${estimated_cost:.4f}")

    # Use OpenAI for transcription
    transcription = transcribe_with_openai(file_path)
    logging.debug(f"Received audio file: {filename}")
    logging.debug(f"Transcription output: {transcription}")

    if not transcription or transcription.startswith("Error:"):
        logging.error(f"Transcription failed for {filename}: {transcription}")
        return jsonify({"error": "Failed to transcribe audio."}), 500

    return jsonify({
        "transcription": transcription,
        "estimated_cost": round(estimated_cost, 4)
    })

