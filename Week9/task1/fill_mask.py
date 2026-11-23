"""Mask filling: guess the missing word."""
from transformers import pipeline

from common import DEVICE, title

unmasker = pipeline("fill-mask", model="distilbert/distilroberta-base", device=DEVICE)
mask = unmasker.tokenizer.mask_token          # "<mask>" for this model
sentence = f"To understand generative AI, one must study {mask} well."

title("Fill mask")
print(sentence)
for r in unmasker(sentence, top_k=5):
    print(f"  {r['token_str'].strip():<12} {r['score']:.3f}  ->  {r['sequence']}")
