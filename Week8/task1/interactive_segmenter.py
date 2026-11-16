"""Interactive Segmenter: you point at an object, it cuts that object out.

    python interactive_segmenter.py [image] [x] [y]
    default: samples/cat_and_dog.jpg, point x=0.3 y=0.5 (0..1 of the width/height)
"""
import sys

import cv2
import numpy as np
import mediapipe as mp

from common import BaseOptions, input_path, load_image, model, save, title, vision

path = input_path("cat_and_dog.jpg")
x = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
y = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
image, canvas = load_image(path)

RegionOfInterest = vision.InteractiveSegmenterLegacyRegionOfInterest
NormalizedKeypoint = mp.tasks.components.containers.keypoint.NormalizedKeypoint

options = vision.InteractiveSegmenterLegacyOptions(
    base_options=BaseOptions(model_asset_path=model("magic_touch.tflite")),
    output_category_mask=True,
)
roi = RegionOfInterest(format=RegionOfInterest.Format.KEYPOINT, keypoint=NormalizedKeypoint(x, y))
with vision.InteractiveSegmenterLegacy.create_from_options(options) as segmenter:
    result = segmenter.segment(image, roi)

mask = np.squeeze(result.category_mask.numpy_view()) > 0
h, w = canvas.shape[:2]
px, py = min(int(x * w), w - 1), min(int(y * h), h - 1)
if not mask[py, px]:      # the selected object must contain the clicked point
    mask = ~mask
title(f"Interactive Segmenter - {path}, point ({x}, {y})")
print(f"Selected object covers {100 * mask.mean():.1f} % of the image")

highlight = canvas.copy()
highlight[mask] = (0.4 * highlight[mask] + 0.6 * np.array([0, 255, 0])).astype(np.uint8)
cv2.circle(highlight, (int(x * w), int(y * h)), 8, (0, 0, 255), -1)
save(highlight, "interactive_segmenter.jpg")
