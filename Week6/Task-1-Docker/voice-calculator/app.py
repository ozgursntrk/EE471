import io
import json
import os
import re
import threading
import wave

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
if not SPEECH_KEY or not SPEECH_REGION:
    raise RuntimeError("SPEECH_KEY and SPEECH_REGION must be set in the .env file")

VOICE = "en-US-JennyNeural"
SAMPLE_RATE = 16000
MAX_COMMAND_SECONDS = 15
MAX_TTS_CHARS = 100

# Spoken word -> calculator key (from the command table, plus common mishearings)
WORD_TO_KEY = {
    "zero": "0", "oh": "0",
    "one": "1", "won": "1",
    "two": "2", "to": "2", "too": "2",
    "three": "3",
    "four": "4", "for": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8", "ate": "8",
    "nine": "9",
    "point": ".", "dot": ".",
    "over": "/", "divided": "/",
    "times": "*", "multiplied": "*", "x": "*",
    "plus": "+",
    "minus": "-",
    "is": "=", "equals": "=",
}
SYMBOL_TO_KEY = {"+": "+", "-": "-", "*": "*", "×": "*", "/": "/", "÷": "/", "=": "=", ".": "."}

app = Flask(__name__)


class AzureError(Exception):
    """Raised when the Azure Speech service returns an error."""


@app.errorhandler(ValueError)
def handle_bad_input(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(AzureError)
def handle_azure_error(e):
    return jsonify({"error": f"Azure error: {e}"}), 502


# ================= Calculator (from Week 4, no eval) =================
def calculate(a, b, operation):
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            raise ZeroDivisionError("Division by zero")
        return a / b
    raise ValueError("Unknown operation")


# ================= Text-to-speech (the "magical" buttons) =================
def synthesize(text):
    """Send text to Azure and return the audio as WAV bytes."""
    config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    config.speech_synthesis_voice_name = VOICE
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    details = result.cancellation_details
    raise AzureError(details.error_details or str(details.reason))


# ================= Speech-to-text (the microphone button) =================
def read_uploaded_audio():
    """Read the 'audio' file from the request and return its raw 16 kHz mono samples."""
    file = request.files.get("audio")
    if file is None:
        raise ValueError("No audio file was sent.")
    try:
        with wave.open(io.BytesIO(file.read()), "rb") as wav:
            if (wav.getframerate(), wav.getsampwidth(), wav.getnchannels()) != (SAMPLE_RATE, 2, 1):
                raise ValueError("Audio must be 16 kHz, 16-bit, mono WAV.")
            if wav.getnframes() > MAX_COMMAND_SECONDS * SAMPLE_RATE:
                raise ValueError(f"Command is too long (max {MAX_COMMAND_SECONDS} seconds).")
            return wav.readframes(wav.getnframes())
    except (wave.Error, EOFError):
        raise ValueError("The file is not a valid WAV file.")


def recognize_words(pcm):
    """Return what was said as plain lowercase words, e.g. 'five plus two is'."""
    config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    config.speech_recognition_language = "en-US"
    # Detailed output gives the "lexical" form: words, not digits ("five", not "5")
    config.output_format = speechsdk.OutputFormat.Detailed

    stream_format = speechsdk.audio.AudioStreamFormat(
        samples_per_second=SAMPLE_RATE, bits_per_sample=16, channels=1
    )
    stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    stream.write(pcm)
    stream.close()
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=config, audio_config=speechsdk.audio.AudioConfig(stream=stream)
    )

    # Tell Azure which words to expect, so "two" is not heard as "to"
    phrases = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
    for word in ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
                 "nine", "point", "over", "times", "plus", "minus", "is"]:
        phrases.addPhrase(word)

    parts, errors = [], []
    done = threading.Event()

    def on_recognized(evt):
        if evt.result.reason != speechsdk.ResultReason.RecognizedSpeech:
            return
        try:
            parts.append(json.loads(evt.result.json)["NBest"][0]["Lexical"])
        except (KeyError, IndexError, ValueError):
            parts.append(evt.result.text)

    def on_canceled(evt):
        if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
            errors.append(evt.cancellation_details.error_details)
        done.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda evt: done.set())

    recognizer.start_continuous_recognition()
    done.wait(timeout=MAX_COMMAND_SECONDS + 30)
    recognizer.stop_continuous_recognition()

    if errors:
        raise AzureError(errors[0])
    return " ".join(parts)


def words_to_keys(text):
    """Turn 'five plus two is' into ['5', '+', '2', '=']."""
    text = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", text.lower())  # drop sentence dots, keep 2.5
    keys = []
    for token in re.findall(r"[a-z]+|\d|[.+\-*/=×÷]", text):
        if token in WORD_TO_KEY:
            keys.append(WORD_TO_KEY[token])
        elif token.isdigit():
            keys.append(token)
        elif token in SYMBOL_TO_KEY:
            keys.append(SYMBOL_TO_KEY[token])
    return keys


# ================= Routes =================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400
    try:
        a = float(data["a"])
        b = float(data["b"])
        operation = data["operation"]
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid input"}), 400
    try:
        result = calculate(a, b, operation)
    except (ZeroDivisionError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    if result == int(result):
        result = int(result)
    return jsonify({"result": result}), 200


@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text or len(text) > MAX_TTS_CHARS:
        raise ValueError(f"Text must be 1-{MAX_TTS_CHARS} characters.")
    audio = synthesize(text)
    return send_file(io.BytesIO(audio), mimetype="audio/wav")


@app.route("/api/voice-command", methods=["POST"])
def voice_command():
    heard = recognize_words(read_uploaded_audio())
    keys = words_to_keys(heard)
    if not keys:
        return jsonify({"error": f"No calculator command found in: '{heard}'"}), 422
    return jsonify({"heard": heard, "keys": keys}), 200


if __name__ == "__main__":
    app.run(debug=True)