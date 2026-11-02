import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()  # .env dosyasını bulur (üst klasörlere de bakar)

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("SPEECH_KEY"),
    region=os.getenv("SPEECH_REGION"),
)
audio_config = speechsdk.audio.AudioOutputConfig(filename="test.wav")
synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

result = synthesizer.speak_text_async("Hello, EE471 class").get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("OK: test.wav created")
else:
    print("ERROR:", result.cancellation_details.error_details)