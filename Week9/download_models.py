"""Downloads every model used in Week 9 into the Hugging Face cache (run once, before recording).

    python download_models.py           -> all models (~7 GB in total, Whisper alone is ~3 GB)
    python download_models.py nowhisper -> everything except Whisper

Already downloaded models are skipped, and an interrupted download continues where it stopped.
"""
import sys
import warnings

from transformers import logging, pipeline

logging.set_verbosity_error()
warnings.filterwarnings("ignore")

MODELS = [  # (pipeline type, model, approximate size)
    ("sentiment-analysis", "distilbert/distilbert-base-uncased-finetuned-sst-2-english", "270 MB"),
    ("question-answering", "distilbert/distilbert-base-cased-distilled-squad", "260 MB"),
    ("fill-mask", "distilbert/distilroberta-base", "330 MB"),
    ("ner", "dslim/bert-base-NER", "430 MB"),
    ("translation", "Helsinki-NLP/opus-mt-fr-en", "300 MB"),
    ("text-generation", "HuggingFaceTB/SmolLM2-360M", "720 MB"),
    ("image-classification", "google/vit-base-patch16-224", "350 MB"),
    ("summarization", "sshleifer/distilbart-cnn-12-6", "1.2 GB"),
    ("zero-shot-classification", "facebook/bart-large-mnli", "1.6 GB"),
    ("automatic-speech-recognition", "openai/whisper-large-v3", "3.1 GB"),
]

skip_whisper = len(sys.argv) > 1 and sys.argv[1] == "nowhisper"
for i, (task, model, size) in enumerate(MODELS, 1):
    if skip_whisper and "whisper" in model:
        continue
    print(f"\n[{i}/{len(MODELS)}] {model}  (~{size})", flush=True)
    pipe = pipeline(task, model=model)   # downloads (or finds in the cache) and loads the model
    del pipe
print("\nAll models are in the cache.")
