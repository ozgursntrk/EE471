"""Image Segmenter: labels every pixel with a class (person, cat, car, ... DeepLab v3, 21 classes).

    python image_segmenter.py [image]    (default: samples/pose-3.jpg)
"""
import cv2
import numpy as np

from common import BaseOptions, input_path, load_image, model, save, title, vision

LABELS = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat",
          "chair", "cow", "dining table", "dog", "horse", "motorbike", "person", "potted plant",
          "sheep", "sofa", "train", "tv"]

path = input_path("pose-3.jpg")
image, canvas = load_image(path)

options = vision.ImageSegmenterOptions(
    base_options=BaseOptions(model_asset_path=model("deeplab_v3.tflite")),
    output_category_mask=True,
)
with vision.ImageSegmenter.create_from_options(options) as segmenter:
    result = segmenter.segment(image)

mask = np.squeeze(result.category_mask.numpy_view())   # one class number per pixel
title(f"Image Segmenter - {path}")
for value, count in zip(*np.unique(mask, return_counts=True)):
    print(f"  {LABELS[value]:<12} {100 * count / mask.size:5.1f} % of the pixels")

colors = np.random.default_rng(0).integers(0, 255, (len(LABELS), 3), dtype=np.uint8)
colors[0] = 0
overlay = cv2.addWeighted(canvas, 0.5, colors[mask], 0.5, 0)
save(overlay, "image_segmenter.jpg")
