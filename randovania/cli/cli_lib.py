from __future__ import annotations

import argparse
import enum
import statistics
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Sequence


class EnumAction(argparse.Action):
    """
    Argparse action for handling Enums
    """

    # Taken from https://stackoverflow.com/a/60750535

    def __init__(self, **kwargs: Any) -> None:
        # Pop off the type value
        enum_type: type | None = kwargs.pop("type", None)

        # Ensure an Enum subclass is provided
        if enum_type is None:
            raise ValueError("type must be assigned an Enum when using EnumAction")
        if not issubclass(enum_type, enum.Enum):
            raise TypeError("type must be an Enum when using EnumAction")

        # Generate choices from the Enum
        kwargs.setdefault("choices", tuple(e.value for e in enum_type))

        super().__init__(**kwargs)

        self._enum = enum_type

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        # Convert value back into an Enum
        value = self._enum(values)
        setattr(namespace, self.dest, value)


def add_debug_argument(parser: ArgumentParser) -> None:
    parser.add_argument("--debug", choices=range(4), type=int, default=0, help="The level of debug logging to print.")


def add_validate_argument(parser: ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--validate",
        action="store_true",
        dest="validate",
        default=True,
        help="After generating a layout, validate if it's possible. Default behaviour.",
    )
    group.add_argument(
        "--no-validate",
        action="store_false",
        dest="validate",
        default=True,
        help="After generating a layout, don't validate if it's possible.",
    )


def print_report_multiple_times(total_times: list[float]) -> None:
    print(
        f"Result after doing {len(total_times)} times:\n"
        f"Mean: {statistics.mean(total_times):.3f} seconds\n"
        f"stdev: {statistics.stdev(total_times):.3f} seconds\n"
        f"Median: {statistics.median(total_times):.3f} seconds"
    )
