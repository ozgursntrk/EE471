# Week 5 – Azure Speech Services

Both apps use **Azure AI Speech**. Create a `.env` file in the repository root
(see `.env.example`) with your own key:
```
SPEECH_KEY=your_azure_speech_key
SPEECH_REGION=westeurope
```
`.env` is in `.gitignore`, so the key is never pushed.

## Task 1 – Speech Studio website (`Week-5-Task-1`)
One Flask website with five tabs:
- **Text to Speech** – text → WAV audio (play / download), 3 voices incl. Turkish
- **Speech to Text** – record or upload audio → text
- **Diarization** – who spoke when (Guest-1, Guest-2, ...) with Azure's real-time conversation transcriber
- **Translation** – speak in one language, get the text in another
- **Pronunciation** – read a sentence, get accuracy / fluency / completeness scores per word

```
cd Week5/Week-5-Task-1
pip install -r requirements.txt
python app.py
```
`python make_test_dialog.py` creates `dialog.wav` (two voices) to test diarization.

**Git workflow:** `text-to-speech` and `speech-to-text` were branched from the same commit,
so merging the second one caused add/add conflicts in `app.py`, `index.html`, `style.css`
and `script.js`. The conflicts were resolved by combining both features into one tabbed page
(element IDs prefixed with `tts-` / `stt-`). Part 4 was developed on `part-4-extensions`.

## Task 2 – Voice-activated calculator (`Week-5-Task-2`)
- **Button → voice:** every key is spoken; `=` speaks the result ("is eight")
- **Microphone → buttons:** click the mic, say e.g. "five plus two is", click again

| 0–9 | . | ÷ | × | + | − | = |
|---|---|---|---|---|---|---|
| zero … nine | point | over | times | plus | minus | is |

```
cd Week5/Week-5-Task-2
pip install -r requirements.txt
python app.py
```
