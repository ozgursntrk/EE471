"""Holistic Landmarker: face, body and both hands in one model (543 points).

    python holistic_landmarker.py [image]  (default: samples/pose-3.jpg)
"""
from common import BaseOptions, draw_landmarks, input_path, load_image, model, save, title, vision

path = input_path("pose-3.jpg")
image, canvas = load_image(path)

options = vision.HolisticLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model("holistic_landmarker.task")),
)
with vision.HolisticLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

title(f"Holistic Landmarker - {path}")
parts = {
    "face": (result.face_landmarks, (0, 255, 0)),
    "pose": (result.pose_landmarks, (0, 0, 255)),
    "left hand": (result.left_hand_landmarks, (255, 0, 0)),
    "right hand": (result.right_hand_landmarks, (255, 0, 255)),
}
for name, (landmarks, color) in parts.items():
    landmarks = landmarks or []
    print(f"  {name:<11} {len(landmarks)} landmarks")
    if landmarks:
        draw_landmarks(canvas, landmarks, color, radius=2)
save(canvas, "holistic_landmarker.jpg")
