"""Turn a spoken sentence into an API request, and an API answer into a spoken reply.

parse_command("Check out item 3")
    -> {"action": "checkout", "method": "POST", "path": "/api/items/3/checkout", ...}

build_reply(command, 200, {...})
    -> "Item 3, 'The Catcher in the Rye', has been checked out."
"""
import re

# Small numbers Azure sometimes writes as words, plus common mishearings ("to" = 2)
NUMBER_WORDS = {
    "one": 1, "won": 1, "two": 2, "to": 2, "too": 2, "three": 3, "four": 4, "for": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}

# "item 3", "item number 3", "item #3", "item three"
ITEM_ID = r"\bitem\s+(?:number\s+|no\.?\s+|#\s*)?(\d+|" + "|".join(NUMBER_WORDS) + r")\b"

# Words that start a field inside create / replace / update commands
FIELD_WORDS = r"type|title|author|director|page count|pages|page|duration"


class CommandError(ValueError):
    """Raised when a sentence cannot be turned into a library command."""


# ================= Sentence -> request =================
def parse_command(text):
    """Return {"action", "method", "path", "body", "item_id"} for a spoken sentence."""
    sentence = text.strip()
    lower = normalize(sentence)
    if not lower:
        raise CommandError("I did not hear anything. Please try again.")

    item_id = find_item_id(lower)

    if re.match(r"(create|add|new)\b", lower):
        return make_command("create", "POST", "/api/items", body=parse_create_fields(sentence))

    if item_id is not None:
        if re.search(r"\breplace\b", lower):
            return make_command("replace", "PUT", f"/api/items/{item_id}", item_id,
                                parse_edit_fields(sentence, require_all=True))
        if re.search(r"\b(update|change|edit|rename|set)\b", lower):
            return make_command("update", "PATCH", f"/api/items/{item_id}", item_id,
                                parse_edit_fields(sentence))
        if re.search(r"\b(delete|remove)\b", lower):
            return make_command("delete", "DELETE", f"/api/items/{item_id}", item_id)
        if re.search(r"\b(check\s*-?\s*out|borrow|lend)\b", lower):
            return make_command("checkout", "POST", f"/api/items/{item_id}/checkout", item_id)
        if re.search(r"\b(return|give back|bring back|check\s*-?\s*in)\b", lower):
            return make_command("return", "POST", f"/api/items/{item_id}/return", item_id)
        if re.search(r"\b(show|get|find|describe|tell|what|read|details)\b", lower):
            return make_command("get", "GET", f"/api/items/{item_id}", item_id)

    if re.search(r"\b(list|show|what|which|all)\b", lower):
        return make_command("list", "GET", "/api/items" + parse_list_filters(lower))

    raise CommandError(
        "Sorry, I did not understand that command. "
        "Try for example: check out item 3."
    )


