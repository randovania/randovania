from PySide2 import QtWidgets

_current_dark_theme = False


def set_dark_theme(active: bool):
    global _current_dark_theme
    if _current_dark_theme == active:
        return

    if active:
        import qdarkstyle
        style = qdarkstyle.load_stylesheet(qt_api='pyside2')
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

    _current_dark_theme = active
    QtWidgets.QApplication.instance().setStyleSheet(style)
