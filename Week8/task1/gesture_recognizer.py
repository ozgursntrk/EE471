"""Gesture Recognizer: recognises hand gestures (thumbs up, victory, open palm, ...).

    python gesture_recognizer.py [image]  (default: samples/thumbs_up.jpg)
"""
import cv2

from common import BaseOptions, draw_landmarks, input_path, load_image, model, save, title, vision

path = input_path("thumbs_up.jpg")
image, canvas = load_image(path)

options = vision.GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path=model("gesture_recognizer.task")),
    num_hands=2,
)
with vision.GestureRecognizer.create_from_options(options) as recognizer:
    result = recognizer.recognize(image)

title(f"Gesture Recognizer - {path}")
print(f"Hands found: {len(result.gestures)}")
for gestures, handedness, landmarks in zip(result.gestures, result.handedness, result.hand_landmarks):
    gesture, hand = gestures[0], handedness[0]
    print(f"  {hand.category_name} hand: {gesture.category_name} ({gesture.score:.2f})")
    draw_landmarks(canvas, landmarks, (0, 200, 255), vision.HandLandmarksConnections.HAND_CONNECTIONS)
    cv2.putText(canvas, gesture.category_name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
save(canvas, "gesture_recognizer.jpg")
