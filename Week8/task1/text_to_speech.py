"""Text-to-Speech: turns text into speech (Phonon 31M voice model, runs on the CPU).

    python text_to_speech.py ["your text"]
Saves outputs/speech.wav (also used as input by the audio classifier and transcriber demos).
"""
import sys

from common import BaseOptions, model, output_path, title, write_wav
import mediapipe as mp

TEXT = (sys.argv[1] if len(sys.argv) > 1 else
        "Hello, this is EE 471. MediaPipe can turn text into speech directly on my laptop.")

options = mp.tasks.audio.TextToSpeechOptions(
    base_options=BaseOptions(model_asset_path=model("phonon_int8.litertlm")),
)
with mp.tasks.audio.TextToSpeech.create_from_options(options) as tts:
    voices = tts.list_voices()
    result = tts.synthesize(TEXT)

title("Text-to-Speech")
print("Voices in this model:", ", ".join(v.voice_id for v in voices))
print(f"Text: {TEXT}")
seconds = len(result.samples) / result.sample_rate_hz
print(f"Audio: {seconds:.1f} s at {result.sample_rate_hz} Hz")
write_wav(output_path("speech.wav"), result.samples, result.sample_rate_hz)
print("Saved outputs/speech.wav")
