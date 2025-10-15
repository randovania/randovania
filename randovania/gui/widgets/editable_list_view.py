from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt

from randovania.gui.widgets.combo_box_item_delegate import ComboBoxItemDelegate


class EditableListModel[T](QtCore.QAbstractListModel):
    """Underlying Model for EditableListView. Should be subclassed."""

    items: list[T]

    def __init__(self):
        super().__init__()
        self.items = []

    def _display_item(self, row: int) -> str:
        """
        Return a human-readable string
        representing the item on this row.
        """

        raise NotImplementedError

    def _new_item(self, identifier: str) -> T:
        """
        Create and return a new item,
        with the provided identifier.
        """

        raise NotImplementedError

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.items) + 1

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> str | None:
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            return None

        if index.row() < len(self.items):
            return self._display_item(index.row())

        elif role == Qt.ItemDataRole.DisplayRole:
            return "New..."

        return ""

    def removeRows(self, row: int, count: int, parent: QtCore.QModelIndex = ...) -> bool:
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.items[row : row + count]
        self.endRemoveRows()
        return True

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def setData(self, index: QtCore.QModelIndex, value: str, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            new_item = self._new_item(value)
            if index.row() < len(self.items):
                self.items[index.row()] = new_item
                self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.DisplayRole])
            else:
                row = self.rowCount()
                self.beginInsertRows(QtCore.QModelIndex(), row + 1, row + 1)
                self.items.append(new_item)
                self.endInsertRows()
            return True
        return False


class EditableListView(QtWidgets.QGroupBox):
    """
    Generic base class for adding and removing elements from a list
    in the GUI, such as dock weaknesses or hint features.
    """

    def __init__(self, parent: QtWidgets.QWidget | None, model: EditableListModel | None = None):
        super().__init__(parent)

        self.model = model
        self.delegate = ComboBoxItemDelegate()

        self.list_layout = QtWidgets.QVBoxLayout(self)
        self.list_layout.setSpacing(6)
        self.list_layout.setContentsMargins(11, 11, 11, 11)
        self.list_layout.setObjectName("dock_incompatible_layout")
        self.list_layout.setContentsMargins(2, 2, 2, 2)

        self.list = QtWidgets.QListView(self)
        self.list.setObjectName("list")
        self.list.setItemDelegate(self.delegate)
        self.list.setModel(self.model)

        self.list_layout.addWidget(self.list)

        self.remove_selected_button = QtWidgets.QPushButton(self)
        self.remove_selected_button.setText("Remove Selected")
        self.remove_selected_button.clicked.connect(self._on_remove_selected_button_pressed)

        self.list_layout.addWidget(self.remove_selected_button)

    def setModel(self, model: EditableListModel) -> None:
        self.model = model
        self.list.setModel(self.model)

    def _on_remove_selected_button_pressed(self) -> None:
        indices = [selection.row() for selection in self.list.selectedIndexes()]
        if indices:
            assert len(indices) == 1
            self.model.removeRow(indices[0])
