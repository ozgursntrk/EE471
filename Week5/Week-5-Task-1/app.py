import io
import os

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
if not SPEECH_KEY or not SPEECH_REGION:
    raise RuntimeError("SPEECH_KEY and SPEECH_REGION must be set in the .env file")

VOICES = {
    "en-US-JennyNeural": "English (US) – Jenny",
    "en-GB-RyanNeural": "English (UK) – Ryan",
    "tr-TR-EmelNeural": "Turkish – Emel",
}
MAX_CHARS = 1000

app = Flask(__name__)


def synthesize(text, voice):
    """Send text to Azure and return the audio as WAV bytes."""
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = voice
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    # audio_config=None: keep the audio in memory instead of playing it on the speakers
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    details = result.cancellation_details
    raise RuntimeError(details.error_details or str(details.reason))


@app.route("/")
def index():
    return render_template("index.html", voices=VOICES)


@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    voice = data.get("voice", "en-US-JennyNeural")

    if not text:
        return jsonify({"error": "Please enter some text."}), 400
    if len(text) > MAX_CHARS:
        return jsonify({"error": f"Text is too long (max {MAX_CHARS} characters)."}), 400
    if voice not in VOICES:
        return jsonify({"error": "Unknown voice."}), 400

    try:
        audio = synthesize(text, voice)
    except RuntimeError as e:
        return jsonify({"error": f"Azure error: {e}"}), 502

    return send_file(io.BytesIO(audio), mimetype="audio/wav", download_name="speech.wav")


if __name__ == "__main__":
    app.run(debug=True)