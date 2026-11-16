"""Hand Landmarker: 21 points per hand and left/right handedness.

    python hand_landmarker.py [image]    (default: samples/woman_hands.jpg)
"""
from common import BaseOptions, draw_landmarks, input_path, load_image, model, save, title, vision

path = input_path("woman_hands.jpg")
image, canvas = load_image(path)

options = vision.HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model("hand_landmarker.task")),
    num_hands=2,
)
with vision.HandLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

title(f"Hand Landmarker - {path}")
print(f"Hands found: {len(result.hand_landmarks)}")
for handedness, landmarks in zip(result.handedness, result.hand_landmarks):
    hand = handedness[0]
    tip = landmarks[8]  # index finger tip
    print(f"  {hand.category_name} hand ({hand.score:.2f}): {len(landmarks)} landmarks, "
          f"index finger tip at x={tip.x:.2f} y={tip.y:.2f}")
    draw_landmarks(canvas, landmarks, (255, 128, 0), vision.HandLandmarksConnections.HAND_CONNECTIONS)
save(canvas, "hand_landmarker.jpg")
