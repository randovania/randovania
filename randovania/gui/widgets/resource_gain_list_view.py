from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt

from randovania.gui.lib import signal_handling

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceInfo


class _ResourceItemDelegate(QtWidgets.QStyledItemDelegate):
    """Edits the resource column with a combo box. The resource is stored in the item's UserRole."""

    def __init__(self, view: ResourceGainListView) -> None:
        super().__init__(view)
        self.view = view

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        combo = QtWidgets.QComboBox(parent)
        for it in self.view.resources:
            combo.addItem(it.long_name, it)
        return combo

    def setEditorData(
        self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex
    ) -> None:
        assert isinstance(editor, QtWidgets.QComboBox)
        signal_handling.set_combo_with_value(editor, index.data(Qt.ItemDataRole.UserRole))

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        assert isinstance(editor, QtWidgets.QComboBox)
        model.setData(index, editor.currentData(), Qt.ItemDataRole.UserRole)
        model.setData(index, editor.currentText(), Qt.ItemDataRole.DisplayRole)


class _AmountItemDelegate(QtWidgets.QStyledItemDelegate):
    """Edits the amount column with a spin box that only allows positive amounts."""

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        spin = QtWidgets.QSpinBox(parent)
        spin.setMinimum(1)
        spin.setMaximum(9999)
        return spin

    def setEditorData(
        self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex
    ) -> None:
        assert isinstance(editor, QtWidgets.QSpinBox)
        editor.setValue(index.data(Qt.ItemDataRole.EditRole))

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        assert isinstance(editor, QtWidgets.QSpinBox)
        editor.interpretText()
        model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)


class ResourceGainListView(QtWidgets.QGroupBox):
    """
    For editing a list of (resource, amount) pairs, such as a node's `grants_on_collect`.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.resources: list[ResourceInfo] = []

        self.list_layout = QtWidgets.QVBoxLayout(self)
        self.list_layout.setContentsMargins(2, 2, 2, 2)

        self.table = QtWidgets.QTableWidget(0, 2, self)
        self.table.setObjectName("table")
        self.table.setHorizontalHeaderLabels(["Resource", "Amount"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setItemDelegateForColumn(0, _ResourceItemDelegate(self))
        self.table.setItemDelegateForColumn(1, _AmountItemDelegate(self))
        self.list_layout.addWidget(self.table)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add", self)
        self.add_button.clicked.connect(self._on_add)
        self.button_layout.addWidget(self.add_button)

        self.remove_selected_button = QtWidgets.QPushButton("Remove Selected", self)
        self.remove_selected_button.clicked.connect(self._on_remove_selected)
        self.button_layout.addWidget(self.remove_selected_button)
        self.list_layout.addLayout(self.button_layout)

    def create_model(self, resources: Iterable[ResourceInfo]) -> None:
        """Defines which resources can be picked. Must be called before filling the view."""
        self.resources = sorted(resources, key=lambda it: it.long_name)
        self.setEnabled(bool(self.resources))

    def _add_row(self, resource: ResourceInfo, amount: int) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        resource_item = QtWidgets.QTableWidgetItem(resource.long_name)
        resource_item.setData(Qt.ItemDataRole.UserRole, resource)
        self.table.setItem(row, 0, resource_item)

        amount_item = QtWidgets.QTableWidgetItem()
        amount_item.setData(Qt.ItemDataRole.EditRole, amount)
        self.table.setItem(row, 1, amount_item)

    def _on_add(self) -> None:
        if self.resources:
            self._add_row(self.resources[0], 1)

    def _on_remove_selected(self) -> None:
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)

    @property
    def items(self) -> ResourceGainTuple:
        result = []
        for row in range(self.table.rowCount()):
            resource_item = self.table.item(row, 0)
            amount_item = self.table.item(row, 1)
            assert resource_item is not None
            assert amount_item is not None
            result.append(
                (resource_item.data(Qt.ItemDataRole.UserRole), amount_item.data(Qt.ItemDataRole.EditRole)),
            )
        return tuple(result)

    @items.setter
    def items(self, value: ResourceGainTuple) -> None:
        self.table.setRowCount(0)
        for resource, amount in value:
            self._add_row(resource, amount)
