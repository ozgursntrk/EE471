"""Face Landmarker: 478 face points, 52 blendshapes (expressions) and the head pose matrix.

    python face_landmarker.py [image]    (default: samples/face-3.png)
"""
from common import BaseOptions, draw_landmarks, input_path, load_image, model, save, title, vision

path = input_path("face-3.png")
image, canvas = load_image(path)

options = vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model("face_landmarker.task")),
    num_faces=1,
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
)
with vision.FaceLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

title(f"Face Landmarker - {path}")
if not result.face_landmarks:
    raise SystemExit("No face found")
landmarks = result.face_landmarks[0]
print(f"Landmarks: {len(landmarks)} points (x, y, z)")
print(f"Nose tip (landmark 1): x={landmarks[1].x:.3f} y={landmarks[1].y:.3f} z={landmarks[1].z:.3f}")

print("Top 5 blendshapes (facial expressions):")
for b in sorted(result.face_blendshapes[0], key=lambda b: b.score, reverse=True)[:5]:
    print(f"  {b.category_name:<20} {b.score:.2f}")

print("Facial transformation matrix (head rotation + position):")
print(result.facial_transformation_matrixes[0].round(2))

draw_landmarks(canvas, landmarks, (0, 255, 0), vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS, 1)
save(canvas, "face_landmarker.jpg")
