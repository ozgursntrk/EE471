"""Translation: French -> English with Helsinki-NLP/opus-mt-fr-en."""
from transformers import pipeline

from common import DEVICE, title

TEXT = "Ce cours est produit par Hugging Face."

translator = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en", device=DEVICE)

title("Translation (French -> English)")
print(f"French  : {TEXT}")
print(f"English : {translator(TEXT)[0]['translation_text']}")
