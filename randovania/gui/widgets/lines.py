from PySide6 import QtWidgets


def _line(shape: QtWidgets.QFrame.Shape, parent: QtWidgets.QWidget | None = None) -> QtWidgets.QFrame:
    line = QtWidgets.QFrame(parent)
    line.setFrameShape(shape)
    line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

    return line


def HLine(parent: QtWidgets.QWidget | None = None) -> QtWidgets.QFrame:
    """Create a prefabricated horizontal line, just like in Qt Creator"""
    return _line(QtWidgets.QFrame.Shape.HLine)


def VLine(parent: QtWidgets.QWidget | None = None) -> QtWidgets.QFrame:
    """Create a prefabricated vertical line, just like in Qt Creator"""
    return _line(QtWidgets.QFrame.Shape.VLine)
