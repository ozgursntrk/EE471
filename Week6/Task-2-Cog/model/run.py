import os
os.environ["TORCH_HOME"] = "."  # model weights are stored in ./hub (baked into the image)

import logging
import time

import torch
from cog import BaseRunner, Input, Path
from PIL import Image
from torchvision import models

WEIGHTS = models.ResNet50_Weights.IMAGENET1K_V1

# ImageNet class index -> cat kind (the 5 domestic cat classes of ImageNet)
CAT_CLASSES = {
    281: "Tabby",
    282: "Tiger cat",
    283: "Persian",
    284: "Siamese",
    285: "Egyptian Mau",
}

LOG_FILE = "/tmp/predictions.log"


def make_logger():
    """Write every prediction both to the terminal (docker logs) and to a log file."""
    logger = logging.getLogger("cat-classifier")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    for handler in (logging.StreamHandler(), logging.FileHandler(LOG_FILE)):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


class Runner(BaseRunner):
    def setup(self):
        """Runs once when the container starts: load the model into memory."""
        self.log = make_logger()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet50(weights=WEIGHTS).to(self.device)
        self.model.eval()
        self.transform = WEIGHTS.transforms()
        self.categories = WEIGHTS.meta["categories"]
        self.log.info(f"Model loaded on {self.device}")

    def run(self, image: Path = Input(description="Photo of a cat")) -> dict:
        """Runs for every request: classify the cat kind in the image."""
        start = time.time()
        img = Image.open(image).convert("RGB")
        batch = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            probs = self.model(batch)[0].softmax(0)

        # probability of each cat kind (out of all 1000 ImageNet classes)
        cat_probs = {name: probs[i].item() for i, name in CAT_CLASSES.items()}
        cat_total = sum(cat_probs.values())

        # re-scale so the 5 cat kinds add up to 100 %
        breeds = {name: p / cat_total for name, p in cat_probs.items()}
        breeds = dict(sorted(breeds.items(), key=lambda kv: kv[1], reverse=True))
        best = next(iter(breeds))

        top_index = probs.argmax().item()
        result = {
            "is_cat": cat_total >= 0.3,
            "cat_probability": round(cat_total, 4),
            "prediction": best,
            "confidence": round(breeds[best], 4),
            "all_kinds": {k: round(v, 4) for k, v in breeds.items()},
            "top_imagenet_label": self.categories[top_index],
        }

        self.log.info(
            f"prediction={best} confidence={breeds[best]:.1%} "
            f"is_cat={result['is_cat']} top_label={result['top_imagenet_label']} "
            f"time={time.time() - start:.2f}s"
        )
        return result