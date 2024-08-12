from __future__ import annotations

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt

_current_dark_theme = None


def set_dark_theme(active: bool, compact: bool = False, *, app: QtWidgets.QApplication = None):
    global _current_dark_theme
    if _current_dark_theme == active:
        return

    if app is None:
        app = QtWidgets.QApplication.instance()
    new_palette = QtGui.QPalette(app.palette())

    import qdarktheme

    style = qdarktheme.load_stylesheet(theme="dark" if active else "light")
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

    style += """

    QScrollArea {
        border: default;
    }

    QListWidget::item {
        padding: 6px;
        border: 0px solid red; /* FIXME: ugly hack to make item not jump around on hover/selection*/
    }
    """

    if active:
        new_palette.setColor(QtGui.QPalette.Link, Qt.cyan)
        new_palette.setColor(QtGui.QPalette.LinkVisited, Qt.cyan)
        style += """
        QToolTip {
            background-color: black;
            color: white;
            border: black solid 1px
        }

        QListWidget::item::disabled {
            color: rgba(204, 205, 206, 1.000);
        }
        """
    else:
        style += """
        QListWidget::item::disabled {
            color: rgba(72, 74, 76, 1.000);
        }
        """

        new_palette.setColor(QtGui.QPalette.Link, Qt.blue)

    _current_dark_theme = active
    app.setStyleSheet(style)
    app.setPalette(new_palette)
