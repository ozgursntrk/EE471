"""Azure Speech helpers: speech-to-text for commands, text-to-speech for replies."""
import io
import os
import threading
import wave

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()  # reads SPEECH_KEY and SPEECH_REGION from the .env file

VOICE = "en-US-JennyNeural"
SAMPLE_RATE = 16000
MAX_COMMAND_SECONDS = 20

# Words we expect in commands; helps Azure hear "DVD" and "check out" correctly
PHRASES = [
    "create item", "type book", "type DVD", "title", "author", "pages", "duration",
    "list items", "available", "show item", "replace item", "update item",
    "delete item", "check out item", "return item",
]


class AzureError(Exception):
    """Raised when the Azure Speech service returns an error."""


def speech_config():
    key, region = os.getenv("SPEECH_KEY"), os.getenv("SPEECH_REGION")
    if not key or not region:
        raise AzureError("SPEECH_KEY and SPEECH_REGION must be set in the .env file")
    return speechsdk.SpeechConfig(subscription=key, region=region)


# ================= Text-to-speech (the librarian's voice) =================
def synthesize(text):
    """Return the spoken text as WAV bytes."""
    config = speech_config()
    config.speech_synthesis_voice_name = VOICE
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    details = result.cancellation_details
    raise AzureError(details.error_details or str(details.reason))


# ================= Speech-to-text (the user's command) =================
def read_wav(data):
    """Check the uploaded WAV file and return its raw 16 kHz mono samples."""
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            if (wav.getframerate(), wav.getsampwidth(), wav.getnchannels()) != (SAMPLE_RATE, 2, 1):
                raise ValueError("Audio must be 16 kHz, 16-bit, mono WAV.")
            if wav.getnframes() > MAX_COMMAND_SECONDS * SAMPLE_RATE:
                raise ValueError(f"Command is too long (max {MAX_COMMAND_SECONDS} seconds).")
            return wav.readframes(wav.getnframes())
    except (wave.Error, EOFError):
        raise ValueError("The file is not a valid WAV file.")


def recognize(wav_bytes):
    """Return what was said, e.g. 'Check out item 3.'"""
    pcm = read_wav(wav_bytes)
    config = speech_config()
    config.speech_recognition_language = "en-US"

    stream_format = speechsdk.audio.AudioStreamFormat(
        samples_per_second=SAMPLE_RATE, bits_per_sample=16, channels=1
    )
    stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    stream.write(pcm)
    stream.close()
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=config, audio_config=speechsdk.audio.AudioConfig(stream=stream)
    )

    phrases = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
    for phrase in PHRASES:
        phrases.addPhrase(phrase)

    # Continuous recognition: a long "create item ..." sentence can come in several parts
    parts, errors = [], []
    done = threading.Event()

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            parts.append(evt.result.text)

    def on_canceled(evt):
        if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
            errors.append(evt.cancellation_details.error_details)
        done.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda evt: done.set())

    recognizer.start_continuous_recognition()
    done.wait(timeout=MAX_COMMAND_SECONDS + 30)
    recognizer.stop_continuous_recognition()

    if errors:
        raise AzureError(errors[0])
    return " ".join(parts)