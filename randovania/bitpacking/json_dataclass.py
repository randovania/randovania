import dataclasses
import typing
from enum import Enum


def _handle_optional(type_):
    if getattr(type_, "__origin__", None) is typing.Union and (
            len(type_.__args__) == 2 and type_.__args__[1] is type(None)):
        return type_.__args__[0]
    return type_


class JsonDataclass:
    @property
    def as_json(self) -> dict:
        result = {}
        for field in dataclasses.fields(self):
            if not field.init:
                continue
            value = getattr(self, field.name)
            if isinstance(value, Enum):
                value = value.value
            elif value is not None and hasattr(value, "as_json"):
                value = value.as_json
            result[field.name] = value
        return result

    @classmethod
    def from_json(cls, json_dict: dict) -> "JsonDataclass":
        kwargs = {}
        for field in dataclasses.fields(cls):
            if not field.init or (field.name not in json_dict and field.default != dataclasses.MISSING):
                continue
            arg = json_dict[field.name]
            if arg is not None:
                type_ = _handle_optional(field.type)
                if issubclass(type_, Enum):
                    arg = type_(arg)
                elif hasattr(type_, "from_json"):
                    arg = type_.from_json(arg)
            kwargs[field.name] = arg
        return cls(**kwargs)
