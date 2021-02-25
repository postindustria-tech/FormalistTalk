from flask import Flask, jsonify, request

from autogen import describe_dataclass
from model import Model, Material
from validation import validate_content

app = Flask(__name__)


@app.route('/', methods=["GET"])
def index():
    return jsonify(ok=True)


@app.route("/", methods=["POST"])
@validate_content(describe_dataclass(Model))
def update_model():
    content = request.get_json()
    content["materials"] = [
        Material(**item) for item in content.pop("materials")
    ]

    model = Model(**content)
    return jsonify(model)


if __name__ == '__main__':
    app.run()
