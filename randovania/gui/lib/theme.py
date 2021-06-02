from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt

_current_dark_theme = None


def set_dark_theme(active: bool, app: QtWidgets.QApplication = None):
    global _current_dark_theme
    if _current_dark_theme == active:
        return

    if app is None:
        app = QtWidgets.QApplication.instance()
    new_palette = QtGui.QPalette(app.palette())

    import qdarkstyle
    if active:
        palette = qdarkstyle.DarkPalette
    else:
        palette = qdarkstyle.LightPalette

    style = qdarkstyle.load_stylesheet(qt_api='pyside2', palette=palette)
    style += """
    QGroupBox {
        padding: 0px;
    }
    QGroupBox::title {
        padding-bottom: 12px;
    }
    QComboBox {
        padding-right: 10px;
    }
    QPushButton {
        min-width: 60px;
    }
    QToolButton {
        border: 1px solid #32414B;
    }

        """

    if active:
        new_palette.setColor(QtGui.QPalette.Link, Qt.cyan)
        new_palette.setColor(QtGui.QPalette.LinkVisited, Qt.cyan)
    else:
        new_palette.setColor(QtGui.QPalette.Link, Qt.blue)

    _current_dark_theme = active
    app.setStyleSheet(style)
    app.setPalette(new_palette)
