"""Small helpers shared by the Task 1 scripts."""
import os
import warnings
import wave

import numpy as np
import torch
from transformers import logging

logging.set_verbosity_error()          # hide the long info/warning messages of transformers
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
DEVICE = 0 if torch.cuda.is_available() else -1     # 0 = first GPU, -1 = CPU


def sample(name):
    """Path of a file in samples/ (or any path that already exists)."""
    return name if os.path.exists(name) else os.path.join(HERE, "samples", name)


def title(text):
    print(f"\n=== {text} ===")


def read_wav(path, rate=16000):
    """16-bit WAV file -> mono float32 samples at 16 kHz (what Whisper expects)."""
    with wave.open(path, "rb") as f:
        channels, original = f.getnchannels(), f.getframerate()
        pcm = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)
    audio = pcm.reshape(-1, channels).mean(axis=1) / 32768.0
    if original != rate:      # simple resampling, no extra library needed
        audio = np.interp(np.arange(0, len(audio), original / rate), np.arange(len(audio)), audio)
    return audio.astype(np.float32), rate
