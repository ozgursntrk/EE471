import io
import os
import threading
import wave

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
if not SPEECH_KEY or not SPEECH_REGION:
    raise RuntimeError("SPEECH_KEY and SPEECH_REGION must be set in the .env file")

# ---------- Settings ----------
VOICES = {
    "en-US-JennyNeural": "English (US) – Jenny",
    "en-GB-RyanNeural": "English (UK) – Ryan",
    "tr-TR-EmelNeural": "Turkish – Emel",
}
LANGUAGES = {  # spoken languages for recognition, diarization and translation
    "en-US": "English (US)",
    "tr-TR": "Turkish",
}
TRANSLATION_TARGETS = {  # languages we can translate into
    "en": "English",
    "tr": "Turkish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
}
PRONUNCIATION_LANGUAGES = {
    "en-US": "English (US)",
    "en-GB": "English (UK)",
}
MAX_CHARS = 1000
SAMPLE_RATE = 16000
MAX_SECONDS = 120
MAX_PRONUNCIATION_SECONDS = 30

app = Flask(__name__)


class AzureError(Exception):
    """Raised when the Azure Speech service returns an error."""


@app.errorhandler(ValueError)
def handle_bad_input(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(AzureError)
def handle_azure_error(e):
    return jsonify({"error": f"Azure error: {e}"}), 502


# ================= Shared helpers =================
def make_speech_config(language=None):
    """Create the Azure configuration with the key and region from .env."""
    config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    if language:
        config.speech_recognition_language = language
    return config


def read_uploaded_audio(max_seconds=MAX_SECONDS):
    """Read the 'audio' file from the request and return its raw 16 kHz mono samples."""
    file = request.files.get("audio")
    if file is None:
        raise ValueError("No audio file was sent.")
    try:
        with wave.open(io.BytesIO(file.read()), "rb") as wav:
            if (wav.getframerate(), wav.getsampwidth(), wav.getnchannels()) != (SAMPLE_RATE, 2, 1):
                raise ValueError("Audio must be 16 kHz, 16-bit, mono WAV.")
            if wav.getnframes() > max_seconds * SAMPLE_RATE:
                raise ValueError(f"Audio is too long (max {max_seconds} seconds).")
            return wav.readframes(wav.getnframes())
    except (wave.Error, EOFError):
        raise ValueError("The file is not a valid WAV file.")


def read_choice(name, options, default):
    """Read a form field and make sure it is one of the allowed options."""
    value = request.form.get(name, default)
    if value not in options:
        raise ValueError(f"Unknown {name}: {value}")
    return value


def make_audio_config(pcm):
    """Push raw audio from memory into Azure (no temporary file needed)."""
    stream_format = speechsdk.audio.AudioStreamFormat(
        samples_per_second=SAMPLE_RATE, bits_per_sample=16, channels=1
    )
    stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    stream.write(pcm)
    stream.close()
    return speechsdk.audio.AudioConfig(stream=stream)


def run_until_audio_ends(recognizer, start, stop):
    """Start a continuous recognizer and wait until the whole audio is processed."""
    errors = []
    done = threading.Event()

    def on_canceled(evt):
        if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
            errors.append(evt.cancellation_details.error_details)
        done.set()

    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda evt: done.set())

    start()
    done.wait(timeout=MAX_SECONDS + 30)
    stop()

    if errors:
        raise AzureError(errors[0])


# ================= 1) Text-to-speech =================
def synthesize(text, voice):
    """Send text to Azure and return the audio as WAV bytes."""
    config = make_speech_config()
    config.speech_synthesis_voice_name = voice
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    # audio_config=None: keep the audio in memory instead of playing it on the speakers
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    details = result.cancellation_details
    raise AzureError(details.error_details or str(details.reason))


# ================= 2) Speech-to-text =================
def transcribe(pcm, language):
    """Return the recognized text of the whole audio."""
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=make_speech_config(language), audio_config=make_audio_config(pcm)
    )
    sentences = []

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            sentences.append(evt.result.text)

    recognizer.recognized.connect(on_recognized)
    run_until_audio_ends(
        recognizer, recognizer.start_continuous_recognition, recognizer.stop_continuous_recognition
    )
    return " ".join(sentences)


