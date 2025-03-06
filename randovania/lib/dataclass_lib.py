from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from _typeshed import DataclassInstance


def get_field(dataclass: DataclassInstance | type[DataclassInstance], field_name: str) -> dataclasses.Field:
    return next(field for field in dataclasses.fields(dataclass) if field.name == field_name)


def get_metadata_for_field(
    dataclass: DataclassInstance | type[DataclassInstance], field_name: str
) -> Mapping[Any, Any]:
    return get_field(dataclass, field_name).metadata
