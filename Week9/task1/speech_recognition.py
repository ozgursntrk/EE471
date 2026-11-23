"""Automatic speech recognition with OpenAI's Whisper large v3.

    python speech_recognition.py [file.wav]    (default: samples/speech.wav)
"""
import sys

import torch
from transformers import pipeline

from common import DEVICE, read_wav, sample, title

path = sample(sys.argv[1] if len(sys.argv) > 1 else "speech.wav")
audio, rate = read_wav(path)

asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3", device=DEVICE,
               torch_dtype=torch.float16 if DEVICE == 0 else torch.float32)

title(f"Speech recognition - {path} ({len(audio) / rate:.1f} s)")
print(asr({"raw": audio, "sampling_rate": rate})["text"].strip())
