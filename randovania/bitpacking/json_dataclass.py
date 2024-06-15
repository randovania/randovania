from __future__ import annotations

import dataclasses
import datetime
import inspect
import typing
import uuid
from enum import Enum

from frozendict import frozendict

from randovania.lib import type_lib

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance

T = typing.TypeVar("T")


def _decode_with_type(arg: typing.Any, type_: type, extra_args: dict) -> typing.Any:
    type_ = type_lib.resolve_optional(type_)[0]

    if arg is None:
        return None

    type_origin = typing.get_origin(type_) or type_

    if inspect.isclass(type_) and issubclass(type_, Enum):
        return type_(arg)

    elif type_lib.is_named_tuple(type_):
        return type_(**arg)

    elif type_origin == list:
        if type_args := typing.get_args(type_):
            value_types = type_args[0]
        else:
            value_types = typing.Any

        return [_decode_with_type(value, value_types, {}) for value in arg]

    elif type_origin == tuple:
        type_args = typing.get_args(type_)
        if type_args:
            if len(type_args) == 2 and type_args[1] == Ellipsis:
                value_types = [type_args[0]] * len(arg)
            else:
                value_types = type_args
        else:
            value_types = [typing.Any] * len(arg)

        return tuple(
            _decode_with_type(value, value_type, {}) for value, value_type in zip(arg, value_types, strict=True)
        )

    elif type_origin in (dict, frozendict):
        if type_args := typing.get_args(type_):
            key_type, value_types = type_args
        else:
            key_type, value_types = str, typing.Any

        return type_origin(
            (_decode_with_type(key, key_type, {}), _decode_with_type(value, value_types, {}))
            for key, value in arg.items()
        )

    elif type_ is uuid.UUID:
        return uuid.UUID(arg)

    elif type_ is datetime.datetime:
        return datetime.datetime.fromisoformat(arg)

    elif hasattr(type_, "from_json"):
        arg_spec = inspect.getfullargspec(type_.from_json)

        return type_.from_json(
            arg,
            **{
                name: value
                for name, value in extra_args.items()
                if arg_spec.varkw is not None or name in arg_spec.args or name in arg_spec.kwonlyargs
            },
        )

    return arg


def _encode_value(value: typing.Any) -> typing.Any:
    if isinstance(value, Enum):
        return value.value

    elif isinstance(value, uuid.UUID):
        return str(value)

    elif type_lib.is_named_tuple(type(value)):
        return _encode_value(value._asdict())

    elif isinstance(value, tuple | list):
        return [_encode_value(v) for v in value]

    elif isinstance(value, dict | frozendict):
        result = {_encode_value(k): _encode_value(v) for k, v in value.items()}
        if isinstance(value, frozendict):
            return frozendict(result)
        return result

    elif isinstance(value, datetime.datetime):
        return value.astimezone(datetime.UTC).isoformat()

    elif value is not None and hasattr(value, "as_json"):
        return value.as_json

    else:
        return value


class JsonDataclass:
    @property
    def as_json(self: DataclassInstance) -> dict:
        result = {}
        for field in dataclasses.fields(self):
            if not field.init or field.metadata.get("init_from_extra"):
                continue
            value = getattr(self, field.name)

            if field.metadata.get("exclude_if_default"):
                if field.default is not dataclasses.MISSING:
                    if value == field.default:
                        continue
                elif field.default_factory is not dataclasses.MISSING:
                    if value == field.default_factory():
                        continue
                else:
                    raise RuntimeError(f"exclude_if_default, but field {field.name} has no default?")

            result[field.name] = _encode_value(value)
        return result

    @classmethod
    def json_extra_arguments(cls) -> dict:
        return {}

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        assert issubclass(cls, JsonDataclass)
        extra_args = cls.json_extra_arguments()
        extra_args.update(extra)

        resolved_types = typing.get_type_hints(cls)
        dc: type[DataclassInstance] = cls  # type: ignore[assignment]

        new_instance = {}
        for field in dataclasses.fields(dc):
            if not field.init or (
                field.name not in json_dict
                and (field.default != dataclasses.MISSING or field.default_factory != dataclasses.MISSING)
            ):
                continue

            if field.metadata.get("init_from_extra"):
                arg = extra_args[field.name]
            else:
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
