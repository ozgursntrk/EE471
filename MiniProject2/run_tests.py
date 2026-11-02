"""Runs all API tests in order and prints PASS/FAIL for each one."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000/api"

# (açıklama, metot, adres, gövde, beklenen kod)
TESTS = [
    ("List all",              "GET",    "/items", None, 200),
    ("Only available",        "GET",    "/items?available=true", None, 200),
    ("Only books",            "GET",    "/items?type=book", None, 200),
    ("Bad filter",            "GET",    "/items?type=cd", None, 400),
    ("Get one",               "GET",    "/items/1", None, 200),
    ("Get missing",           "GET",    "/items/99", None, 404),
    ("Create book",           "POST",   "/items", {"type": "book", "title": "The Catcher in the Rye", "author": "J.D. Salinger", "page_count": 220}, 201),
    ("Create DVD",            "POST",   "/items", {"type": "dvd", "title": "Interstellar", "author": "Christopher Nolan", "duration": 169}, 201),
    ("Create missing title",  "POST",   "/items", {"type": "book", "author": "Someone", "page_count": 100}, 400),
    ("PUT all fields",        "PUT",    "/items/{book}", {"title": "Catcher (2nd ed.)", "author": "J.D. Salinger", "page_count": 240}, 200),
    ("PUT missing fields",    "PUT",    "/items/{book}", {"title": "Only title"}, 400),
    ("PUT missing item",      "PUT",    "/items/99", {"title": "X", "author": "Y", "page_count": 10}, 404),
    ("PATCH one field",       "PATCH",  "/items/2", {"duration": 150}, 200),
    ("PATCH forbidden field", "PATCH",  "/items/2", {"id": 9}, 400),
    ("PATCH missing item",    "PATCH",  "/items/99", {"title": "X"}, 404),
    ("Checkout",              "POST",   "/items/2/checkout", None, 200),
    ("Checkout again",        "POST",   "/items/2/checkout", None, 409),
    ("Checkout missing",      "POST",   "/items/99/checkout", None, 404),
    ("Delete checked-out",    "DELETE", "/items/2", None, 409),
    ("Return",                "POST",   "/items/2/return", None, 200),
    ("Return again",          "POST",   "/items/2/return", None, 409),
    ("Return missing",        "POST",   "/items/99/return", None, 404),
    ("Delete",                "DELETE", "/items/2", None, 204),
    ("Delete again",          "DELETE", "/items/2", None, 404),
]


def send(method, path, body):
    """Send one request and return (status code, response text)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:   # 4xx cevapları da yakala
        return e.code, e.read().decode()


ids = {}       # oluşturulan kitabın id'sini hatırlamak için
passed = 0

for number, (name, method, path, body, expected) in enumerate(TESTS, start=1):
    path = path.format(**ids)
    status, text = send(method, path, body)

    if name == "Create book" and status == 201:
        ids["book"] = json.loads(text)["id"]

    ok = status == expected
    passed += ok
    mark = "PASS" if ok else "FAIL"
    print(f"{number:2}) [{mark}] {method:6} {path:24} -> {status} (expected {expected})  {name}")
    if text.strip():
        print("      " + text.strip().replace("\n", " ")[:120])

print(f"\n{passed}/{len(TESTS)} tests passed")