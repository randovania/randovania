import functools
from typing import Callable, TypeVar

from PySide6 import QtWidgets

T = TypeVar("T")


def on_checked(widget: QtWidgets.QCheckBox, call: Callable[[bool], None]):
    @functools.wraps(call)
    def wrapper(value: int):
        return call(bool(value))

    widget.stateChanged.connect(wrapper)


def on_combo(widget: QtWidgets.QComboBox, call: Callable[[T], None]):
    @functools.wraps(call)
    def wrapper():
        return call(widget.currentData())

    widget.currentIndexChanged.connect(wrapper)


def set_combo_with_value(combo: QtWidgets.QComboBox, value):
    """
    Searches all items of the given combo for the given value and changes the current index to that one.
    :param combo:
    :param value:
    :return:
    """
    combo.setCurrentIndex(combo.findData(value))
