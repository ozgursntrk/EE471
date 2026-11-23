"""DreamCanvas - a simple chatbot web app with speech input and image generation.

    python app.py      -> open http://127.0.0.1:5000
"""
import time

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from models import DEVICE, ChatBot, ImageGenerator, SpeechToText

app = Flask(__name__)

# ---------- load the three models once, when the server starts ----------
print(f"Loading models on {DEVICE} ...")
start = time.time()
speech_to_text = SpeechToText()
chatbot = ChatBot()
image_generator = ImageGenerator()
print(f"All models loaded in {time.time() - start:.0f} s")


# ---------- errors are returned as JSON ----------
@app.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify({"error": e.description}), e.code


def read_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")
    return data


# ---------- page ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- API ----------
@app.post("/api/transcribe")
def transcribe():
    """Microphone recording (WAV file) -> text."""
    audio = request.files.get("audio")
    if audio is None:
        raise ValueError("No audio file in the request")
    return jsonify({"text": speech_to_text.transcribe(audio.read())})


@app.post("/api/chat")
def chat():
    """Chat history -> the chatbot's reply."""
    messages = read_json().get("messages")
    if not messages or not all(isinstance(m, dict) and m.get("role") in ("user", "assistant")
                               and isinstance(m.get("content"), str) for m in messages):
        raise ValueError("'messages' must be a list of {role, content} objects")
    return jsonify({"reply": chatbot.reply(messages)})


@app.post("/api/generate-image")
def generate_image():
    """Text prompt -> generated image."""
    prompt = str(read_json().get("prompt", "")).strip()
    if not prompt:
        raise ValueError("Please write a prompt first")
    start = time.time()
    image = image_generator.generate(prompt)
    return jsonify({"image": image, "seconds": round(time.time() - start, 2)})


if __name__ == "__main__":
    # use_reloader=False: otherwise Flask starts twice and loads the models twice
    app.run(debug=True, use_reloader=False)