# ================= 3) Real-time diarization (who spoke when) =================
def diarize(pcm, language):
    """Return a list of {speaker, text} segments using Azure's conversation transcriber."""
    transcriber = speechsdk.transcription.ConversationTranscriber(
        speech_config=make_speech_config(language), audio_config=make_audio_config(pcm)
    )
    segments = []

    def on_transcribed(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            segments.append({"speaker": evt.result.speaker_id, "text": evt.result.text})

    transcriber.transcribed.connect(on_transcribed)
    run_until_audio_ends(
        transcriber,
        lambda: transcriber.start_transcribing_async().get(),
        lambda: transcriber.stop_transcribing_async().get(),
    )
    return segments


# ================= 4) Speech translation =================
def translate_speech(pcm, source_language, target_language):
    """Recognize speech in one language and translate it into another."""
    config = speechsdk.translation.SpeechTranslationConfig(
        subscription=SPEECH_KEY, region=SPEECH_REGION
    )
    config.speech_recognition_language = source_language
    config.add_target_language(target_language)
    recognizer = speechsdk.translation.TranslationRecognizer(
        translation_config=config, audio_config=make_audio_config(pcm)
    )
    originals, translations = [], []

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech and evt.result.text:
            originals.append(evt.result.text)
            translations.append(evt.result.translations.get(target_language, ""))

    recognizer.recognized.connect(on_recognized)
    run_until_audio_ends(
        recognizer, recognizer.start_continuous_recognition, recognizer.stop_continuous_recognition
    )
    return " ".join(originals), " ".join(translations)


# ================= 5) Pronunciation assessment =================
def assess_pronunciation(pcm, reference_text, language):
    """Compare the spoken audio with the reference text and return scores (0-100)."""
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=make_speech_config(language), audio_config=make_audio_config(pcm)
    )
    assessment_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Word,
        enable_miscue=True,  # also detect skipped (omitted) and extra (inserted) words
    )
    assessment_config.apply_to(recognizer)
    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.NoMatch:
        raise ValueError("No speech could be recognized.")
    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        raise AzureError(result.cancellation_details.error_details)

    scores = speechsdk.PronunciationAssessmentResult(result)
    return {
        "recognized_text": result.text,
        "pronunciation": scores.pronunciation_score,
        "accuracy": scores.accuracy_score,
        "fluency": scores.fluency_score,
        "completeness": scores.completeness_score,
        "words": [
            {"word": w.word, "accuracy": w.accuracy_score, "error": w.error_type}
            for w in scores.words
        ],
    }


# ================= Routes =================
@app.route("/")
def index():
    return render_template(
        "index.html",
        voices=VOICES,
        languages=LANGUAGES,
        targets=TRANSLATION_TARGETS,
        pronunciation_languages=PRONUNCIATION_LANGUAGES,
    )


@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    voice = data.get("voice", "en-US-JennyNeural")

    if not text:
        raise ValueError("Please enter some text.")
    if len(text) > MAX_CHARS:
        raise ValueError(f"Text is too long (max {MAX_CHARS} characters).")
    if voice not in VOICES:
        raise ValueError("Unknown voice.")

    audio = synthesize(text, voice)
    return send_file(io.BytesIO(audio), mimetype="audio/wav", download_name="speech.wav")


@app.route("/api/stt", methods=["POST"])
def speech_to_text():
    pcm = read_uploaded_audio()
    language = read_choice("language", LANGUAGES, "en-US")
    text = transcribe(pcm, language)
    if not text:
        return jsonify({"error": "No speech could be recognized."}), 422
    return jsonify({"text": text}), 200


@app.route("/api/diarize", methods=["POST"])
def diarization():
    pcm = read_uploaded_audio()
    language = read_choice("language", LANGUAGES, "en-US")
    segments = diarize(pcm, language)
    if not segments:
        return jsonify({"error": "No speech could be recognized."}), 422
    return jsonify({"segments": segments}), 200


@app.route("/api/translate", methods=["POST"])
def translation():
    pcm = read_uploaded_audio()
    source = read_choice("source", LANGUAGES, "tr-TR")
    target = read_choice("target", TRANSLATION_TARGETS, "en")
    original, translated = translate_speech(pcm, source, target)
    if not original:
        return jsonify({"error": "No speech could be recognized."}), 422
    return jsonify({"original": original, "translation": translated}), 200


@app.route("/api/pronunciation", methods=["POST"])
def pronunciation():
    pcm = read_uploaded_audio(max_seconds=MAX_PRONUNCIATION_SECONDS)
    language = read_choice("language", PRONUNCIATION_LANGUAGES, "en-US")
    reference_text = (request.form.get("reference_text") or "").strip()
    if not reference_text:
        raise ValueError("Please enter the sentence you will read.")
    return jsonify(assess_pronunciation(pcm, reference_text, language)), 200


if __name__ == "__main__":
    app.run(debug=True)