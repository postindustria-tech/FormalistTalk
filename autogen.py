from dataclasses import fields, MISSING, is_dataclass


def describe_array(arr_type):
    if not (len(arr_type) == 1 or isinstance(arr_type[0], type)):
        print(f"Unknown list type {arr_type}")
        return None

    return {
        "type": "array",
        "items": describe(arr_type[0])
    }


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
