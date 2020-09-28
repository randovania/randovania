from PySide2 import QtWidgets

_current_dark_theme = False


def set_dark_theme(active: bool):
    global _current_dark_theme
    if _current_dark_theme == active:
        return

    if active:
        import qdarkstyle
        style = qdarkstyle.load_stylesheet(qt_api='pyside2')
    else:
        style = ""

    _current_dark_theme = active
    QtWidgets.QApplication.instance().setStyleSheet(style)
