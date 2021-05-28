import dataclasses
import inspect
import typing
from enum import Enum


def _handle_optional(type_):
    if getattr(type_, "__origin__", None) is typing.Union and (
            len(type_.__args__) == 2 and type_.__args__[1] is type(None)):
        return type_.__args__[0]
    return type_


T = typing.TypeVar("T")


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
    def json_extra_arguments(cls):
        return {}

    @classmethod
    def from_json(cls: typing.Type[T], json_dict: dict, **extra) -> T:
        extra_args = cls.json_extra_arguments()
        extra_args.update(extra)

        new_instance = {}
        for field in dataclasses.fields(cls):
            if not field.init or (field.name not in json_dict and (field.default != dataclasses.MISSING
                                                                   or field.default_factory != dataclasses.MISSING)):
                continue
            arg = json_dict[field.name]
            if arg is not None:
                type_ = _handle_optional(field.type)
                if issubclass(type_, Enum):
                    arg = type_(arg)
                elif hasattr(type_, "from_json"):
                    arg_spec = inspect.getfullargspec(type_.from_json)
                    arg = type_.from_json(arg, **{
                        name: value
                        for name, value in extra_args.items()
                        if arg_spec.varkw is not None or name in arg_spec.args or name in arg_spec.kwonlyargs
                    })
            new_instance[field.name] = arg

        unknown_keys = set(json_dict.keys()) - set(new_instance.keys())
        if unknown_keys:
            raise ValueError(f"Unknown keys present in argument: {unknown_keys}")

        return cls(**new_instance)
