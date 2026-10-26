import io
import os
import threading
import wave

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
if not SPEECH_KEY or not SPEECH_REGION:
    raise RuntimeError("SPEECH_KEY and SPEECH_REGION must be set in the .env file")

LANGUAGES = {
    "en-US": "English (US)",
    "tr-TR": "Turkish",
}
SAMPLE_RATE = 16000
MAX_SECONDS = 120

app = Flask(__name__)


def read_wav(data):
    """Check that the audio is 16 kHz, 16-bit, mono WAV and return the raw samples."""
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            if (wav.getframerate(), wav.getsampwidth(), wav.getnchannels()) != (SAMPLE_RATE, 2, 1):
                raise ValueError("Audio must be 16 kHz, 16-bit, mono WAV.")
            if wav.getnframes() > MAX_SECONDS * SAMPLE_RATE:
                raise ValueError(f"Audio is too long (max {MAX_SECONDS} seconds).")
            return wav.readframes(wav.getnframes())
    except (wave.Error, EOFError):
        raise ValueError("The file is not a valid WAV file.")


def transcribe(pcm, language):
    """Send raw audio samples to Azure and return the recognized text."""
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_recognition_language = language

    # Push the audio from memory into Azure (no temporary file needed)
    stream_format = speechsdk.audio.AudioStreamFormat(
        samples_per_second=SAMPLE_RATE, bits_per_sample=16, channels=1
    )
    stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    stream.write(pcm)
    stream.close()
    audio_config = speechsdk.audio.AudioConfig(stream=stream)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Continuous recognition: collect every sentence until the audio ends
    sentences, errors = [], []
    done = threading.Event()

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            sentences.append(evt.result.text)

    def on_canceled(evt):
        if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
            errors.append(evt.cancellation_details.error_details)
        done.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda evt: done.set())

    recognizer.start_continuous_recognition()
    done.wait(timeout=MAX_SECONDS + 30)
    recognizer.stop_continuous_recognition()

    if errors:
        raise RuntimeError(errors[0])
    return " ".join(sentences)


@app.route("/")
def index():
    return render_template("index.html", languages=LANGUAGES)


@app.route("/api/stt", methods=["POST"])
def speech_to_text():
    file = request.files.get("audio")
    language = request.form.get("language", "en-US")

    if file is None:
        return jsonify({"error": "No audio file was sent."}), 400
    if language not in LANGUAGES:
        return jsonify({"error": "Unknown language."}), 400

    try:
        pcm = read_wav(file.read())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        text = transcribe(pcm, language)
    except RuntimeError as e:
        return jsonify({"error": f"Azure error: {e}"}), 502

    if not text:
        return jsonify({"error": "No speech could be recognized."}), 422
    return jsonify({"text": text}), 200


if __name__ == "__main__":
    app.run(debug=True)