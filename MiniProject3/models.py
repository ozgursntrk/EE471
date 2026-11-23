"""The three AI models behind DreamCanvas, one class each.

    SpeechToText   - Whisper large-v3: microphone recording (WAV) -> text
    ChatBot        - SmolLM2-360M-Instruct: chat history -> short reply
    ImageGenerator - SD-Turbo (Stable Diffusion): prompt -> 512x512 image in one step
"""
import base64
import io
import threading
import wave
import warnings

import numpy as np
import torch
from diffusers import AutoPipelineForText2Image
from transformers import logging, pipeline

logging.set_verbosity_error()
warnings.filterwarnings("ignore")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32


class SpeechToText:
    MODEL = "openai/whisper-large-v3"

    def __init__(self):
        self.pipe = pipeline("automatic-speech-recognition", model=self.MODEL,
                             device=DEVICE, torch_dtype=DTYPE)
        self.lock = threading.Lock()          # one request at a time on the GPU

    @staticmethod
    def read_wav(data, rate=16000):
        """WAV bytes -> mono float32 samples at 16 kHz (what Whisper expects)."""
        with wave.open(io.BytesIO(data), "rb") as f:
            channels, original = f.getnchannels(), f.getframerate()
            pcm = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)
        audio = pcm.reshape(-1, channels).mean(axis=1) / 32768.0
        if original != rate:
            audio = np.interp(np.arange(0, len(audio), original / rate), np.arange(len(audio)), audio)
        return audio.astype(np.float32)

    def transcribe(self, wav_bytes):
        audio = self.read_wav(wav_bytes)
        if len(audio) < 1600:                 # shorter than 0.1 s -> nothing was said
            return ""
        with self.lock:
            result = self.pipe({"raw": audio, "sampling_rate": 16000},
                               generate_kwargs={"language": "english", "task": "transcribe"})
        return result["text"].strip()


class ChatBot:
    MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
    SYSTEM = ("You are DreamCanvas, a friendly assistant inside an image generation app. "
              "Keep your answers short (one to three sentences). When the user asks for an image "
              "prompt, answer with one vivid image description inside double quotes.")
    HISTORY = 6                               # how many previous messages the model sees

    def __init__(self):
        self.pipe = pipeline("text-generation", model=self.MODEL, device=DEVICE, torch_dtype=DTYPE)
        self.lock = threading.Lock()

    def reply(self, messages):
        """messages: [{"role": "user" | "assistant", "content": "..."}, ...] -> reply text"""
        chat = [{"role": "system", "content": self.SYSTEM}] + messages[-self.HISTORY:]
        with self.lock:
            output = self.pipe(chat, max_new_tokens=120, do_sample=True, temperature=0.7, top_p=0.9)
        return output[0]["generated_text"][-1]["content"].strip()


class ImageGenerator:
    MODEL = "stabilityai/sd-turbo"

    def __init__(self):
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            self.MODEL, torch_dtype=DTYPE, variant="fp16" if DEVICE == "cuda" else None)
        self.pipe.to(DEVICE)
        self.pipe.set_progress_bar_config(disable=True)
        self.lock = threading.Lock()

    def generate(self, prompt, steps=1):
        """Prompt -> PNG image as a base64 data URL (the browser can show it directly)."""
        with self.lock:
            # SD-Turbo is trained to work in 1 step and without guidance
            image = self.pipe(prompt=prompt, num_inference_steps=steps, guidance_scale=0.0,
                              width=512, height=512).images[0]
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
