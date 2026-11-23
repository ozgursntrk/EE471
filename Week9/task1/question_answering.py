"""Question answering: check the NER results by asking questions about the same sentence."""
from transformers import pipeline

from common import DEVICE, title

CONTEXT = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living "
           "and working in the beautiful city İzmir in Türkiye.")
# question -> what the NER script found
CHECKS = {
    "What is the person's name?": "Nate",
    "Which organization does the person work for?": "Izmir Institute of Technology",
    "In which city does the person live?": "İzmir",
}

qa = pipeline("question-answering", model="distilbert/distilbert-base-cased-distilled-squad", device=DEVICE)

title("Question answering")
for question, expected in CHECKS.items():
    r = qa(question=question, context=CONTEXT)
    ok = "OK" if expected.lower() in r["answer"].lower() else "DIFFERENT"
    print(f"{question}\n  answer: {r['answer']}  ({r['score']:.2f})   NER: {expected} -> {ok}")
