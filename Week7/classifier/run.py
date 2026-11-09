"""Cog runner: serves one trained model over HTTP.

Which model is chosen with two environment variables (set in docker-compose):
    DATASET = fashion | cifar
    VARIANT = baseline | optimized
"""
import logging
import os
import time

import torch
from cog import BaseRunner, Input, Path
from PIL import Image

from data import DATASETS, preprocess
from models import build_model

LOG_FILE = "/tmp/predictions.log"


def make_logger(tag):
    """Write every prediction to the terminal (docker logs) and to a log file."""
    logger = logging.getLogger("classifier")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(f"%(asctime)s | {tag} | %(message)s", "%Y-%m-%d %H:%M:%S")
    for handler in (logging.StreamHandler(), logging.FileHandler(LOG_FILE)):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


class Runner(BaseRunner):
    def setup(self):
        """Runs once when the container starts: load the trained weights."""
        self.dataset = os.environ.get("DATASET", "fashion")
        self.variant = os.environ.get("VARIANT", "baseline")
        self.classes = DATASETS[self.dataset]["classes"]
        self.log = make_logger(f"{self.dataset}-{self.variant}")

        checkpoint = torch.load(f"weights/{self.dataset}-{self.variant}.pt", map_location="cpu")
        self.test_accuracy = checkpoint["test_accuracy"]
        self.model = build_model(self.dataset, checkpoint["config"])
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.eval()
        self.log.info(f"Model loaded (test accuracy {self.test_accuracy:.2%})")

    def run(self, image: Path = Input(description="Image to classify")) -> dict:
        """Runs for every request."""
        start = time.time()
        batch = preprocess(self.dataset, Image.open(image))
        with torch.no_grad():
            probs = self.model(batch)[0].softmax(0)   # logits -> probabilities

        top = probs.topk(3)
        top3 = [{"label": self.classes[i], "probability": round(p.item(), 4)}
                for p, i in zip(top.values, top.indices)]
        result = {
            "dataset": self.dataset,
            "model": self.variant,
            "prediction": top3[0]["label"],
            "confidence": top3[0]["probability"],
            "top3": top3,
            "test_accuracy": self.test_accuracy,
        }
        self.log.info(f"prediction={result['prediction']} confidence={result['confidence']:.1%} "
                      f"time={time.time() - start:.3f}s")
        return result