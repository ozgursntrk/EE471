# EE 471 – Week 9: Hugging Face Transformers

| Task | Folder | What it does |
|---|---|---|
| 1 | [task1](task1) | Ten `pipeline` demos (sentiment, zero-shot, generation, fill-mask, NER, QA, summary, translation, ViT, Whisper) |
| 2 | – | Video of the chapter 1 quiz |
| 3 | [task3](task3) | `HuggingFaceTasks` class (OOP module) + Gradio web interface with one tab per task |
| 4 | [task4](task4) | Tokenizer and model basics: load & save, encode/decode, padding, truncation, special tokens |

## Setup

```powershell
pip install -r requirements.txt     # torch with CUDA should be installed first
python download_models.py           # downloads all models once (~7 GB, Whisper is ~3 GB)
```

`transformers` is kept below version 5, because version 5 removed the `translation`
and `summarization` pipelines that the course uses. `gradio<6` is needed for the same
reason (Gradio 6 needs a newer `huggingface_hub` than transformers 4 allows).

## Task 1

```powershell
cd task1
python sentiment_analysis.py
python zero_shot_classification.py
python text_generation.py
python fill_mask.py
python named_entity_recognition.py
python question_answering.py         # checks the NER results with questions
python summarization.py
python translation.py                # French -> English
python image_classification.py       # optional: path of your own image
python speech_recognition.py         # optional: path of your own .wav file
```

| Task | Model |
|---|---|
| Sentiment analysis | distilbert-base-uncased-finetuned-sst-2-english |
| Zero-shot classification | facebook/bart-large-mnli |
| Text generation | HuggingFaceTB/SmolLM2-360M |
| Fill mask | distilroberta-base |
| Named entity recognition | dslim/bert-base-NER |
| Question answering | distilbert-base-cased-distilled-squad |
| Summarization | sshleifer/distilbart-cnn-12-6 |
| Translation | Helsinki-NLP/opus-mt-fr-en |
| Image classification | google/vit-base-patch16-224 |
| Speech recognition | openai/whisper-large-v3 |

## Task 3

```powershell
cd task3
python app.py      # open http://127.0.0.1:7860
```

`hf_tasks.py` contains the `HuggingFaceTasks` class with one method per task. Models are
loaded the first time a task is used and then reused. `app.py` builds the Gradio interface
on top of this class.

## Task 4

```powershell
cd task4
python load_and_save.py      # saves the model to task4/saved_model and loads it back
python encode_decode.py
python padding.py
python truncation.py
python special_tokens.py
```
