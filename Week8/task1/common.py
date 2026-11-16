"""Small helpers shared by all demo scripts."""
import os
import sys

import wave

import cv2
import mediapipe as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BaseOptions = mp.tasks.BaseOptions
vision = mp.tasks.vision


def model(name):
    """Path of a model in models/ (run download.py first)."""
    path = os.path.join(HERE, "models", name)
    if not os.path.exists(path):
        sys.exit(f"Model not found: models/{name}  ->  run: python download.py")
    return path


def sample(name):
    """Path of an input file in samples/ (or any path given on the command line)."""
    path = name if os.path.exists(name) else os.path.join(HERE, "samples", name)
    if not os.path.exists(path):
        sys.exit(f"Input not found: {name}")
    return path


def input_path(default):
    """The first command-line argument, or the default sample."""
    return sample(sys.argv[1] if len(sys.argv) > 1 else default)


def load_image(path):
    """Return (MediaPipe image for the model, OpenCV BGR image for drawing)."""
    return mp.Image.create_from_file(path), cv2.imread(path)


def save(image, name):
    """Save the result image to outputs/ and print where it is."""
    os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
    path = os.path.join(HERE, "outputs", name)
    cv2.imwrite(path, image)
    print(f"Saved outputs/{name}")


def to_pixels(image, point):
    """Normalized (0..1) landmark -> pixel coordinates."""
    h, w = image.shape[:2]
    return int(point.x * w), int(point.y * h)


def draw_landmarks(image, landmarks, color, connections=(), radius=3):
    """Draw landmark points and the lines between them."""
    for c in connections:
        cv2.line(image, to_pixels(image, landmarks[c.start]),
                 to_pixels(image, landmarks[c.end]), color, 2)
    for p in landmarks:
        cv2.circle(image, to_pixels(image, p), radius, color, -1)


def draw_box(image, box, label, color=(0, 200, 0)):
    """Draw a bounding box (pixels) with a label."""
    x, y = int(box.origin_x), int(box.origin_y)
    cv2.rectangle(image, (x, y), (x + int(box.width), y + int(box.height)), color, 2)
    cv2.putText(image, label, (x, max(y - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def output_path(name):
    os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
    return os.path.join(HERE, "outputs", name)


def write_wav(path, samples, sample_rate):
    """Float samples (-1..1) -> 16-bit mono WAV file."""
    pcm = (np.clip(np.asarray(samples, dtype=np.float32), -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(int(sample_rate))
        f.writeframes(pcm.tobytes())


def read_wav(path):
    """16-bit WAV file -> (float32 mono samples in -1..1, sample rate)."""
    with wave.open(path, "rb") as f:
        channels, rate = f.getnchannels(), f.getframerate()
        pcm = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)
    samples = pcm.reshape(-1, channels).mean(axis=1) / 32768.0
    return samples.astype(np.float32), rate


def title(text):
    print(f"\n=== {text} ===")
