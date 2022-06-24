import dataclasses
import types

from randovania.lib import type_lib


class DataclassPostInitTypeCheck:
    def __post_init__(self):
        for f in dataclasses.fields(self):
            v = getattr(self, f.name)
            resolved_type, optional = type_lib.resolve_optional(f.type)
            if optional and v is None:
                continue

            if isinstance(resolved_type, types.GenericAlias):
                type_args = resolved_type.__args__
                resolved_type = resolved_type.__origin__
            else:
                type_args = None

            if not isinstance(v, resolved_type):
                raise ValueError(f"Unexpected type for field {f.name} ({v}): Got {type(v)}, expected {f.type}.")

            if resolved_type is dict and type_args is not None:
                assert isinstance(v, dict)
                errors = []
                for key, item in v.items():
                    if not isinstance(key, type_args[0]):
                        errors.append(f"For key {key}, expected type {type_args[0]} got {type(key)}.")

                    if not isinstance(item, type_args[1]):
                        errors.append(f"For value {item} (key {key}), expected type {type_args[1]} got {type(item)}.")

                if errors:
                    raise ValueError(f"Errors for field {f.name} ({v}):\n" + "\n".join(errors))

            if resolved_type is set and type_args is not None:
                assert isinstance(v, set)
                errors = []
                for item in v:
                    if not isinstance(item, type_args[0]):
                        errors.append(f"For value {item}, expected type {type_args[1]} got {type(item)}.")
                if errors:
                    raise ValueError(f"Errors for field {f.name} ({v}):\n" + "\n".join(errors))

            if "min" in f.metadata:
                if v < f.metadata["min"]:
                    raise ValueError(f"Field {f.name} has value {v}, which is less than minimum {f.metadata['min']}")

            if "max" in f.metadata:
                if v > f.metadata["max"]:
                    raise ValueError(f"Field {f.name} has value {v}, which is more than maximum {f.metadata['max']}")
