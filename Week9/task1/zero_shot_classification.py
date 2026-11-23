"""Zero-shot classification: pick a label the model was never trained on."""
from transformers import pipeline

from common import DEVICE, title

TEXT = "Berkshire keeps their cash reserves at an extremely high level."
LABELS = ["finance", "sports", "politics", "technology"]

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=DEVICE)
result = classifier(TEXT, candidate_labels=LABELS)

title("Zero-shot classification")
print(TEXT)
for label, score in zip(result["labels"], result["scores"]):
    print(f"  {label:<11} {score:.3f}")
