"""1) Load a model from the Hub, save it to a folder, and load it back from that folder."""
import os

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import CHECKPOINT, title

FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_model")

# load from the Hugging Face Hub (the cache) and save to our own folder
model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT)
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
model.save_pretrained(FOLDER)
tokenizer.save_pretrained(FOLDER)

title("Load & save")
print(f"Saved to {FOLDER}:")
for name in sorted(os.listdir(FOLDER)):
    print(f"  {name:<25} {os.path.getsize(os.path.join(FOLDER, name)) / 1e6:7.2f} MB")

# load again, this time from the folder, and check that it works
model = AutoModelForSequenceClassification.from_pretrained(FOLDER)
tokenizer = AutoTokenizer.from_pretrained(FOLDER)
inputs = tokenizer("I love this course!", return_tensors="pt")
with torch.no_grad():
    probs = model(**inputs).logits.softmax(dim=-1)[0]
label = model.config.id2label[int(probs.argmax())]
print(f"Reloaded model: 'I love this course!' -> {label} ({probs.max():.3f})")
