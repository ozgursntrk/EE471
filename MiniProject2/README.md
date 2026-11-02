# EE 471 – Mini Project 2: Voice-activated Library App

The Week 4 Library REST API with a **voice librarian**: speak a command, the app calls the
matching endpoint and speaks the result back (Azure Speech Services).

## How it works

```
🎤 speech ──► /api/voice/command ──► Azure speech-to-text ──► "Check out item 3"
                                     voice_commands.parse_command()
                                     ──► {"method": "POST", "path": "/api/items/3/checkout"}
browser ──► POST /api/items/3/checkout   (the normal Week 4 endpoint)
browser ──► /api/voice/reply  ──► build_reply() ──► "Item 3, '1984', has been checked out."
browser ──► /api/voice/speak  ──► Azure text-to-speech ──► 🔊 played in the browser
```

| File | Purpose |
|---|---|
| `app.py` | Flask app: the 8 Week 4 endpoints (unchanged) + 3 voice endpoints |
| `custom_classes.py` | Book, DVD, LibraryCollection and the business rules (from Week 4) |
| `voice_commands.py` | Sentence → API request, and API answer → spoken sentence |
| `speech.py` | Azure Speech: speech-to-text and text-to-speech |
| `templates/`, `static/` | Library page + voice panel (microphone, text box, result log) |
| `run_tests.py`, `tests.http` | Week 4 API tests (still pass) |

## Setup

1. Create an Azure Speech resource and copy its key and region.
2. In the **repository root**, copy `.env.example` to `.env` and fill it in:
   ```
   SPEECH_KEY=your_azure_speech_key
   SPEECH_REGION=westeurope
   ```
   `.env` is listed in `.gitignore`, so the key is never pushed to GitHub.
3. Install and run:
   ```
   cd MiniProject2
   pip install -r requirements.txt
   python app.py
   ```
4. Open http://127.0.0.1:5000, click 🎤, say a command, click 🎤 again.
   You can also type the command in the text box and press **Run**.

## Voice commands

| Endpoint | Example command | Librarian's answer |
|---|---|---|
| `POST /api/items` | "Create item, type book, title The Catcher in the Rye, author J.D. Salinger, pages 220" | "Successfully created book 'The Catcher in the Rye' with ID 5." |
| `POST /api/items` (DVD) | "Create item, type DVD, title Interstellar, director Christopher Nolan, duration 169" | "Successfully created DVD 'Interstellar' with ID 6." |
| `GET /api/items` | "List items" / "List available books" / "List checked out DVDs" | "There are 3 available books: ..." |
| `GET /api/items/<id>` | "Show item 3" | "Item 3 is the book '1984' by George Orwell, 328 pages. It is available." |
| `PUT /api/items/<id>` | "Replace item 5, title Animal Farm, author George Orwell, pages 112" | "Item 5 has been replaced. It is now the book 'Animal Farm' by George Orwell." |
| `PATCH /api/items/<id>` | "Update item 2, duration 150" | "Item 2 has been updated: the duration is now 150 minutes." |
| `DELETE /api/items/<id>` | "Delete item 4" | "Item 4 has been deleted." |
| `POST /api/items/<id>/checkout` | "Check out item 3" | "Item 3, '1984', has been checked out." |
| `POST /api/items/<id>/return` | "Return item 3" | "Item 3, '1984', has been returned. Thank you." |

Errors are spoken too:

| Case | Answer |
|---|---|
| 409 – checkout twice | "Sorry, item 3 is already checked out." |
| 409 – return an available item | "Sorry, item 3 is not checked out, so it cannot be returned." |
| 409 – delete a checked-out item | "Sorry, item 3 is checked out, so it cannot be deleted." |
| 404 – unknown id | "Sorry, item 99 was not found." |
| 400 – invalid data | "Sorry, I could not do that. Missing fields: author, page_count" |
| Command not understood | "Sorry, I did not understand that command. Try for example: check out item 3." |

## Voice endpoints

| Endpoint | Input | Output |
|---|---|---|
| `POST /api/voice/command` | WAV file (`audio`) or JSON `{"text": "..."}` | `{"heard", "command": {"action", "method", "path", "body", "item_id"}}` |
| `POST /api/voice/reply` | `{"command", "status", "data"}` | `{"reply": "..."}` |
| `POST /api/voice/speak` | `{"text": "..."}` | `audio/wav` |

Note: the data is kept in memory (as in Week 4), so restarting the server resets the library to its 4 starting items.