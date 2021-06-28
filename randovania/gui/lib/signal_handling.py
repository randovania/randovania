import functools
from typing import Callable, TypeVar

from PySide2 import QtWidgets

T = TypeVar("T")


def on_checked(widget: QtWidgets.QCheckBox, call: Callable[[bool], None]):
    @functools.wraps(call)
    def wrapper(value: int):
        return call(bool(value))

    widget.stateChanged.connect(wrapper)


def combo_set_to_value(combo: QtWidgets.QComboBox, item):
    combo.setCurrentIndex(combo.findData(item))


def on_combo(widget: QtWidgets.QCheckBox, call: Callable[[T], None]):
    @functools.wraps(call)
    def wrapper():
        return call(widget.currentData())

    widget.currentIndexChanged.connect(wrapper)
