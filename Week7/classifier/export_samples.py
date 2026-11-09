"""Save a few test images as PNG files, to try the websites and Postman.

    python export_samples.py            # both datasets
    python export_samples.py fashion    # only one
"""
import os
import sys

from torchvision import datasets

from data import DATA_DIR, DATASETS

PER_CLASS = 2

names = sys.argv[1:] or list(DATASETS)
for name in names:
    info = DATASETS[name]
    test_set = info["cls"](root=DATA_DIR, train=False, download=True)
    os.makedirs(f"samples/{name}", exist_ok=True)
    saved = {c: 0 for c in range(10)}
    for index, (img, label) in enumerate(test_set):
        if saved[label] < PER_CLASS:
            saved[label] += 1
            safe = info["classes"][label].replace("/", "-").replace(" ", "-")
            # upscale so the picture is visible in the browser (the model resizes it back)
            img.resize((img.width * 8, img.height * 8)).save(f"samples/{name}/{safe}-{index}.png")
        if all(v == PER_CLASS for v in saved.values()):
            break
    print(f"Saved {PER_CLASS * 10} images to samples/{name}/")