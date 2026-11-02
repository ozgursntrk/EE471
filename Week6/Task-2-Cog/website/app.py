import base64
import os

import requests
from flask import Flask, jsonify, render_template, request

# Address of the Cog model server.
# Inside docker compose it is http://model:5000 (the service name), set in docker-compose.yml.
COG_URL = os.environ.get("COG_URL", "http://localhost:5000")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_MB = 10

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/classify")
def classify():
    """Receive the uploaded image and forward it to the Cog model."""
    file = request.files.get("image")
    if file is None or file.filename == "":
        return jsonify(error="Please choose an image first."), 400
    if file.mimetype not in ALLOWED_TYPES:
        return jsonify(error="Only JPG, PNG or WEBP images are supported."), 400

    # Cog expects files as a URL, so we send the image as a base64 data URL
    encoded = base64.b64encode(file.read()).decode("ascii")
    data_url = f"data:{file.mimetype};base64,{encoded}"

    try:
        response = requests.post(
            f"{COG_URL}/predictions",
            json={"input": {"image": data_url}},
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        app.logger.error("Cog request failed: %s", error)
        return jsonify(error="The model server is not reachable."), 502

    prediction = response.json()
    if prediction.get("status") != "succeeded":
        return jsonify(error=prediction.get("error") or "Prediction failed."), 500

    return jsonify(prediction["output"])


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify(error=f"The image is larger than {MAX_MB} MB."), 413


if __name__ == "__main__":
    app.run(debug=True, port=8000)