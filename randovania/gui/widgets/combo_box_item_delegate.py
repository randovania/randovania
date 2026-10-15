from __future__ import annotations

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt


class ComboBoxItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[str] = []

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        combo = QtWidgets.QComboBox(parent)
        for item in self.items:
            combo.addItem(item)
        return combo

    def setEditorData(
        self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex
    ) -> None:
        assert isinstance(editor, QtWidgets.QComboBox)

        content = index.data(Qt.ItemDataRole.EditRole)
        idx = editor.findText(content)
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        assert isinstance(editor, QtWidgets.QComboBox)
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
