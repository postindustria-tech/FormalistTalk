![left fit](logo.png)

# Валидация данных в Python 

**С JSON Schema и щепоткой магии**

Павел Дмитриев

Fullstack mobile developer

---

# Немного воды

* Большая часть работы backend — обработка JSON
* Формат JSON — достаточно свободный, ошибки случаются часто

Есть много различных способов валидации

* WTForms
* Cerberus
* Тысячи их
* JSONSchema

---

# Кратко про синтаксис

Наш примеер JSON:

[.code-highlight: 1-4]
[.code-highlight: 5]
[.code-highlight: 6]
[.code-highlight: 7-15]
[.code-highlight: all]

```json
{
    "id": 1,
    "name": "Example model",
    "scale": 0.3,
    "rotation": [ 0, 0, 1 ],
    "thumbnailUrl": null,
    "materials": [{
        "name": "metal1",
        "shader": "shine/metal",
    }, {
        "name": "metal2",
        "shader": "shine/metal",
    }, {
        "name": "wood1",
        "shader": "regular/wood",
    }]
}
```

---

# Кратко про синтаксис

```json
{
    "type": "object",
    "properties": {
        "id": {
            "type": "integer"
        },
        "name": {
            "type": "string",
            "minLength": 1,
        }
    // ...
    },
    "required": ["id", "name"]
}
```

---

# Синтаксис: списки

```json
{
    "rotation": {
        "type": "array",
        "items": {
            "type": "number",
        },
        "minItems": 3,
        "maxItems": 3,
    }
}
```

---

# Синтаксис: опциональные значения

Мы можем использовать возможности Python для переиспользования фрагментов

```python
optional_non_empty_string = {
    "type": ["string", "null"],
    "minLength": 1
}
```

Пример использования

```python
{
    "thumbnailUrl": optional_non_empty_string
}
```

--- 

# Синтаксис: вложенные словари

```json
{
    "materials": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "material": {
                    "type": "string",
                    "minLength": 1,
                },
                "object": {
                    "type": "string",
                    "minLength": 1,
                },
            },
            "required": ["material", "object"],
        }
    }
}
```

---

# Переиспользование наборов полей

```python
_field_set = {
    "fieldA": {"type": "integer"},
    "fieldB": {"type": "string"}
}
```

Включение в более общую схему

```python
update_model_schema = {
    "type": "object",
    "properties": {
        **_field_set,
    },
    "additionalProperties": False,
    "minProperties": 1,
}

insert_model_schema = {
    "type": "object",
    "properties": {
        **_field_set,
    },
    "additionalProperties": False,
    "required": ["fieldA", "fieldB"],
}

```

---

# Data classes в Python

[.code-highlight: 1-4, 13-20]
[.code-highlight: all]

```python
from dataclasses import dataclass
from typing import List, Optional

from utils.helpers import default_empty_list


@dataclass
class Material:
    object: str
    material: str


@dataclass
class Model:
    id: int
    name: str
    thumbnail_url: Optional[str] = None
    rotation: [float]
    scale: float
    materials: List[Material] = default_empty_list
```

---

# Что за default\_empty\_list?

```python
from dataclasses import field

def default_field(obj):
    return field(default_factory=lambda: copy(obj))


default_empty_list = field(default_factory=lambda: [])
```

---

# Валидация

```python
from jsonschema import validate, ValidationError


class JSONValidationError(Exception):
    def __init__(self, message, path):
        super(JSONValidationError, self).__init__(message)
        self.message = message
        self.path = path

def validate_json(content, schema):
    try:
        validate(content, schema=schema)
    except ValidationError as ex:
        raise JSONValidationError(ex.message, _format_json_path(ex.path))
```

---

# Преобразуем `path`

```python
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
```

---

# Магия декораторов

[.code-highlight: 10-16]
[.code-highlight: 17-18]
[.code-highlight: 5-6,17-18]
[.code-highlight: all]

```python
from inspect import getfullargspec

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
```

---

# Автогенерация

```python
from dataclasses import dataclass, fields, MISSING, is_dataclass


@dataclass
class Child:
    field: float = 0.1


@dataclass
class Simple:
    name: str
    age: int
    extra: Child
    lists: [int]
```

---

# Описание dataclass

```python
def describe_dataclass(dc):
    required = []
    properties = {}

    for dc_field in fields(dc):
        if (description := describe(dc_field.type)) is not None:
            properties[dc_field.name] = description
        else:
            print(f"Unknown field type: {dc_field.type}")
            break
        if dc_field.default == MISSING:
            required.append(dc_field.name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
```

---

# Описание полей

```python
def describe(dc_field):
    if is_dataclass(dc_field):
        return describe_dataclass(dc_field)
    elif isinstance(dc_field, list):
        return describe_array(dc_field)
    elif dc_field == str:
        return {"type": "string"}
    elif dc_field == int:
        return {"type": "integer"}
    elif dc_field == float:
        return {"type": "number"}
```

---

# Описание списков

[.code-highlight: 1]
[.code-highlight: 1-4]
[.code-highlight: all]
```python
def describe_array(arr_type):
    if not (len(arr_type) == 1 or isinstance(arr_type[0], type)):
        print(f"Unknown list type {arr_type}")
        return None

    return {
        "type": "array",
        "items": describe(arr_type[0])
    }
```

---

# Что же получилось?

```python
{
    'type': 'object', 
    'properties': {
        'id': {'type': 'integer'}, 
        'name': {'type': 'string'}, 
        'url': {'type': 'string'}, 
        'rotation': {
            'type': 'array', 
            'items': {'type': 'number'}
        }, 
        'scale': {'type': 'number'}, 
        'thumbnail_url': {'type': 'string'}, 
        'materials': {
            'type': 'array', 
            'items': {
                'type': 'object', 
                'properties': {
                    'object': {'type': 'string'}, 
                    'material': {'type': 'string'}
                }, 
                'required': ['object', 'material']
            }
        }
    }, 
    'required': ['id', 'name', 'url', 'rotation', 'scale', 'materials']
}
```

---

# Демонстрация и вопросы
