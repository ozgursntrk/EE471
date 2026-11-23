"""Text generation: complete a sentence, max 35 words, two alternatives.

    python text_generation.py [seed]     (other seed -> other answers, default 123)
"""
import re
import sys

from transformers import pipeline, set_seed

from common import DEVICE, title

PROMPT = "If I continue to complete all in-class exercises in this modern software practices course,"
MAX_WORDS = 35


def shorten(text):
    """Keep at most MAX_WORDS words and stop at the first full stop after the prompt."""
    text = PROMPT + re.split(r"[\n•]", text[len(PROMPT):])[0]     # drop lists / new lines
    words = text.split()[:MAX_WORDS]
    sentence = " ".join(words)
    end = sentence.find(".", len(PROMPT))
    return sentence[:end + 1] if end != -1 else sentence


set_seed(int(sys.argv[1]) if len(sys.argv) > 1 else 123)   # same seed -> same answers
generator = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M", device=DEVICE)
results = generator(PROMPT, max_new_tokens=50, num_return_sequences=2, do_sample=True, top_p=0.9)

title("Text generation")
for i, r in enumerate(results, 1):
    answer = shorten(r["generated_text"])
    print(f"{i}) {answer}  ({len(answer.split())} words)")
