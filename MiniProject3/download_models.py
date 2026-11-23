"""Downloads the two new models of Mini Project 3 (Whisper large-v3 is already in the cache from Week 9).

    python download_models.py      (~3.2 GB: SmolLM2 Instruct ~0.7 GB, SD-Turbo ~2.5 GB)
"""
import torch
from diffusers import AutoPipelineForText2Image
from transformers import AutoModelForCausalLM, AutoTokenizer

print("[1/2] HuggingFaceTB/SmolLM2-360M-Instruct (chatbot)")
AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-360M-Instruct")
AutoModelForCausalLM.from_pretrained("HuggingFaceTB/SmolLM2-360M-Instruct")

print("[2/2] stabilityai/sd-turbo (image generation, fp16 files only)")
AutoPipelineForText2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float16, variant="fp16")

print("Done.")
