from __future__ import annotations

import dataclasses
import typing

from PySide6 import QtCore
from PySide6.QtCore import Qt

if typing.TYPE_CHECKING:
    from types import EllipsisType

    from _typeshed import DataclassInstance


def _unmodified_to_qt[T](obj: T) -> T:
    return obj


def _unmodified_from_qt[T](obj: T) -> tuple[bool, T]:
    return (True, obj)


@dataclasses.dataclass(frozen=True)
class FieldDefinition[QtT, PyT]:
    """
    Defines an interface between a Dataclass field and a table column.
    """

    display_name: str
    field_name: str
    _: dataclasses.KW_ONLY
    to_qt: typing.Callable[[PyT], QtT] = _unmodified_to_qt  # type: ignore[assignment]
    from_qt: typing.Callable[[QtT], tuple[bool, PyT | None]] = _unmodified_from_qt  # type: ignore[assignment]


def BoolFieldDefinition(display_name: str, field_name: str) -> FieldDefinition[str, bool]:
    def bool_to_qt(value: bool) -> str:
        return "True" if value else "False"

    def bool_from_qt(value: str) -> tuple[bool, bool | None]:
        if value.lower() == "true":
            return (True, True)
        if value.lower() == "false":
            return (True, False)
        return (False, None)

    return FieldDefinition[str, bool](
        display_name=display_name,
        field_name=field_name,
        to_qt=bool_to_qt,
        from_qt=bool_from_qt,
    )


class EditableTableModel[T: DataclassInstance](QtCore.QAbstractTableModel):
    """
    Generic base class for using a QTableView to edit a Dataclass.
    """

    def __init__(self):
        super().__init__()
        self.allow_edits = True

    def _all_columns(self) -> list[FieldDefinition]:
        """Return a list of FieldDefinitions describing each field in the items"""
        raise NotImplementedError

    def _get_items(self) -> list[T] | dict[typing.Any, T]:
        """All items controlled by this model. Automatically handles both list and dict"""
        raise NotImplementedError

    def _iterate_items(self) -> typing.Iterator[T]:
        """Iterate items, regardless of list vs dict"""
        items = self._get_items()
        if isinstance(items, list):
            yield from items
        else:
            yield from items.values()

    def _create_item(self, identifier: str) -> T:
        """Create a new valid item using the provided identifier"""
        raise NotImplementedError

    def _get_item_identifier(self, item: T) -> str:
        """Get a unique identifier for the item, to prevent duplicates"""
        raise NotImplementedError

    def set_allow_edits(self, value: bool) -> None:
        """Setter for `allow_edits`"""
        self.beginResetModel()
        self.allow_edits = value
        self.endResetModel()

    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation != Qt.Orientation.Horizontal:
            return section

        return self._all_columns()[section].display_name

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | EllipsisType = ...) -> int:
        result = len(self._get_items())
        if self.allow_edits:
            result += 1
        return result

    def columnCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | EllipsisType = ...) -> int:
        return len(self._all_columns())

    def _get_item(self, row: int) -> T:
        """Return the item on the given row."""
        all_items = self._get_items()
        if isinstance(all_items, list):
            return all_items[row]
        return all_items[list(all_items.keys())[row]]

    def _set_item(self, row: int, item: T) -> None:
        """Set the given row to the given item."""
        all_items = self._get_items()
        if isinstance(all_items, list):
            all_items[row] = item
        else:
            all_items[list(all_items.keys())[row]] = item

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            return None

        if index.row() < len(self._get_items()):
            item = self._get_item(index.row())
            field = self._all_columns()[index.column()]
            return field.to_qt(getattr(item, field.field_name))

        elif role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return "New..."
        else:
            return ""

    def setData(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        value: typing.Any,
        role: int | EllipsisType = ...,
    ) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            all_items = self._get_items()
            if index.row() < len(all_items):
                item = self._get_item(index.row())
                field = self._all_columns()[index.column()]
                valid, new_value = field.from_qt(value)
                if valid:
                    self._set_item(
                        index.row(),
                        dataclasses.replace(
                            item,
                            **{field.field_name: new_value},
                        ),
                    )
                    self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                    return True
            else:
                if value:
                    all_items = set(self._iterate_items())
                    if any(self._get_item_identifier(item) == value for item in all_items):
                        return False
                    return self.append_item(self._create_item(value))
        return False

    def _append_item_to_database(self, item: T) -> None:
        """Appends the given item to the model's underlying database"""
        all_items = self._get_items()
        if isinstance(all_items, list):
            all_items.append(item)
        else:
            id = self._get_item_identifier(item)
            assert id not in all_items
            all_items[id] = item

    def append_item(self, item: T) -> bool:
        """Appends the item to the database and safely adds rows while doing so"""
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row + 1, row + 1)
        self._append_item_to_database(item)
        self.endInsertRows()
        return True

    def flags(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> QtCore.Qt.ItemFlag:
        result = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if self.allow_edits:
            if index.row() == len(self._get_items()):
                if index.column() == 0:
                    result |= Qt.ItemFlag.ItemIsEditable
            else:
                if index.column() > 0:
                    result |= Qt.ItemFlag.ItemIsEditable
        return result
