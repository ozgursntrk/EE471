"""Audio Classifier: what kind of sound is it? (YAMNet, 521 sound classes, ~1 s windows)

    python audio_classifier.py [file.wav]     (default: outputs/speech.wav from text_to_speech.py)
"""
import sys

from common import BaseOptions, model, output_path, read_wav, title
import mediapipe as mp

path = sys.argv[1] if len(sys.argv) > 1 else output_path("speech.wav")
samples, rate = read_wav(path)

options = mp.tasks.audio.AudioClassifierOptions(
    base_options=BaseOptions(model_asset_path=model("yamnet.tflite")),
    max_results=3,
)
with mp.tasks.audio.AudioClassifier.create_from_options(options) as classifier:
    audio = mp.tasks.components.containers.AudioData.create_from_array(samples, rate)
    results = classifier.classify(audio)       # one result per ~1 second window

title(f"Audio Classifier - {path}")
for r in results:
    top = ", ".join(f"{c.category_name} {c.score:.2f}" for c in r.classifications[0].categories)
    print(f"  {r.timestamp_ms / 1000:4.1f} s: {top}")
