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
## Task 1 – 22 MediaPipe solutions

Every solution has its own small script in `task1/`. Each one loads the model, runs it on a sample
input, prints the result and (for vision) saves an annotated image to `task1/outputs/`.
`common.py` holds the shared helpers (model paths, drawing, WAV files).

```powershell
cd Week8\task1
python download.py          # small models (~90 MB): vision, audio classifier, text
python download.py genai    # generative models (~1.9 GB)
python face_detector.py     # any demo; most accept your own input: python object_detector.py my.jpg
```

| Group | Script | Model | Demo input → result |
|---|---|---|---|
| Audio | `text_to_speech.py` | Phonon 31M | sentence → `outputs/speech.wav` |
| Audio | `audio_transcriber.py` | Parakeet TDT 0.6B | `speech.wav` → the same sentence as text |
| Audio | `audio_classifier.py` | YAMNet | `speech.wav` → "Speech" every second |
| Text | `language_detector.py` | Language detector | 5 sentences → tr, en, fr, de, ja |
| Text | `text_classifier.py` | BERT (movie reviews) | sentences → positive / negative |
| Text | `text_embedder.py` | Universal Sentence Encoder | similar sentences → high cosine similarity |
| Text | `text_proofreader.py` | Proofread 200M | "I goes to the libary" → "I went to the library" |
| Text | `text_summarizer.py` | Summarization 200M | paragraph → TL;DR and key points |
| Retrieval | `universal_embedder.py` | EmbeddingGemma 440M | texts and images in one vector space |
| Retrieval | `semantic_retriever.py` | EmbeddingGemma 440M | search by meaning in texts and an image |
| Decision | `decision_maker.py` | EmbeddingGemma 270M | support message → topic + urgent? |
| Vision | `face_detector.py` | BlazeFace | face box + 6 key points |
| Vision | `face_landmarker.py` | Face landmarker | 478 points, blendshapes, head pose matrix |
| Vision | `gesture_recognizer.py` | Gesture recognizer | hand → Thumb_Up |
| Vision | `hand_landmarker.py` | Hand landmarker | 21 points per hand, left/right |
| Vision | `holistic_landmarker.py` | Holistic landmarker | face + body + both hands |
| Vision | `image_classifier.py` | EfficientNet-Lite0 | burger → cheeseburger 0.98 |
| Vision | `image_embedder.py` | MobileNet-V3 | burger vs crop vs pets similarity |
| Vision | `image_segmenter.py` | DeepLab v3 | class of every pixel (person / background) |
| Vision | `interactive_segmenter.py` | MagicTouch | click a point → that object's mask |
| Vision | `object_detector.py` | EfficientDet-Lite0 | dog 0.89, cat 0.82 with boxes |
| Vision | `pose_landmarker.py` | Pose landmarker (full) | 33 body points |

Note: with mediapipe 1.2.3, the point-based interactive segmenter from the documentation is
`InteractiveSegmenterLegacy` (the new `InteractiveSegmenter` works with brush strokes).

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