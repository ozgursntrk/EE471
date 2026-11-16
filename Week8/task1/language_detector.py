"""Language Detector: which language is the text written in? (110 languages)

    python language_detector.py ["your text"]
"""
import sys

from common import BaseOptions, model, title
import mediapipe as mp

TEXTS = [sys.argv[1]] if len(sys.argv) > 1 else [
    "Merhaba, bugün hava çok güzel.",
    "Hello, the weather is very nice today.",
    "Bonjour, il fait très beau aujourd'hui.",
    "Hallo, das Wetter ist heute sehr schön.",
    "こんにちは、今日はとても良い天気です。",
]

options = mp.tasks.text.LanguageDetectorOptions(
    base_options=BaseOptions(model_asset_path=model("language_detector.tflite")),
    max_results=2,
)
title("Language Detector")
with mp.tasks.text.LanguageDetector.create_from_options(options) as detector:
    for text in TEXTS:
        result = detector.detect(text)
        best = ", ".join(f"{p.language_code} {p.probability:.2f}" for p in result.languages)
        print(f"  {text:<45} -> {best}")
