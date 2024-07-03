from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import _SubParsersAction

try:
    import PySide6  # noqa: F401

    has_gui = True
except ModuleNotFoundError:
    has_gui = False


def create_subparsers(sub_parsers: _SubParsersAction) -> None:
    if has_gui:
        from randovania.gui import qt

        return qt.create_subparsers(sub_parsers)
