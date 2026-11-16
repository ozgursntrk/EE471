"""Decision Maker: answers structured questions about a text with probabilities (EmbeddingGemma 270M).

    python decision_maker.py ["customer message"]
"""
import sys

from common import BaseOptions, model, title
import mediapipe as mp

D = mp.tasks.decision
MESSAGES = [sys.argv[1]] if len(sys.argv) > 1 else [
    "I was charged twice for my subscription this month, please refund me!",
    "The app crashes every time I try to log in.",
    "How do I change the colour theme to dark mode?",
]

topic = D.ChoiceQuestion(criteria={
    "billing": "Refunds, invoices, payments or subscription charges.",
    "technical": "Crashes, login errors or features that do not work.",
    "how-to": "Questions about how to use a feature.",
})
urgent = D.BooleanQuestion(condition="The customer is upset and needs help urgently.")

options = D.DecisionMakerOptions(
    base_options=BaseOptions(model_asset_path=model("embeddinggemma-2-text-270m.litertlm")),
)
title("Decision Maker")
with D.DecisionMaker.create_from_options(options) as maker:
    for message in MESSAGES:
        choice = maker.evaluate_choice(message, topic)
        flag = maker.evaluate_boolean(message, urgent)
        probabilities = ", ".join(f"{k} {p:.2f}" for k, p in choice.probabilities.items())
        print(f"\n{message}")
        print(f"  topic : {choice.selected_key}  ({probabilities})")
        print(f"  urgent: {flag.value}  (p = {flag.probability_true:.2f})")
