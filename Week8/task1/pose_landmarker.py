"""Pose Landmarker: 33 body points (nose, shoulders, elbows, wrists, hips, knees, ankles ...).

    python pose_landmarker.py [image]    (default: samples/pose-2.jpg)
"""
from common import BaseOptions, draw_landmarks, input_path, load_image, model, save, title, vision

NAMES = {0: "nose", 11: "left shoulder", 12: "right shoulder", 15: "left wrist",
         16: "right wrist", 27: "left ankle", 28: "right ankle"}

path = input_path("pose-2.jpg")
image, canvas = load_image(path)

options = vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model("pose_landmarker_full.task")),
    num_poses=1,
)
with vision.PoseLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

title(f"Pose Landmarker - {path}")
if not result.pose_landmarks:
    raise SystemExit("No person found")
landmarks = result.pose_landmarks[0]
print(f"Landmarks: {len(landmarks)}")
for i, name in NAMES.items():
    p = landmarks[i]
    print(f"  {name:<15} x={p.x:.2f} y={p.y:.2f} visibility={p.visibility:.2f}")
draw_landmarks(canvas, landmarks, (0, 0, 255), vision.PoseLandmarksConnections.POSE_LANDMARKS)
save(canvas, "pose_landmarker.jpg")
