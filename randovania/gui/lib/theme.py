import importlib
from pathlib import Path

from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt

import randovania

_current_dark_theme = None


def set_dark_theme(active: bool, compact: bool = False, *, app: QtWidgets.QApplication = None):
    global _current_dark_theme
    if _current_dark_theme == active:
        return

    if app is None:
        app = QtWidgets.QApplication.instance()
    new_palette = QtGui.QPalette(app.palette())

    import qdarktheme
    if active:
        palette = "dark"
    else:
        palette = "light"

    if randovania.is_frozen():
        # HACK: when frozen with pyinstaller, __spec__.origin is None which causes importlib.resources to not find where
        # the stylesheet.qss to be found
        x = Path(__file__).parents[3].joinpath("qdarktheme/dist", palette, "__init__.py")
        importlib.import_module(f"qdarktheme.dist.{palette}").__spec__.origin = x

    style = qdarktheme.load_stylesheet(theme=palette)
    if compact:
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
    
    style += "QScrollArea { border: default; }"

    if active:
        new_palette.setColor(QtGui.QPalette.Link, Qt.cyan)
        new_palette.setColor(QtGui.QPalette.LinkVisited, Qt.cyan)
    else:
        new_palette.setColor(QtGui.QPalette.Link, Qt.blue)

    _current_dark_theme = active
    app.setStyleSheet(style)
    app.setPalette(new_palette)
