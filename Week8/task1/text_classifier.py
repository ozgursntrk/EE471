"""Text Classifier: is a sentence positive or negative? (BERT trained on movie reviews)

    python text_classifier.py ["your text"]
"""
import sys

from common import BaseOptions, model, title
import mediapipe as mp

TEXTS = [sys.argv[1]] if len(sys.argv) > 1 else [
    "I loved this movie, the actors were brilliant!",
    "The plot was boring and way too long.",
    "It was okay, nothing special.",
]

options = mp.tasks.text.TextClassifierOptions(
    base_options=BaseOptions(model_asset_path=model("bert_classifier.tflite")),
)
title("Text Classifier")
with mp.tasks.text.TextClassifier.create_from_options(options) as classifier:
    for text in TEXTS:
        categories = classifier.classify(text).classifications[0].categories
        scores = ", ".join(f"{c.category_name} {c.score:.2f}" for c in categories)
        print(f"  {text:<50} -> {scores}")
