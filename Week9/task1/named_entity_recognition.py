"""Named entity recognition: find the person, the organization and the places."""
from transformers import pipeline

from common import DEVICE, title

TEXT = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living "
        "and working in the beautiful city İzmir in Türkiye.")
TYPES = {"PER": "person", "ORG": "organization", "LOC": "location", "MISC": "other"}

ner = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple", device=DEVICE)


def merge_pieces(entities):
    """The tokenizer splits rare letters ("Türkiye" -> "T" + "ürkiye"); join touching pieces of one type."""
    merged = []
    for e in entities:
        if merged and merged[-1]["entity_group"] == e["entity_group"] and merged[-1]["end"] == e["start"]:
            merged[-1]["end"] = e["end"]
            merged[-1]["score"] = min(merged[-1]["score"], e["score"])
        else:
            merged.append(dict(e))
    return merged


title("Named entity recognition")
print(TEXT)
for e in merge_pieces(ner(TEXT)):
    word = TEXT[e["start"]:e["end"]]          # take the word from the text (keeps "İ" correct)
    print(f"  {TYPES[e['entity_group']]:<13} {word:<32} {e['score']:.3f}")
