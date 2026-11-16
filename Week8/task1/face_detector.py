"""Face Detector: finds faces (box + 6 key points: eyes, nose, mouth, ears).

    python face_detector.py [image]      (default: samples/face-3.png)
"""
from common import BaseOptions, draw_box, input_path, load_image, model, save, title, vision
import cv2

path = input_path("face-3.png")
image, canvas = load_image(path)

options = vision.FaceDetectorOptions(
    base_options=BaseOptions(model_asset_path=model("blaze_face_short_range.tflite")),
    min_detection_confidence=0.5,
)
with vision.FaceDetector.create_from_options(options) as detector:
    result = detector.detect(image)

title(f"Face Detector - {path}")
print(f"Faces found: {len(result.detections)}")
h, w = canvas.shape[:2]
for i, detection in enumerate(result.detections, 1):
    box, score = detection.bounding_box, detection.categories[0].score
    print(f"  face {i}: score {score:.2f}, box x={box.origin_x} y={box.origin_y} "
          f"w={box.width} h={box.height}")
    draw_box(canvas, box, f"face {score:.2f}")
    for kp in detection.keypoints:  # right eye, left eye, nose, mouth, right ear, left ear
        cv2.circle(canvas, (int(kp.x * w), int(kp.y * h)), 4, (0, 0, 255), -1)
save(canvas, "face_detector.jpg")
