"""Download the MediaPipe models and sample inputs used by the demos.

    python download.py          # the small models (~90 MB): vision, audio, text
    python download.py genai    # the big generative models (~1.9 GB)
"""
import os
import sys
import urllib.request

GCS = "https://storage.googleapis.com/mediapipe-models"
HF = "https://huggingface.co/litert-community"

MODELS = {
    "vision": {
        "blaze_face_short_range.tflite": f"{GCS}/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
        "face_landmarker.task": f"{GCS}/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        "gesture_recognizer.task": f"{GCS}/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
        "hand_landmarker.task": f"{GCS}/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        "holistic_landmarker.task": f"{GCS}/holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task",
        "efficientnet_lite0.tflite": f"{GCS}/image_classifier/efficientnet_lite0/float32/1/efficientnet_lite0.tflite",
        "mobilenet_v3_small.tflite": f"{GCS}/image_embedder/mobilenet_v3_small/float32/1/mobilenet_v3_small.tflite",
        "deeplab_v3.tflite": f"{GCS}/image_segmenter/deeplab_v3/float32/1/deeplab_v3.tflite",
        "magic_touch.tflite": f"{GCS}/interactive_segmenter/magic_touch/float32/1/magic_touch.tflite",
        "efficientdet_lite0.tflite": f"{GCS}/object_detector/efficientdet_lite0/int8/1/efficientdet_lite0.tflite",
        "pose_landmarker_full.task": f"{GCS}/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
    },
    "audio": {
        "yamnet.tflite": f"{GCS}/audio_classifier/yamnet/float32/1/yamnet.tflite",
    },
    "text": {
        "language_detector.tflite": f"{GCS}/language_detector/language_detector/float32/1/language_detector.tflite",
        "bert_classifier.tflite": f"{GCS}/text_classifier/bert_classifier/float32/1/bert_classifier.tflite",
        "universal_sentence_encoder.tflite":
            f"{GCS}/text_embedder/universal_sentence_encoder/float32/1/universal_sentence_encoder.tflite",
    },
    "genai": {
        "phonon_int8.litertlm": f"{HF}/phonon-31m-en/resolve/main/phonon_int8.litertlm",
        "parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm":
            f"{HF}/parakeet-tdt-0.6b-v3/resolve/main/parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm",
        "proofread_quant_200m.litertlm": f"{GCS}/text_proofreader/200m/latest/proofread_quant_200m.litertlm",
        "summarization_quant_200m_2modes.litertlm":
            f"{GCS}/text_summarizer/200m/latest/summarization_quant_200m_2modes.litertlm",
        "embeddinggemma-2-text-270m.litertlm":
            f"{HF}/embeddinggemma-2-text-270m-litert-lm/resolve/main/embeddinggemma-2-text-270m.litertlm",
        "embeddinggemma-2-text-vision-440m.litertlm":
            f"{HF}/embeddinggemma-2-text-vision-440m-litert-lm/resolve/main/embeddinggemma-2-text-vision-440m.litertlm",
    },
}

# Sample images from the official MediaPipe example notebooks
SAMPLES = {
    "burger.jpg": "https://storage.googleapis.com/mediapipe-tasks/image_classifier/burger.jpg",
    "burger_crop.jpg": "https://storage.googleapis.com/mediapipe-tasks/image_embedder/burger_crop.jpg",
    "cat_and_dog.jpg": "https://storage.googleapis.com/mediapipe-tasks/object_detector/cat_and_dog.jpg",
    "thumbs_up.jpg": "https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/thumbs_up.jpg",
    "woman_hands.jpg": "https://storage.googleapis.com/mediapipe-tasks/hand_landmarker/woman_hands.jpg",
    "segmentation_input.jpg": "https://storage.googleapis.com/mediapipe-assets/segmentation_input_rotation0.jpg",
}


def download(url, path):
    if os.path.exists(path):
        print(f"  ok (already there)  {os.path.basename(path)}")
        return
    print(f"  downloading         {os.path.basename(path)} ...", flush=True)
    try:
        urllib.request.urlretrieve(url, path + ".part")
        os.replace(path + ".part", path)
        print(f"  done                {os.path.getsize(path) / 1e6:.1f} MB")
    except Exception as error:  # keep going, report at the end
        print(f"  FAILED              {error}")


if __name__ == "__main__":
    groups = sys.argv[1:] or ["vision", "audio", "text"]
    os.makedirs("models", exist_ok=True)
    os.makedirs("samples", exist_ok=True)
    for group in groups:
        print(f"[{group}]")
        for name, url in MODELS[group].items():
            download(url, os.path.join("models", name))
    if "vision" in groups:
        print("[sample images]")
        for name, url in SAMPLES.items():
            download(url, os.path.join("samples", name))