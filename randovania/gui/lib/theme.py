from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt

_current_dark_theme = False


def set_dark_theme(active: bool):
    global _current_dark_theme
    if _current_dark_theme == active:
        return

    app: QtWidgets.QApplication = QtWidgets.QApplication.instance()
    new_palette = QtGui.QPalette(app.palette())

    if active:
        import qdarkstyle
        style = qdarkstyle.load_stylesheet(qt_api='pyside2')
        new_palette.setColor(QtGui.QPalette.Link, Qt.cyan)
        new_palette.setColor(QtGui.QPalette.LinkVisited, Qt.cyan)
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
    else:
        style = ""
        new_palette.setColor(QtGui.QPalette.Link, Qt.blue)

    _current_dark_theme = active
    app.setStyleSheet(style)
    app.setPalette(new_palette)
