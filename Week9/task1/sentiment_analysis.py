"""Sentiment analysis: is a sentence positive or negative?"""
from transformers import pipeline

from common import DEVICE, title

SENTENCES = [
    "I've been waiting for a modern software practices course my whole life.",
    "I hate software courses",
]

classifier = pipeline("sentiment-analysis",
                      model="distilbert/distilbert-base-uncased-finetuned-sst-2-english", device=DEVICE)

title("Sentiment analysis")
for sentence, result in zip(SENTENCES, classifier(SENTENCES)):
    print(f"{result['label']:<8} {result['score']:.3f}  {sentence}")
