import dataclasses

import typing


def _handle_optional(type_):
    if getattr(type_, "__origin__", None) is typing.Union and (
            len(type_.__args__) == 2 and type_.__args__[1] is type(None)):
        return type_.__args__[0], True
    return type_, False


class DataclassPostInitTypeCheck:
    def __post_init__(self):
        for f in dataclasses.fields(self):
            v = getattr(self, f.name)
            resolved_type, optional = _handle_optional(f.type)
            if optional and v is None:
                continue
            if not isinstance(v, resolved_type):
                raise ValueError(f"Unexpected type for field {f.name} ({v}): Got {type(v)}, expected {f.type}.")
