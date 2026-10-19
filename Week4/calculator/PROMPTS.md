# Section 1 – Prompts & Corrections

AI tool used: Claude (chat)

## Main prompts
1. "Turn my Figma calculator design into a web page (HTML/CSS/JS) served by Flask.
   Do not calculate in JavaScript; send POST /api/calculate with JSON
   {"a": number, "b": number, "operation": "add|subtract|multiply|divide"}.
   Do not use eval(). Return an error for invalid input and division by zero."
2. "Give me test requests for the API so I can test it without the web page."
3. "When I click an operator (÷, ×, ...) nothing appears on the screen. Fix it."

## Corrections I made
1. **API test returned 400 "Request body must be JSON".**
   I added a debug print and saw the request arrived with no body. The cause was
   the REST Client extension sending only the selected text. I fixed how I sent
   the request and changed `get_json(silent=True)` to
   `get_json(force=True, silent=True)` so the body is parsed reliably.
2. **Operator was not visible on the display.**
   The first version of script.js stored the operator silently, so the user could
   not see "8 ÷". I rewrote the display logic with a `render()` function that shows
   the full expression (e.g. "8 ÷ 2") and lets the user change the operator.
3. **Checked that eval() is not used.** All operations are handled with explicit
   if-statements in `calculate()` in app.py.
4. **Thunder Client required a paid license**, so I switched to the free
   REST Client extension and saved my tests in `tests.http`.