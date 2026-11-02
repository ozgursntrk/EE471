"""Create dialog.wav: a short conversation between two different Azure voices.
Use it to test the Diarization tab without needing a second person."""
import os

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

SSML = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="en-US-JennyNeural">Hi, did you finish the EE471 assignment?<break time="800ms"/></voice>
  <voice name="en-US-GuyNeural">Almost. I am still working on the speech translation part.<break time="800ms"/></voice>
  <voice name="en-US-JennyNeural">Nice. For me, diarization was the hardest part.<break time="800ms"/></voice>
  <voice name="en-US-GuyNeural">Really? I thought pronunciation assessment was harder.</voice>
</speak>
"""

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("SPEECH_KEY"), region=os.getenv("SPEECH_REGION")
)
audio_config = speechsdk.audio.AudioOutputConfig(filename="dialog.wav")
synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
result = synthesizer.speak_ssml_async(SSML).get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("OK: dialog.wav created")
else:
    print("ERROR:", result.cancellation_details.error_details)