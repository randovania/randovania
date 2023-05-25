import dataclasses
import datetime
import inspect
import typing
import uuid
from enum import Enum

from randovania.lib import type_lib

T = typing.TypeVar("T")


def _decode_with_type(arg: typing.Any, type_: type, extra_args: dict) -> typing.Any:
    type_ = type_lib.resolve_optional(type_)[0]

    if arg is None:
        return None

    if issubclass(type_, Enum):
        return type_(arg)

    elif typing.get_origin(type_) == list:
        if type_args := typing.get_args(type_):
            value_type = type_args[0]
        else:
            value_type = typing.Any

        return [
            _decode_with_type(value, value_type, {})
            for value in arg
        ]

    elif typing.get_origin(type_) == dict:
        if type_args := typing.get_args(type_):
            key_type, value_type = type_args
        else:
            key_type, value_type = str, typing.Any

        return {
            _decode_with_type(key, key_type, {}): _decode_with_type(value, value_type, {})
            for key, value in arg.items()
        }
    
    elif type_lib.is_named_tuple(type_):
        return type_(**arg)

    elif type_ is uuid.UUID:
        return uuid.UUID(arg)

    elif type_ is datetime.datetime:
        return datetime.datetime.fromisoformat(arg)

    elif hasattr(type_, "from_json"):
        arg_spec = inspect.getfullargspec(type_.from_json)

        return type_.from_json(arg, **{
            name: value
            for name, value in extra_args.items()
            if arg_spec.varkw is not None or name in arg_spec.args or name in arg_spec.kwonlyargs
        })

    return arg


def _encode_value(value: typing.Any) -> typing.Any:
    if isinstance(value, Enum):
        value = value.value

    elif isinstance(value, uuid.UUID):
        value = str(value)

    elif isinstance(value, list):
        value = [
            _encode_value(v)
            for v in value
        ]

    elif isinstance(value, dict):
        value = {
            _encode_value(k): _encode_value(v)
            for k, v in value.items()
        }
    
    elif type_lib.is_named_tuple(type(value)):
        value = _encode_value(value._asdict())

    elif isinstance(value, datetime.datetime):
        return value.astimezone(datetime.timezone.utc).isoformat()

    elif value is not None and hasattr(value, "as_json"):
        value = value.as_json

    return value


class JsonDataclass:
    @property
    def as_json(self) -> dict:
        result = {}
        for field in dataclasses.fields(self):
            if not field.init:
                continue
            value = getattr(self, field.name)
            result[field.name] = _encode_value(value)
        return result

    @classmethod
    def json_extra_arguments(cls):
        return {}

    @classmethod
    def from_json(cls: type[T], json_dict: dict, **extra) -> T:
        extra_args = cls.json_extra_arguments()
        extra_args.update(extra)

        resolved_types = typing.get_type_hints(cls)

        new_instance = {}
        for field in dataclasses.fields(cls):
            if not field.init or (field.name not in json_dict and (field.default != dataclasses.MISSING
                                                                   or field.default_factory != dataclasses.MISSING)):
                continue
            arg = json_dict[field.name]
            if arg is not None:
                field_type = field.type
                if isinstance(field_type, str):
                    field_type = resolved_types[field.name]

                arg = _decode_with_type(arg, field_type, extra_args)

            new_instance[field.name] = arg

        unknown_keys = set(json_dict.keys()) - set(new_instance.keys())
        if unknown_keys:
            raise ValueError(f"Unknown keys present in argument: {unknown_keys}")

        return cls(**new_instance)
