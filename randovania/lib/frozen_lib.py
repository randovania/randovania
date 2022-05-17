from __future__ import annotations

import typing

from frozendict import frozendict


def unwrap(extra: typing.Any) -> typing.Any:
    if isinstance(extra, tuple):
        return [unwrap(value) for value in extra]

    elif isinstance(extra, frozendict):
        return {key: unwrap(value) for key, value in extra.items()}

    else:
        return extra


def wrap(extra: typing.Any) -> typing.Any:
    if isinstance(extra, list):
        return tuple(wrap(value) for value in extra)

    elif isinstance(extra, dict):
        return frozendict((key, wrap(value)) for key, value in extra.items())

    else:
        return extra
