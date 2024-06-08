from __future__ import annotations

import functools
import typing
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6 import QtWidgets

T = TypeVar("T")


def on_checked(widget: QtWidgets.QCheckBox, call: Callable[[bool], None]) -> None:
    @functools.wraps(call)
    def wrapper(value: int) -> None:
        return call(bool(value))

    widget.stateChanged.connect(wrapper)


def on_combo(widget: QtWidgets.QComboBox, call: Callable[[typing.Any], None]) -> None:
    @functools.wraps(call)
    def wrapper() -> None:
        return call(widget.currentData())

    widget.currentIndexChanged.connect(wrapper)


def set_combo_with_value(combo: QtWidgets.QComboBox, value: typing.Any) -> None:
    """
    Searches all items of the given combo for the given value and changes the current index to that one.
    :param combo:
    :param value:
    :return:
    """
    combo.setCurrentIndex(combo.findData(value))


def refresh_if_needed(combo: QtWidgets.QComboBox, func: Callable[[int], None]) -> None:
    if combo.currentIndex() == 0:
        func(0)


def clear_without_notify(combo: QtWidgets.QComboBox) -> None:
    """Clears the given QComboBox, while blocking any signals from being emitted."""
    old_blocking = combo.blockSignals(True)
    combo.clear()
    combo.blockSignals(old_blocking)
