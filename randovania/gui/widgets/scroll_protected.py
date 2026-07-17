from __future__ import annotations

import typing
from typing import Any, ClassVar

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QEvent, Qt


class ScrollProtectedWidgetMixin:
    """
    A mixin class for creating custom QWidgets that will not be
    affected by Mouse Wheel scrolling unless they are focused.
    """

    widget_type: ClassVar[type[QtWidgets.QWidget]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        assert isinstance(self, QtWidgets.QWidget)
        super().__init__(*args, **kwargs)

        self.installEventFilter(self)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def focusInEvent(self, event: QEvent) -> None:
        assert isinstance(self, QtWidgets.QWidget)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

    def focusOutEvent(self, event: QEvent) -> None:
        assert isinstance(self, QtWidgets.QWidget)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def eventFilter(self, watched: QtCore.QObject, event: QEvent, /) -> bool:
        assert isinstance(self, QtWidgets.QWidget)
        if event.type() == QEvent.Type.Wheel and isinstance(watched, self.widget_type):
            if watched.focusPolicy() == Qt.FocusPolicy.WheelFocus:
                event.accept()
                return False
            else:
                event.ignore()
                return True

        parent = typing.cast("QtWidgets.QWidget", super())  # eww
        return parent.eventFilter(watched, event)


class ScrollProtectedSlider(ScrollProtectedWidgetMixin, QtWidgets.QSlider):
    """
    A custom QSlider that will not be affected by Mouse Wheel scrolling unless it is focused.
    """

    widget_type = QtWidgets.QSlider

    def __init__(self, orientation: Qt.Orientation, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(orientation, parent)


class ScrollProtectedSpinBox(ScrollProtectedWidgetMixin, QtWidgets.QSpinBox):
    """
    A custom QSpinBox that will not be affected by Mouse Wheel scrolling unless it is focused.
    """

    widget_type = QtWidgets.QSpinBox

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)


class ScrollProtectedDoubleSpinBox(ScrollProtectedWidgetMixin, QtWidgets.QDoubleSpinBox):
    """
    A custom QDoubleSpinBox that will not be affected by Mouse Wheel scrolling unless it is focused.
    """

    widget_type = QtWidgets.QDoubleSpinBox

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)


class ScrollProtectedComboBox(ScrollProtectedWidgetMixin, QtWidgets.QComboBox):
    """
    A custom QComboBox that will not be affected by Mouse Wheel scrolling unless it is focused.
    """

    widget_type = QtWidgets.QComboBox

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
