"""Object Detector: finds objects with boxes (80 COCO classes, EfficientDet-Lite0).

    python object_detector.py [image]    (default: samples/cat_and_dog.jpg)
"""
from common import BaseOptions, draw_box, input_path, load_image, model, save, title, vision

path = input_path("cat_and_dog.jpg")
image, canvas = load_image(path)

options = vision.ObjectDetectorOptions(
    base_options=BaseOptions(model_asset_path=model("efficientdet_lite0.tflite")),
    score_threshold=0.4,
    max_results=5,
)
with vision.ObjectDetector.create_from_options(options) as detector:
    result = detector.detect(image)

title(f"Object Detector - {path}")
for d in result.detections:
    c = d.categories[0]
    print(f"  {c.category_name:<10} {c.score:.2f}  box x={d.bounding_box.origin_x} "
          f"y={d.bounding_box.origin_y} w={d.bounding_box.width} h={d.bounding_box.height}")
    draw_box(canvas, d.bounding_box, f"{c.category_name} {c.score:.2f}")
save(canvas, "object_detector.jpg")
