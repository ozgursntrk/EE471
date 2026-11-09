import base64
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, jsonify, render_template, request

# Set in docker-compose: which dataset this website is for, and where the two Cog models run
DATASET = os.environ.get("DATASET", "fashion")
MODELS = {
    "baseline": os.environ.get("BASELINE_URL", "http://localhost:5001"),
    "optimized": os.environ.get("OPTIMIZED_URL", "http://localhost:5002"),
}
TITLES = {
    "fashion": ("👕 Garment Classifier", "Fashion-MNIST: T-shirt, trouser, pullover, dress, coat, "
                                       "sandal, shirt, sneaker, bag, ankle boot"),
    "cifar": ("🚗 CIFAR-10 Classifier", "CIFAR-10: airplane, automobile, bird, cat, deer, "
                                      "dog, frog, horse, ship, truck"),
}
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_MB = 10

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024


@app.get("/")
def index():
    title, subtitle = TITLES[DATASET]
    return render_template("index.html", title=title, subtitle=subtitle)


def predict(name, data_url):
    """Send the image to one Cog model and return its output (or an error)."""
    try:
        response = requests.post(f"{MODELS[name]}/predictions",
                                 json={"input": {"image": data_url}}, timeout=60)
        response.raise_for_status()
        prediction = response.json()
    except requests.RequestException as error:
        app.logger.error("%s model failed: %s", name, error)
        return {"error": f"The {name} model is not reachable."}
    if prediction.get("status") != "succeeded":
        return {"error": prediction.get("error") or "Prediction failed."}
    return prediction["output"]


@app.post("/api/classify")
def classify():
    """Send the uploaded image to both models at the same time."""
    file = request.files.get("image")
    if file is None or file.filename == "":
        return jsonify(error="Please choose an image first."), 400
    if file.mimetype not in ALLOWED_TYPES:
        return jsonify(error="Only JPG, PNG or WEBP images are supported."), 400

    encoded = base64.b64encode(file.read()).decode("ascii")
    data_url = f"data:{file.mimetype};base64,{encoded}"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {name: pool.submit(predict, name, data_url) for name in MODELS}
        results = {name: future.result() for name, future in futures.items()}
    return jsonify(results)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify(error=f"The image is larger than {MAX_MB} MB."), 413


if __name__ == "__main__":
    app.run(debug=True, port=8000)