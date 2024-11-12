from flask import Blueprint, request, jsonify
import os
import whisper
import librosa
import soundfile as sf  # Import soundfile for saving audio
import speech_recognition as sr
from pydub import AudioSegment
AudioSegment.ffmpeg = "C:\\ffmpeg\\bin\\ffmpeg.exe"
AudioSegment.ffprobe = "C:\\ffmpeg\\bin\\ffprobe.exe"
stt_bp = Blueprint('stt', __name__)

# Load Whisper model (you can choose 'tiny', 'base', 'small', 'medium', 'large')
model = whisper.load_model("small")  # You can change to another model size if needed


def convert_to_wav(audio_path):
    audio = AudioSegment.from_file(audio_path)
    wav_path = audio_path.rsplit(".", 1)[0] + ".wav"  # Ensure it changes the extension properly
    audio.export(wav_path, format="wav")
    return wav_path

def preprocess_audio(audio_path, accent):
    # Load the audio file
    y, sr = librosa.load(audio_path, sr=None)

    # Accent-specific preprocessing
    if accent == "en-UK":
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=-2)
    elif accent == "en-AU":
        y = librosa.effects.time_stretch(y, rate=0.95)
    elif accent == "en-UR":
        y = librosa.effects.preemphasis(y, coef=0.97)
    print(f"Accent preprocessing applied for: {accent}")

    # Save the processed audio
    temp_processed_audio = os.path.join('instance', 'processed_audio.wav')
    sf.write(temp_processed_audio, y, sr)
    print(f"Processed audio saved to: {temp_processed_audio}")

    return temp_processed_audio

def transcribe_with_speech_recognition(audio_path, accent):
    recognizer = sr.Recognizer()
    accent_map = {
        "en-US": "en-US",
        "en-UK": "en-GB",
        "en-AU": "en-AU",
        "en-UR": "en-IN"  # Using en-US as a placeholder for Urdu-English
    }
    selected_accent = accent_map.get(accent, "en-US")

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language=selected_accent)
    except sr.UnknownValueError:
        text = "Audio not clear enough to transcribe."
    except sr.RequestError:
        text = "Could not request results from Google Speech Recognition service."

    return text

@stt_bp.route('/transcribe_audio', methods=['POST'])
def transcribe_audio():
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio data found"}), 400

        # Save the uploaded audio
    audio_file = request.files['audio_data']
    audio_dir = os.path.join('instance', 'audio')

    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    audio_path = os.path.join(audio_dir, 'temp_audio')
    audio_file.save(audio_path)

    # Convert to WAV if not already in WAV format
    if not audio_path.lower().endswith('.wav'):
        audio_path = convert_to_wav(audio_path)  # Convert the audio to WAV
        print(f"Audio converted to WAV: {audio_path}")

    # Get the selected accent and approach
    accent = request.form.get("accent", "en-US")
    approach = request.form.get("approach", "whisper")

    # Transcribe based on the selected approach
    if approach == "sr":
        transcription = transcribe_with_speech_recognition(audio_path, accent)
        print("In SR.")
    else:
        # Default to Whisper
        # Preprocess audio according to accent
        processed_audio_path = preprocess_audio(audio_path, accent)
        result = model.transcribe(processed_audio_path)
        transcription = result['text']  # Whisper returns result in 'text'

    return jsonify({"transcription": transcription})
