"""Shared settings for the Task 4 scripts."""
import warnings

from transformers import logging

logging.set_verbosity_error()
warnings.filterwarnings("ignore")

# The model from chapter 2 of the course (also used for sentiment analysis in Task 1)
CHECKPOINT = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"


def title(text):
    print(f"\n=== {text} ===")
