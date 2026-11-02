# Mini Project 2 – Vibe Coding Transcript

AI tool used: Claude (chat). The conversation was in Turkish; my prompts are shown as I wrote
them, with a short English note. Long code answers are summarized – the final code is in this folder.

## 1. Understanding the task
**Me:** "kanka bu hafta bir taskimiz daha var bu taskin en son yaptığımızla alakası var mı"
*(Is this task related to the Docker task we just did?)* + Mini-Project-2.pdf

**AI:** No – it combines the Week 4 Library App with the Week 5 Azure Speech code. It also
pointed out that the deadline is the next day.

**Me:** "evet geçelim mini project 2ye öncelikle ne yapacağımızı anlat" *(explain the plan first)*

**AI:** Explained the flow of one command: record → Azure speech-to-text → a parser turns the
sentence into a request (e.g. `POST /api/items/3/checkout`) → the real endpoint runs → a reply
sentence is built from the status code and JSON → Azure text-to-speech. Proposed a voice command
for each of the 8 endpoints and the error cases, plus a text box for testing without a microphone.

## 2. Setting up the folder
**Me:** "başlayalım kanka EE471 klasöründe mi kalayım?"

**AI:** Copy `Week4/library` (merged main) to `MiniProject2`, delete `main.py` and the old
`PROMPTS.md`, and check that `.env` exists and is ignored by git (`git check-ignore .env`).

## 3. Server side
**AI:** Gave three files:
- `speech.py` – Azure speech-to-text (WAV from the browser, phrase list for "check out", "DVD"…)
  and text-to-speech (JennyNeural voice). Reused from my Week 5 code.
- `voice_commands.py` – `parse_command()` (regular expressions: item number, action words,
  fields like `title`, `author`, `pages`, `duration`, list filters) and `build_reply()`
  (one sentence per endpoint and per error code).
- 3 new routes in `app.py`: `/api/voice/command`, `/api/voice/reply`, `/api/voice/speak`.
  The 8 Week 4 endpoints were not changed.

**Me:** "app.py'ı direkt verir misin şu anki halini de atıyorum sana"
*(give me the whole app.py instead of 3 separate edits)*

**AI:** Sent the complete file.

**Test (PowerShell):** `{"text": "Check out item 3"}` → `POST /api/items/3/checkout` ✅,
and `/api/voice/speak` produced `hello.wav` with the librarian's voice ✅.

## 4. Page
**AI:** Added a voice panel to `index.html` (microphone button, text box, result log with
"You said / Request / Response / Librarian") and appended CSS and JS. The browser calls the
real REST endpoint itself, so every request appears in the Flask log.

**Me:** (screenshot) "şu an konuşamadığım için sesli deneyemiyorum ama çalışıyordur herhalde"
*(I can't speak right now, it probably works)*

**AI:** The logic worked, but the voice panel had no styling. It also said "probably works"
is not enough: the microphone path must be tested with real speech before recording the video.

**Me:** pasted my `style.css` – the new CSS had not been added.
**AI:** Sent the complete `style.css`. After Ctrl+F5 the panel looked right, and
"Check out item 3" a second time returned 409 → "Sorry, item 3 is already checked out." ✅

## 5. Testing all endpoints
**AI:** Gave a test order: return, create, list, show, update (PATCH), replace (PUT),
checkout, delete while checked out (409), return + delete (204), show item 99 (404).

**Me:** "item 5 yok ki knk 4 item var" *(there is no item 5, only 4 items)*
**AI:** Item 5 is created by the "Create item…" command in step 2; IDs are never reused.

**Me:** "çalışıyor sıkıntı yok" – all endpoints answered correctly.

## Things I checked / corrected
1. **Missing CSS** – my first paste of the CSS was not saved; I replaced the whole file.
2. **Item IDs** – I expected item 5 to exist; it is only created by the voice "create" command,
   and deleted IDs are never reused, so the test order matters.
3. **Untested microphone** – typed commands were tested first; the microphone was tested
   separately before recording the demo video.
4. **Security** – the Azure key stays in the root `.env` (ignored by git); it is never shown
   in the code, the videos or this file.