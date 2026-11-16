"""Image Classifier: what is in the image? (1000 ImageNet classes, EfficientNet-Lite0)

    python image_classifier.py [image]   (default: samples/burger.jpg)
"""
import cv2

from common import BaseOptions, input_path, load_image, model, save, title, vision

path = input_path("burger.jpg")
image, canvas = load_image(path)

options = vision.ImageClassifierOptions(
    base_options=BaseOptions(model_asset_path=model("efficientnet_lite0.tflite")),
    max_results=3,
)
with vision.ImageClassifier.create_from_options(options) as classifier:
    result = classifier.classify(image)

title(f"Image Classifier - {path}")
for i, c in enumerate(result.classifications[0].categories):
    print(f"  {i + 1}. {c.category_name:<20} {c.score:.2f}")
    cv2.putText(canvas, f"{c.category_name} {c.score:.2f}", (10, 25 + 25 * i),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
save(canvas, "image_classifier.jpg")
