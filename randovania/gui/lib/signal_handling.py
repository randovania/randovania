import functools
from typing import Callable

from PySide2 import QtWidgets


def on_checked(widget: QtWidgets.QCheckBox, call: Callable[[bool], None]):
    @functools.wraps(call)
    def wrapper(value: int):
        return call(bool(value))

    widget.stateChanged.connect(wrapper)