def normalize(text):
    """Lowercase, 'D.V.D.' -> 'dvd', and remove commas and sentence dots."""
    text = text.lower()
    text = re.sub(r"\bd\.?\s*v\.?\s*d\b\.?", "dvd", text)
    text = re.sub(r"[,!?;:]", " ", text)
    text = re.sub(r"\.(?=\s|$)", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_item_id(lower):
    """Return the number after the word 'item', or None."""
    match = re.search(ITEM_ID, lower)
    if not match:
        return None
    word = match.group(1)
    return int(word) if word.isdigit() else NUMBER_WORDS[word]


def make_command(action, method, path, item_id=None, body=None):
    return {"action": action, "method": method, "path": path,
            "item_id": item_id, "body": body}


def parse_list_filters(lower):
    """'list available books' -> '?available=true&type=book'."""
    params = []
    if re.search(r"\b(checked out|unavailable|not available|borrowed)\b", lower):
        params.append("available=false")
    elif re.search(r"\bavailable\b", lower):
        params.append("available=true")
    if re.search(r"\bbooks?\b", lower):
        params.append("type=book")
    elif re.search(r"\b(dvds?|movies?|films?)\b", lower):
        params.append("type=dvd")
    return "?" + "&".join(params) if params else ""


def split_fields(sentence):
    """'type book, title Dune, author Frank Herbert' -> {'type': 'book', 'title': 'Dune', ...}"""
    sentence = re.sub(r"\bD\.?\s*V\.?\s*D\b\.?", "DVD", sentence, flags=re.IGNORECASE)
    parts = re.split(rf"\b({FIELD_WORDS})\b", sentence, flags=re.IGNORECASE)
    fields = {}
    # parts = [text before the first field word, word, value, word, value, ...]
    for i in range(1, len(parts) - 1, 2):
        key, value = parts[i].lower(), parts[i + 1]
        key = "author" if key == "director" else "pages" if key.startswith("page") else key
        if key in ("title", "author"):
            # "author J.D. Salinger, 220 pages" / "director Denis Villeneuve, 155 minutes"
            value = re.sub(r"[\s,]*\d+\s*(pages?|minutes)\b.*$", "", value, flags=re.IGNORECASE)
            next_word = parts[i + 2].lower() if i + 2 < len(parts) else ""
            if next_word.startswith("page"):
                value = re.sub(r"[\s,]+\d+\s*$", "", value)
        value = value.strip(" ,.;:")
        if value and key not in fields:
            fields[key] = value
    return fields


def to_number(value, field):
    """'220' or '220 pages' -> 220. Raise CommandError if there is no number."""
    match = re.search(r"\d[\d,]*", value or "")
    if not match:
        raise CommandError(f"Please say a number for the {field}.")
    return int(match.group().replace(",", ""))


def parse_create_fields(sentence):
    """Body for POST /api/items."""
    fields = split_fields(sentence)
    lower = normalize(sentence)

    item_type = fields.get("type", "").lower()
    if not item_type:  # "create book ..." / "add a DVD ..."
        item_type = "dvd" if re.search(r"\bdvd\b", lower) else "book" if "book" in lower else ""
    if "dvd" in item_type:
        item_type = "dvd"
    elif "book" in item_type:
        item_type = "book"

    body = {"type": item_type, "title": fields.get("title"), "author": fields.get("author")}
    if item_type == "dvd":
        body["duration"] = number_field(fields, sentence, "duration")
    else:
        body["page_count"] = number_field(fields, sentence, "pages")
    return body


def parse_edit_fields(sentence, require_all=False):
    """Body for PUT / PATCH: only the fields that were said ('type' cannot be changed)."""
    fields = split_fields(sentence)
    body = {}
    for name in ("title", "author"):
        if name in fields:
            body[name] = fields[name]
    if "pages" in fields or re.search(r"\d+\s*pages\b", sentence, re.IGNORECASE):
        body["page_count"] = number_field(fields, sentence, "pages")
    if "duration" in fields or re.search(r"\d+\s*minutes\b", sentence, re.IGNORECASE):
        body["duration"] = number_field(fields, sentence, "duration")
    if not body and not require_all:
        raise CommandError("Please say what to change, for example: update item 3, title Dune.")
    return body


def number_field(fields, sentence, name):
    """Read 'pages 220' or '220 pages' (or 'duration 148' / '148 minutes')."""
    if name in fields:
        return to_number(fields[name], name)
    unit = "pages" if name == "pages" else "minutes"
    match = re.search(rf"(\d+)\s*{unit}\b", sentence, re.IGNORECASE)
    return int(match.group(1)) if match else None


# ================= API answer -> spoken reply =================
def build_reply(command, status, data):
    """Build the sentence the librarian says after the API call."""
    action = command["action"]
    item_id = command.get("item_id")

    if status >= 400:
        return error_reply(action, item_id, status, (data or {}).get("error", ""))

    if action == "create":
        return f"Successfully created {kind(data)} '{data['title']}' with ID {data['id']}."
    if action == "list":
        return list_reply(command["path"], data)
    if action == "get":
        return describe(data)
    if action == "replace":
        return (f"Item {item_id} has been replaced. "
                f"It is now the {kind(data)} '{data['title']}' by {data['author']}.")
    if action == "update":
        changes = ", ".join(f"{field_name(k)} is now {format_value(k, v)}"
                            for k, v in command["body"].items())
        return f"Item {item_id} has been updated: {changes}."
    if action == "delete":
        return f"Item {item_id} has been deleted."
    if action == "checkout":
        reply = f"Item {item_id}, '{data['item']['title']}', has been checked out."
        if data["item"]["type"] == "dvd":
            reply += " Please handle it with care and do not scratch the disc."
        return reply
    if action == "return":
        return f"Item {item_id}, '{data['item']['title']}', has been returned. Thank you."
    return "Done."


def error_reply(action, item_id, status, message):
    if status == 404:
        return f"Sorry, item {item_id} was not found." if item_id else "Sorry, that was not found."
    if status == 409:
        if action == "checkout":
            return f"Sorry, item {item_id} is already checked out."
        if action == "return":
            return f"Sorry, item {item_id} is not checked out, so it cannot be returned."
        if action == "delete":
            return f"Sorry, item {item_id} is checked out, so it cannot be deleted."
    return f"Sorry, I could not do that. {message}".strip()


def kind(item):
    return "DVD" if item["type"] == "dvd" else "book"


def describe(item):
    """'Item 3 is the book '1984' by George Orwell, 328 pages. It is available.'"""
    if item["type"] == "dvd":
        size = f"{item['duration']} minutes long"
    else:
        size = f"{item['page_count']} pages"
    status = "available" if item["is_available"] else "checked out"
    return (f"Item {item['id']} is the {kind(item)} '{item['title']}' by {item['author']}, "
            f"{size}. It is {status}.")


def list_reply(path, items):
    """'There are 2 available books: '1984' (item 3) and 'Dune' (item 5).'"""
    adjective = ("available " if "available=true" in path
                 else "checked out " if "available=false" in path else "")
    noun = "books" if "type=book" in path else "DVDs" if "type=dvd" in path else "items"
    if not items:
        return f"There are no {adjective}{noun} right now."
    if len(items) == 1:
        noun = noun[:-1]  # books -> book
    names = [f"'{item['title']}' (item {item['id']})" for item in items[:5]]
    if len(items) > 5:
        names.append(f"{len(items) - 5} more")
    listed = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    verb = "is" if len(items) == 1 else "are"
    return f"There {verb} {len(items)} {adjective}{noun}: {listed}."


def field_name(key):
    return {"page_count": "the page count", "duration": "the duration"}.get(key, f"the {key}")


def format_value(key, value):
    if key == "page_count":
        return f"{value} pages"
    if key == "duration":
        return f"{value} minutes"
    return f"'{value}'"