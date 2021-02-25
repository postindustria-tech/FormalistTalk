from functools import wraps
from inspect import getfullargspec

from flask import request, jsonify
from jsonschema import validate, ValidationError


class JSONValidationError(Exception):
    def __init__(self, message, path):
        super(JSONValidationError, self).__init__(message)
        self.message = message
        self.path = path


def _format_json_path(path) -> str:
    parts = []
    first = True
    for item in path:
        if isinstance(item, str):
            if first:
                parts.append(item)
                first = False
            else:
                parts.extend((".", item))
        elif isinstance(item, int):
            parts.append(f"[{item}]")

    return "".join(parts)


def validate_json(content, schema):
    try:
        validate(content, schema=schema)
    except ValidationError as ex:
        raise JSONValidationError(ex.message, _format_json_path(ex.path))


def validate_content(schema):
    def decorator(f):
        argspec = getfullargspec(f)
        inject_content = "content" in argspec.args or argspec.varkw is not None

        @wraps(f)
        def decorated_function(*args, **kwargs):
            content = request.get_json()
            try:
                if len(schema) > 0:
                    validate_json(request.get_json(), schema)
            except JSONValidationError as ex:
                return jsonify(error=ex.message, path=ex.path), 400

            if inject_content and "content" not in kwargs:
                kwargs["content"] = content

            return f(*args, **kwargs)
        return decorated_function
    return decorator
