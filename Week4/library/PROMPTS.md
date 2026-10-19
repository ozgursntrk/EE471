# Section 2 – Prompts & Corrections

AI tool used: Claude (chat)

## Main prompts
1. "Extend my Week 3 custom_classes.py: add ItemNotFoundError and ItemStateError,
   unique ids that are never reused, to_dict(), exceptions instead of return strings,
   and get_item / list_items / update_item / remove_item."
2. "Write app.py exposing LibraryCollection as a REST API with these 8 endpoints.
   Routes must only translate HTTP to method calls; all rules stay in custom_classes.py."
3. "Give me a way to run all API tests at once and see PASS/FAIL."
4. "Build a single-page frontend (index.html, style.css, script.js) like the design:
   item cards, checkout/return, edit, delete, add/edit form, filters, error area."

## Things the AI got wrong that I fixed
1. **DVD reminder was lost.** The model returns the "Handle with care" reminder in the
   checkout message, but the first frontend ignored the response, so the user never
   saw it. I added a green info area and show the API's message after checkout.
2. **Stale error message.** After a failed delete (409), the red error stayed on screen
   even after opening the Add Item form. I clear the error/info areas when the user
   starts a new action.
3. **Validation rules were not reusable.** The first update_item had its checks inline,
   so POST (create) and PUT would have duplicated them. I moved them into
   `_validate_fields()` and added `create_item()` / `replace_item()` in
   custom_classes.py, so app.py stays a thin HTTP layer.

## Review notes
- No business rule is duplicated in JavaScript: e.g. deleting a checked-out item is
  sent to the API, and the 409 message is displayed in the error area.
- DELETE returns 204 with an empty body; script.js does not try to parse JSON for it.
- All 24 endpoint tests pass (`python run_tests.py`).