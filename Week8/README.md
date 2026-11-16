# EE 471 – Week 8: MediaPipe

| Task | Folder | What it does |
|---|---|---|
| 1 | [task1](task1) | Demos of 22 MediaPipe solutions (audio, text, decision, retrieval, vision) |
| 2 | [task2](task2) | Which arm is up? (Pose Landmarker) → `left`, `right`, `both` or `None` |
| 3 | [task3](task3) | Where is the face looking? (Face Landmarker) → `left`, `right` or `straight` |

**Left / right** always mean the **person's own** left and right (MediaPipe's convention),
not the left or right side of the image.

## Requirements

- Python 3.12+ and `pip install mediapipe opencv-python numpy`
- Docker Desktop (for Task 2 and 3)

## Task 2 – Which arm is up?

The Pose Landmarker finds 33 body landmarks. An arm counts as **up** when its wrist is above its
shoulder by more than 10 % of the torso length (shoulder–hip distance). Points with a visibility
below 0.5 are ignored.

```powershell
cd Week8\task2

# Python
python arm_up.py images/pose-1.jpg            # add --debug to save an image with the landmarks

# Docker
docker build -t arm-up .
docker run --rm -v "${PWD}/images:/images" arm-up /images/pose-1.jpg
```

| Image | Result |
|---|---|
| pose-1.jpg | left |
| pose-2.jpg | right |
| pose-3.jpg | both |

## Task 3 – Where is the face looking?

The Face Landmarker finds 478 face landmarks. The script measures where the **nose tip** lies
between the two face edges (cheeks 234 and 454): 0.5 means the middle. If the nose moves more
than 0.12 towards one side, the head is turned to that side.

```powershell
cd Week8\task3

# Python
python face_direction.py images/face-1.png    # add --debug to save an image with the landmarks

# Docker
docker build -t face-direction .
docker run --rm -v "${PWD}/images:/images" face-direction /images/face-1.png
```

| Image | Result |
|---|---|
| face-1.png | right |
| face-2.png | left |
| face-3.png | straight |

## Notes

- MediaPipe prints many `INFO` / `WARNING` lines from its inference engine. They are harmless;
  the answer is the last line. Add `2>$null` (PowerShell) or `2>/dev/null` (bash) to hide them.
- The Docker images install `libgl1`, `libglib2.0-0`, `libegl1` and `libgles2`, which MediaPipe's
  Linux library needs even without a GPU.