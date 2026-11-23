"""One class for all ten Hugging Face tasks of Task 1.

    from hf_tasks import HuggingFaceTasks
    hf = HuggingFaceTasks()
    hf.sentiment("I love this course")

Each model is loaded the first time its task is used and then kept in memory,
so the app starts fast and only loads what you actually try.
"""
import re
import warnings

import numpy as np
import torch
from transformers import logging, pipeline

logging.set_verbosity_error()
warnings.filterwarnings("ignore")


class HuggingFaceTasks:
    """A small wrapper around transformers pipelines: one method per task."""

    # task name -> (pipeline type, model on the Hugging Face Hub)
    MODELS = {
        "sentiment": ("sentiment-analysis", "distilbert/distilbert-base-uncased-finetuned-sst-2-english"),
        "zero_shot": ("zero-shot-classification", "facebook/bart-large-mnli"),
        "generation": ("text-generation", "HuggingFaceTB/SmolLM2-360M"),
        "fill_mask": ("fill-mask", "distilbert/distilroberta-base"),
        "ner": ("ner", "dslim/bert-base-NER"),
        "qa": ("question-answering", "distilbert/distilbert-base-cased-distilled-squad"),
        "summary": ("summarization", "sshleifer/distilbart-cnn-12-6"),
        "translation": ("translation", "Helsinki-NLP/opus-mt-fr-en"),
        "image": ("image-classification", "google/vit-base-patch16-224"),
        "speech": ("automatic-speech-recognition", "openai/whisper-large-v3"),
    }

    def __init__(self, device=None):
        if device is None:
            device = 0 if torch.cuda.is_available() else -1
        self.device = device
        self._pipelines = {}          # cache: task name -> loaded pipeline

    def _get(self, name):
        """Load a pipeline the first time it is needed, then reuse it."""
        if name not in self._pipelines:
            task, model = self.MODELS[name]
            extra = {}
            if name == "ner":
                extra["aggregation_strategy"] = "simple"      # merge word pieces into whole entities
            if name == "speech" and self.device != -1:
                extra["torch_dtype"] = torch.float16          # half precision on the GPU
            print(f"Loading {model} ...")
            self._pipelines[name] = pipeline(task, model=model, device=self.device, **extra)
        return self._pipelines[name]

    # ---------- text ----------
    def sentiment(self, text):
        """-> {"POSITIVE": 0.99, "NEGATIVE": 0.01}"""
        result = self._get("sentiment")(text, top_k=None)
        return {r["label"]: r["score"] for r in result}

    def zero_shot(self, text, labels):
        """labels: list of strings -> {label: score}"""
        result = self._get("zero_shot")(text, candidate_labels=labels)
        return dict(zip(result["labels"], result["scores"]))

    def generate(self, prompt, max_words=35, n=2, seed=123):
        """Complete the prompt; returns n alternatives with at most max_words words each."""
        torch.manual_seed(seed)
        results = self._get("generation")(prompt, max_new_tokens=50, num_return_sequences=n,
                                          do_sample=True, top_p=0.9)
        answers = []
        for r in results:
            text = prompt + re.split(r"[\n•]", r["generated_text"][len(prompt):])[0]   # drop lists / new lines
            sentence = " ".join(text.split()[:max_words])
            end = sentence.find(".", len(prompt))
            answers.append(sentence[:end + 1] if end != -1 else sentence)
        return answers

    def fill_mask(self, text, top_k=5):
        """Write the gap as [MASK] (or <mask>) -> {word: score}"""
        unmasker = self._get("fill_mask")
        text = text.replace("[MASK]", unmasker.tokenizer.mask_token)
        return {r["token_str"].strip(): r["score"] for r in unmasker(text, top_k=top_k)}

    def ner(self, text):
        """-> list of {"type", "word", "start", "end", "score"}"""
        entities = []
        for e in self._get("ner")(text):
            if entities and entities[-1]["type"] == e["entity_group"] and entities[-1]["end"] == e["start"]:
                entities[-1]["end"] = e["end"]          # "T" + "ürkiye" -> "Türkiye"
                entities[-1]["word"] = text[entities[-1]["start"]:e["end"]]
                continue
            entities.append({"type": e["entity_group"], "word": text[e["start"]:e["end"]],
                             "start": e["start"], "end": e["end"], "score": float(e["score"])})
        return entities

    def answer(self, question, context):
        """-> (answer, score)"""
        r = self._get("qa")(question=question, context=context)
        return r["answer"], r["score"]

    def summarize(self, text, max_length=60, min_length=20):
        summary = self._get("summary")(text, max_length=max_length, min_length=min_length,
                                       do_sample=False)[0]["summary_text"]
        return re.sub(r"\s+([.,])", r"\1", summary).strip()     # "word ." -> "word."

    def translate(self, text):
        """French -> English"""
        return self._get("translation")(text)[0]["translation_text"]

    # ---------- image ----------
    def classify_image(self, image, top_k=3):
        """image: file path or PIL image -> {label: score}"""
        return {r["label"]: r["score"] for r in self._get("image")(image, top_k=top_k)}

    # ---------- audio ----------
    def transcribe(self, audio, sample_rate=None):
        """audio: numpy array (+ sample_rate) or (sample_rate, array) as Gradio gives it."""
        if isinstance(audio, tuple):
            sample_rate, audio = audio
        audio = np.asarray(audio)
        if np.issubdtype(audio.dtype, np.integer):            # 16-bit numbers -> -1..1
            audio = audio / np.iinfo(audio.dtype).max
        if audio.ndim == 2:                                   # stereo -> mono
            audio = audio.mean(axis=1)
        if sample_rate != 16000:                              # Whisper wants 16 kHz
            audio = np.interp(np.arange(0, len(audio), sample_rate / 16000), np.arange(len(audio)), audio)
        result = self._get("speech")({"raw": audio.astype(np.float32), "sampling_rate": 16000})
        return result["text"].strip()


if __name__ == "__main__":
    # quick test without the web interface
    hf = HuggingFaceTasks()
    print(hf.sentiment("I hate software courses"))
    print(hf.translate("Bonjour, comment allez-vous ?"))
