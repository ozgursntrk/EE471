"""Text Proofreader: fixes spelling and grammar mistakes (200M on-device language model).

    python text_proofreader.py ["your text"]
"""
import sys

from common import BaseOptions, model, title
import mediapipe as mp

TEXT = (sys.argv[1] if len(sys.argv) > 1 else
        "Yesterday I goes to the libary and borrowed three book about machin learning.")

options = mp.tasks.text.TextProofreaderOptions(
    base_options=BaseOptions(model_asset_path=model("proofread_quant_200m.litertlm")),
)
with mp.tasks.text.TextProofreader.create_from_options(options) as proofreader:
    result = proofreader.proofread(TEXT)

title("Text Proofreader")
print(f"Original : {TEXT}")
print(f"Corrected: {result.proofread_text}")
print("Changes:")
for c in result.corrections:
    if c.type.name != "SAME":
        print(f"  {c.type.name:<9} '{c.text}'")
