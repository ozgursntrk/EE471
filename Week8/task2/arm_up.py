"""Which arm is up? Uses MediaPipe Pose Landmarker.

    python arm_up.py images/pose-1.jpg           -> left | right | both | None
    python arm_up.py images/pose-1.jpg --debug   -> also saves the image with the landmarks

"left" and "right" are from the person's own point of view (MediaPipe's convention).
"""
import argparse
import os
import sys

import mediapipe as mp

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_landmarker_full.task")

# Pose landmark numbers (33 points in total)
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HIP, RIGHT_HIP = 23, 24

MIN_VISIBILITY = 0.5   # ignore points the model is not sure about
MARGIN = 0.10          # wrist must be this much (x torso length) above the shoulder


def detect_pose(image_path):
    """Return the 33 landmarks of the first person, or None if nobody is found."""
    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_poses=1,
    )
    with mp.tasks.vision.PoseLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp.Image.create_from_file(image_path))
    return result.pose_landmarks[0] if result.pose_landmarks else None


def is_arm_up(landmarks, shoulder, wrist, torso):
    """Image y grows downwards, so 'up' means a smaller y value."""
    s, w = landmarks[shoulder], landmarks[wrist]
    if w.visibility < MIN_VISIBILITY or s.visibility < MIN_VISIBILITY:
        return False
    return w.y < s.y - MARGIN * torso


def classify(landmarks):
    if landmarks is None:
        return "None"
    # torso length = distance between the middle of the shoulders and the middle of the hips
    shoulder_y = (landmarks[LEFT_SHOULDER].y + landmarks[RIGHT_SHOULDER].y) / 2
    hip_y = (landmarks[LEFT_HIP].y + landmarks[RIGHT_HIP].y) / 2
    torso = abs(hip_y - shoulder_y) or 0.3

    left = is_arm_up(landmarks, LEFT_SHOULDER, LEFT_WRIST, torso)
    right = is_arm_up(landmarks, RIGHT_SHOULDER, RIGHT_WRIST, torso)
    if left and right:
        return "both"
    if left:
        return "left"
    if right:
        return "right"
    return "None"


def save_debug(image_path, landmarks):
    """Draw shoulders (blue) and wrists (red) and save as <name>-debug.jpg."""
    import cv2  # only needed for --debug

    image = cv2.imread(image_path)
    h, w = image.shape[:2]
    points = {LEFT_SHOULDER: "L shoulder", RIGHT_SHOULDER: "R shoulder",
              LEFT_WRIST: "L wrist", RIGHT_WRIST: "R wrist"}
    for index, label in points.items():
        p = landmarks[index]
        x, y = int(p.x * w), int(p.y * h)
        color = (255, 0, 0) if "shoulder" in label else (0, 0, 255)
        cv2.circle(image, (x, y), 6, color, -1)
        cv2.putText(image, label, (x + 8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
    out = os.path.splitext(image_path)[0] + "-debug.jpg"
    cv2.imwrite(out, image)
    print(f"saved {out}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify which arm is up.")
    parser.add_argument("image", help="path to the input image")
    parser.add_argument("--debug", action="store_true", help="save an image with the landmarks")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        sys.exit(f"Image not found: {args.image}")
    pose = detect_pose(args.image)
    if args.debug and pose is not None:
        save_debug(args.image, pose)
    print(classify(pose))