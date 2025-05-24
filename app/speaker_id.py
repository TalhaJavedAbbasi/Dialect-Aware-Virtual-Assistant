import os
import tempfile
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from pydub import AudioSegment
from scipy.spatial.distance import cosine

# Path to the folder where known speaker samples are stored
SPEAKER_FOLDER = "speakers"  # e.g., speakers/talha.m4a, speakers/ahmad.wav

# Load encoder once
encoder = VoiceEncoder()
speaker_profiles = {}  # Dictionary: {name: embedding}

def convert_audio_to_wav(input_path, output_path, sample_rate=16000):
    """Convert any audio format to single-channel WAV."""
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(sample_rate)
    audio.export(output_path, format="wav")

def build_speaker_profiles():
    """Embed all known speaker audio files."""
    global speaker_profiles
    speaker_profiles.clear()

    print("🔄 Building speaker profiles...")

    for file in os.listdir(SPEAKER_FOLDER):
        name, ext = os.path.splitext(file)
        input_path = os.path.join(SPEAKER_FOLDER, file)
        temp_wav_path = os.path.join(tempfile.gettempdir(), name + ".wav")

        try:
            convert_audio_to_wav(input_path, temp_wav_path)
            wav = preprocess_wav(temp_wav_path)
            embed = encoder.embed_utterance(wav)
            speaker_profiles[name] = embed
            print(f"✅ Loaded profile for {name}")
        except Exception as e:
            print(f"⚠️ Error processing {file}: {e}")

    print(f"🧠 Total speakers loaded: {len(speaker_profiles)}")

def identify_speaker(audio_path):
    """Compare a new audio chunk against known speaker profiles."""
    try:
        wav = preprocess_wav(audio_path)
        embed = encoder.embed_utterance(wav)

        if not speaker_profiles:
            return "Unknown"

        distances = {
            speaker: cosine(embed, profile)
            for speaker, profile in speaker_profiles.items()
        }

        best_match = min(distances, key=distances.get)
        confidence = 1 - distances[best_match]

        print(f"🔎 Speaker Match: {best_match} (confidence: {confidence:.2f})")

        return best_match if distances[best_match] < 0.4 else "Unknown"

    except Exception as e:
        print(f"❌ Speaker identification error: {e}")
        return "Unknown"
