from __future__ import annotations

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt


class ComboBoxItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self):
        super().__init__()
        self.items = []

    def createEditor(
        self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ) -> QtWidgets.QWidget:
        combo = QtWidgets.QComboBox(parent)
        for item in self.items:
            combo.addItem(item)
        return combo

    def setEditorData(self, editor: QtWidgets.QComboBox, index: QtCore.QModelIndex) -> None:
        content = index.data(Qt.ItemDataRole.EditRole)
        idx = editor.findText(content)
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(
        self, editor: QtWidgets.QComboBox, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex
    ) -> None:
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
