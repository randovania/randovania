from __future__ import annotations

from PySide6 import QtGui
from PySide6.QtCore import Qt

from randovania.gui.lib.common_qt_lib import current_application
from randovania.gui.qt import RdvApplication

_current_dark_theme = None


def set_dark_theme(active: bool, compact: bool = False, *, app: RdvApplication | None = None) -> None:
    global _current_dark_theme
    if _current_dark_theme == active:
        return

    if app is None:
        app = current_application()
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

    QStatusBar QLabel:hover {
        background: transparent;
    }

    QStatusBar QProgressBar:hover {
        background: transparent;
    }
    """

    if active:
        new_palette.setColor(QtGui.QPalette.ColorRole.Link, Qt.GlobalColor.cyan)
        new_palette.setColor(QtGui.QPalette.ColorRole.LinkVisited, Qt.GlobalColor.cyan)
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

        new_palette.setColor(QtGui.QPalette.ColorRole.Link, Qt.GlobalColor.blue)

    _current_dark_theme = active
    app.setStyleSheet(style)
    app.setPalette(new_palette)
