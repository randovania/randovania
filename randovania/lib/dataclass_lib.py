from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


def get_field(dataclass: DataclassInstance | type[DataclassInstance], field_name: str) -> dataclasses.Field:
    """
    Returns the `Field` object for a given dataclass and field name.

    :param dataclass: The dataclass (type or instance) to pull from.
    :param field_name: The name of the field.
    :return: The `Field` object.
    :raises AttributeError: The field does not exist.
    """
    try:
        return next(field for field in dataclasses.fields(dataclass) if field.name == field_name)
    except StopIteration:
        if not isinstance(dataclass, type):
            dataclass = type(dataclass)
        raise AttributeError(f"{dataclass.__name__} has no field '{field_name}'")
