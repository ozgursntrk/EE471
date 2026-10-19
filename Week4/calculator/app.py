from flask import Flask, request, jsonify, render_template

app = Flask(__name__)


def calculate(a, b, operation):
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            raise ZeroDivisionError("Division by zero")
        return a / b
    raise ValueError("Unknown operation")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    print("GELEN:", request.headers.get("Content-Type"), request.data)
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        a = float(data["a"])
        b = float(data["b"])
        operation = data["operation"]
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid input"}), 400

    try:
        result = calculate(a, b, operation)
    except (ZeroDivisionError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    if result == int(result):
        result = int(result)
    return jsonify({"result": result}), 200


if __name__ == "__main__":
    app.run(debug=True)