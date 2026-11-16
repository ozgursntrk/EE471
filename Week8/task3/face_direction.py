"""Where is the face looking? Uses MediaPipe Face Landmarker.

    python face_direction.py images/face-1.png           -> left | right | straight
    python face_direction.py images/face-1.png --debug   -> also saves the image with the landmarks

"left" and "right" are from the person's own point of view (like in Task 2).
"""
import argparse
import os
import sys

import mediapipe as mp

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task")

# Face landmark numbers (478 points in total)
NOSE_TIP = 1
RIGHT_FACE_EDGE = 234   # person's right cheek (left side of the image when facing the camera)
LEFT_FACE_EDGE = 454    # person's left cheek

THRESHOLD = 0.12        # how far the nose may move from the middle and still count as "straight"


def detect_face(image_path):
    """Return the 478 landmarks of the first face, or None if no face is found."""
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_faces=1,
    )
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp.Image.create_from_file(image_path))
    return result.face_landmarks[0] if result.face_landmarks else None


def nose_position(landmarks):
    """0 = nose at the person's right cheek, 0.5 = in the middle, 1 = at the left cheek."""
    right = landmarks[RIGHT_FACE_EDGE].x
    left = landmarks[LEFT_FACE_EDGE].x
    nose = landmarks[NOSE_TIP].x
    return (nose - right) / (left - right)


def classify(landmarks):
    if landmarks is None:
        return "None"
    position = nose_position(landmarks)
    if position > 0.5 + THRESHOLD:
        return "left"      # nose moved towards the left cheek -> head turned to the person's left
    if position < 0.5 - THRESHOLD:
        return "right"
    return "straight"


def save_debug(image_path, landmarks):
    """Draw the nose (red) and the two face edges (blue) and save as <name>-debug.png."""
    import cv2  # only needed for --debug

    image = cv2.imread(image_path)
    h, w = image.shape[:2]
    points = {NOSE_TIP: ("nose", (0, 0, 255)),
              RIGHT_FACE_EDGE: ("R edge", (255, 0, 0)),
              LEFT_FACE_EDGE: ("L edge", (255, 0, 0))}
    for index, (label, color) in points.items():
        p = landmarks[index]
        x, y = int(p.x * w), int(p.y * h)
        cv2.circle(image, (x, y), 5, color, -1)
        cv2.putText(image, label, (x + 6, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
    text = f"nose position = {nose_position(landmarks):.2f}"
    cv2.putText(image, text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    out = os.path.splitext(image_path)[0] + "-debug.png"
    cv2.imwrite(out, image)
    print(f"saved {out} ({text})", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify where the face is looking.")
    parser.add_argument("image", help="path to the input image")
    parser.add_argument("--debug", action="store_true", help="save an image with the landmarks")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        sys.exit(f"Image not found: {args.image}")
    face = detect_face(args.image)
    if args.debug and face is not None:
        save_debug(args.image, face)
    print(classify(face))