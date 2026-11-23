"""Gradio web interface for the ten Hugging Face tasks.

    python app.py        -> open http://127.0.0.1:7860 in the browser
"""
import os

import gradio as gr

from hf_tasks import HuggingFaceTasks

hf = HuggingFaceTasks()
SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "task1", "samples")

NER_TEXT = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living "
            "and working in the beautiful city İzmir in Türkiye.")
CRISIS_TEXT = (
    "The 2008 Global Financial Crisis stands as the most severe economic collapse of the 21st century, "
    "often compared to the Great Depression of the 1930s. Triggered by the bursting of the United States "
    "housing bubble, its effects rippled across the globe, leading to the collapse of major financial "
    "institutions and a deep international recession. The crisis began with the subprime mortgage market. "
    "In the early 2000s, low interest rates and a push for homeownership led banks to issue high-risk "
    "loans to borrowers with poor credit."
)


# ---------- small functions that connect the class to the interface ----------
def run_zero_shot(text, labels):
    return hf.zero_shot(text, [label.strip() for label in labels.split(",") if label.strip()])


def run_generation(prompt):
    first, second = hf.generate(prompt)
    return first, second


def run_ner(text):
    entities = hf.ner(text)
    highlighted = {"text": text,
                   "entities": [{"entity": e["type"], "start": e["start"], "end": e["end"]} for e in entities]}
    table = [[e["type"], e["word"], round(e["score"], 3)] for e in entities]
    return highlighted, table


def run_qa(question, context):
    answer, score = hf.answer(question, context)
    return answer, round(score, 3)


# ---------- the interface: one tab per task ----------
with gr.Blocks(title="EE 471 - Hugging Face Tasks") as demo:
    gr.Markdown("# EE 471 Week 9 – Hugging Face Transformers demo\nOne tab per task. "
                "A model is downloaded/loaded the first time its tab is used.")

    with gr.Tab("Sentiment"):
        text = gr.Textbox(label="Text", value="I've been waiting for a modern software practices course my whole life.")
        button = gr.Button("Analyze", variant="primary")
        output = gr.Label(label="Sentiment")
        button.click(hf.sentiment, text, output)
        gr.Examples(["I hate software courses"], text)

    with gr.Tab("Zero-shot"):
        text = gr.Textbox(label="Text", value="Berkshire keeps their cash reserves at an extremely high level.")
        labels = gr.Textbox(label="Labels (comma separated)", value="finance, sports, politics, technology")
        button = gr.Button("Classify", variant="primary")
        output = gr.Label(label="Scores")
        button.click(run_zero_shot, [text, labels], output)

    with gr.Tab("Text generation"):
        text = gr.Textbox(label="Start of the sentence",
                          value="If I continue to complete all in-class exercises in this modern software practices course,")
        button = gr.Button("Complete (2 alternatives, max 35 words)", variant="primary")
        first, second = gr.Textbox(label="Alternative 1"), gr.Textbox(label="Alternative 2")
        button.click(run_generation, text, [first, second])

    with gr.Tab("Fill mask"):
        text = gr.Textbox(label="Sentence with [MASK]", value="To understand generative AI, one must study [MASK] well.")
        button = gr.Button("Fill", variant="primary")
        output = gr.Label(label="Best words")
        button.click(hf.fill_mask, text, output)

    with gr.Tab("NER"):
        text = gr.Textbox(label="Text", value=NER_TEXT)
        button = gr.Button("Find entities", variant="primary")
        highlighted = gr.HighlightedText(label="Entities")
        table = gr.Dataframe(headers=["type", "word", "score"], label="Details")
        button.click(run_ner, text, [highlighted, table])

    with gr.Tab("Question answering"):
        context = gr.Textbox(label="Context", value=NER_TEXT, lines=3)
        question = gr.Textbox(label="Question", value="What is the person's name?")
        button = gr.Button("Answer", variant="primary")
        answer, score = gr.Textbox(label="Answer"), gr.Number(label="Score")
        button.click(run_qa, [question, context], [answer, score])
        gr.Examples(["What is the person's name?", "Which organization does the person work for?",
                     "In which city does the person live?"], question)

    with gr.Tab("Summarization"):
        text = gr.Textbox(label="Long text", value=CRISIS_TEXT, lines=6)
        button = gr.Button("Summarize", variant="primary")
        output = gr.Textbox(label="Summary")
        button.click(hf.summarize, text, output)

    with gr.Tab("Translation"):
        text = gr.Textbox(label="French text", value="Ce cours est produit par Hugging Face.")
        button = gr.Button("Translate to English", variant="primary")
        output = gr.Textbox(label="English")
        button.click(hf.translate, text, output)

    with gr.Tab("Image classification"):
        image = gr.Image(type="pil", label="Image")
        button = gr.Button("Classify", variant="primary")
        output = gr.Label(label="Top 3 classes")
        button.click(hf.classify_image, image, output)
        gr.Examples([os.path.join(SAMPLES, "burger.jpg"), os.path.join(SAMPLES, "cat_and_dog.jpg")], image)

    with gr.Tab("Speech recognition"):
        audio = gr.Audio(sources=["microphone", "upload"], type="numpy", label="Record or upload speech")
        button = gr.Button("Transcribe", variant="primary")
        output = gr.Textbox(label="Text")
        button.click(hf.transcribe, audio, output)

if __name__ == "__main__":
    demo.launch()
