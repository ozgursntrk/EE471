"""Image classification with Google's ViT (vit-base-patch16-224, 1000 ImageNet classes).

    python image_classification.py [image]     (default: samples/burger.jpg)
"""
import sys

from transformers import pipeline

from common import DEVICE, sample, title

path = sample(sys.argv[1] if len(sys.argv) > 1 else "burger.jpg")
classifier = pipeline("image-classification", model="google/vit-base-patch16-224", device=DEVICE)

title(f"Image classification - {path}")
for r in classifier(path, top_k=3):
    print(f"  {r['label']:<35} {r['score']:.3f}")
