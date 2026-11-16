"""Text Summarizer: summarizes a long text, as a TL;DR or as key points (200M model).

    python text_summarizer.py [file.txt]
"""
import sys

from common import BaseOptions, model, title
import mediapipe as mp

TEXT = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else (
    "MediaPipe is an open-source framework from Google for building machine learning pipelines "
    "that run directly on phones, computers and in the browser. It offers ready-made solutions "
    "for vision, text and audio, such as face and hand landmark detection, object detection, "
    "image segmentation, text classification and audio classification. Recently, Google added "
    "generative tasks like text summarization, proofreading, speech recognition and text-to-speech. "
    "Because the models run on the device, no data has to be sent to a server, which protects "
    "privacy, works offline and reduces latency. Developers can use the same task API in Python, "
    "Android, iOS and the web, and they can customize many models with their own data."
)
Mode = mp.tasks.text.TextSummarizerMode

title("Text Summarizer")
print(f"Input: {len(TEXT.split())} words")
for mode in (Mode.TLDR, Mode.KEYPOINTS):
    options = mp.tasks.text.TextSummarizerOptions(
        base_options=BaseOptions(model_asset_path=model("summarization_quant_200m_2modes.litertlm")),
        mode=mode,
    )
    with mp.tasks.text.TextSummarizer.create_from_options(options) as summarizer:
        print(f"\n[{mode.name}]\n{summarizer.summarize(TEXT).summary}")
