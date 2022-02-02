from PySide2 import QtWidgets


class ScrollMessageBox(QtWidgets.QMessageBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        children: list[QtWidgets.QWidget] = self.children()

        grid = self.findChild(QtWidgets.QGridLayout)
        assert isinstance(grid, QtWidgets.QGridLayout)

        old_label = None
        position = None
        for i, it in enumerate(children):
            if it.objectName() == "qt_msgbox_label":
                position = grid.getItemPosition(i)
                old_label = it
                break
        assert old_label is not None
        assert position is not None

        label = QtWidgets.QLabel(old_label.text(), self)
        label.setWordWrap(True)

        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(label)
        scroll.setMinimumSize(400, 200)
        grid.addWidget(scroll, *position)

        old_label.setText('')

    @classmethod
    def create_new(
            cls,
            parent: QtWidgets.QWidget,
            icon: QtWidgets.QMessageBox.Icon,
            title: str,
            body: str,
            buttons: QtWidgets.QMessageBox.StandardButtons,
            default_button: QtWidgets.QMessageBox.StandardButton,
    ) -> "ScrollMessageBox":
        box = cls(icon, title, body, buttons, parent)
        box.setDefaultButton(default_button)
        return box
