"""Audio Transcriber: speech-to-text on the device (Parakeet TDT 0.6B).

    python audio_transcriber.py [file.wav]    (default: outputs/speech.wav from text_to_speech.py)
"""
import sys

from common import BaseOptions, model, output_path, read_wav, title
import mediapipe as mp

path = sys.argv[1] if len(sys.argv) > 1 else output_path("speech.wav")
samples, rate = read_wav(path)

options = mp.tasks.audio.AudioTranscriberOptions(
    base_options=BaseOptions(model_asset_path=model("parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm")),
    sample_rate_hz=rate,
)
with mp.tasks.audio.AudioTranscriber.create_from_options(options) as transcriber:
    result = transcriber.transcribe(samples, end_of_stream=True)

title(f"Audio Transcriber - {path} ({len(samples) / rate:.1f} s)")
print(f"Text: {result.text}")
for s in result.segments:
    print(f"  {s.from_timestamp_ms / 1000:5.1f}-{s.to_timestamp_ms / 1000:5.1f} s  {s.transcript}")
