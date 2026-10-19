from flask import Flask, request, jsonify, render_template
from werkzeug.exceptions import HTTPException
from custom_classes import (
    Book, DVD, LibraryCollection, ItemNotFoundError, ItemStateError
)

app = Flask(__name__)

# Tek bir kütüphane, başlangıçta 4 öğe (karışık türler)
library = LibraryCollection()
library.add_item(Book("The Great Gatsby", "F. Scott Fitzgerald", 180))
library.add_item(DVD("Inception", "Christopher Nolan", 148))
library.add_item(Book("1984", "George Orwell", 328))
library.add_item(DVD("Arrival", "Denis Villeneuve", 116))


# ---------- Hataları durum koduna çevir ----------
@app.errorhandler(ItemNotFoundError)
def handle_not_found(e):
    return jsonify({"error": str(e)}), 404


@app.errorhandler(ItemStateError)
def handle_state_error(e):
    return jsonify({"error": str(e)}), 409


@app.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(HTTPException)
def handle_http_error(e):
    # Yanlış adres (404) veya yanlış metot (405) da JSON dönsün
    return jsonify({"error": e.description}), e.code


def read_json():
    """Read the request body as a JSON object, or raise ValueError."""
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")
    return data


# ---------- Sayfa ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- Endpoint'ler ----------
@app.route("/api/items", methods=["POST"])
def create_item():
    data = read_json()
    item = library.create_item(
        data.get("type"),
        data.get("title"),
        data.get("author"),
        page_count=data.get("page_count"),
        duration=data.get("duration"),
    )
    return jsonify(item.to_dict()), 201


@app.route("/api/items", methods=["GET"])
def list_items():
    available_arg = request.args.get("available")
    available = None
    if available_arg is not None:
        if available_arg not in ("true", "false"):
            raise ValueError("'available' must be 'true' or 'false'")
        available = available_arg == "true"
    items = library.list_items(available=available, item_type=request.args.get("type"))
    return jsonify([item.to_dict() for item in items]), 200


@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    return jsonify(library.get_item(item_id).to_dict()), 200


@app.route("/api/items/<int:item_id>", methods=["PUT"])
def replace_item(item_id):
    item = library.replace_item(item_id, **read_json())
    return jsonify(item.to_dict()), 200


@app.route("/api/items/<int:item_id>", methods=["PATCH"])
def patch_item(item_id):
    data = read_json()
    if not data:
        raise ValueError("No fields to update")
    item = library.update_item(item_id, **data)
    return jsonify(item.to_dict()), 200


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    library.remove_item(item_id)
    return "", 204


@app.route("/api/items/<int:item_id>/checkout", methods=["POST"])
def checkout_item(item_id):
    item = library.get_item(item_id)
    message = item.checkout()
    return jsonify({"message": message, "item": item.to_dict()}), 200


@app.route("/api/items/<int:item_id>/return", methods=["POST"])
def return_item(item_id):
    item = library.get_item(item_id)
    message = item.return_item()
    return jsonify({"message": message, "item": item.to_dict()}), 200


if __name__ == "__main__":
    app.run(debug=True)