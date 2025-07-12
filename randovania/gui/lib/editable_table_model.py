from __future__ import annotations

import dataclasses
import datetime
import typing
from typing import override

from PySide6 import QtCore
from PySide6.QtCore import QDateTime, Qt

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
    When default_factory is set, the field is optional.
    When from_qt is None, the field is read only.
    """

    display_name: str
    field_name: str
    _: dataclasses.KW_ONLY
    default_factory: typing.Callable[[], PyT] | None = None
    to_qt: typing.Callable[[PyT], QtT] = _unmodified_to_qt  # type: ignore[assignment]
    from_qt: typing.Callable[[QtT], tuple[bool, PyT | None]] | None = _unmodified_from_qt  # type: ignore[assignment]


def BoolFieldDefinition(display_name: str, field_name: str, *, read_only: bool = False) -> FieldDefinition[str, bool]:
    def bool_to_qt(value: bool) -> str:
        return "True" if value else "False"

    def bool_from_qt(value: str) -> tuple[bool, bool | None]:
        if value.lower() == "true":
            return True, True
        if value.lower() == "false":
            return True, False
        return False, None

    return FieldDefinition[str, bool](
        display_name=display_name,
        field_name=field_name,
        to_qt=bool_to_qt,
        from_qt=None if read_only else bool_from_qt,
    )


def DateFieldDefinition(
    display_name: str, field_name: str, *, read_only: bool = False, optional: bool = False
) -> FieldDefinition[QDateTime, datetime.datetime]:
    """Creates a FieldDefinition for editing a datetime.datetime"""

    default_factory = None

    if optional:

        def default_factory() -> datetime.datetime:
            return datetime.datetime.now(datetime.UTC)

    def date_to_qt(value: datetime.datetime) -> QDateTime:
        return QtCore.QDateTime.fromSecsSinceEpoch(int(value.timestamp()))

    def date_from_qt(value: QDateTime) -> tuple[bool, datetime.datetime]:
        result = value.toPython()
        assert isinstance(result, datetime.datetime)
        return True, result.astimezone(datetime.UTC)

    return FieldDefinition[QDateTime, datetime.datetime](
        display_name=display_name,
        field_name=field_name,
        default_factory=default_factory,
        to_qt=date_to_qt,
        from_qt=None if read_only else date_from_qt,
    )


class DataclassTableModel[T: DataclassInstance](QtCore.QAbstractTableModel):
    """
    Generic base class for using a QTableView to view a Dataclass.
    """

    def __init__(self) -> None:
        super().__init__()
        self.allow_edits = False

    def _all_columns(self) -> list[FieldDefinition]:
        """Return a list of FieldDefinitions describing each field in the items"""
        raise NotImplementedError

    def _get_items(self) -> list[T] | dict[typing.Any, T]:
        """All items controlled by this model. Automatically handles both list and dict"""
        raise NotImplementedError

    @override
    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation != Qt.Orientation.Horizontal:
            return section

        return self._all_columns()[section].display_name

    @override
    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | EllipsisType = ...) -> int:
        return len(self._get_items())

    @override
    def columnCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | EllipsisType = ...) -> int:
        return len(self._all_columns())

    def _get_item(self, row: int) -> T:
        """Return the item on the given row."""
        all_items = self._get_items()
        if isinstance(all_items, list):
            return all_items[row]
        return all_items[list(all_items.keys())[row]]

    @override
    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.CheckStateRole}:
            return None

        if index.row() < len(self._get_items()):
            item = self._get_item(index.row())
            field = self._all_columns()[index.column()]

            value = getattr(item, field.field_name)
            if role == Qt.ItemDataRole.CheckStateRole:
                if field.default_factory is not None:
                    if value is not None:
                        return Qt.CheckState.Checked
                    else:
                        return Qt.CheckState.Unchecked
                return None

            if field.default_factory is not None and value is None:
                return ""
            return field.to_qt(value)

        else:
            return ""

    @override
    def setData(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        value: typing.Any,
        role: int | EllipsisType = ...,
    ) -> bool:
        return False

    @override
    def flags(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> QtCore.Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable


class EditableTableModel[T: DataclassInstance](DataclassTableModel[T]):
    """
    Generic base class for using a QTableView to edit a Dataclass.
    """

    def __init__(self) -> None:
        super().__init__()
        self.allow_edits = True

    def _iterate_items(self) -> typing.Iterator[T]:
        """Iterate items, regardless of list vs dict"""
        items = self._get_items()
        if isinstance(items, list):
            yield from items
        else:
            yield from items.values()

    def set_allow_edits(self, value: bool) -> None:
        """Setter for `allow_edits`"""
        self.beginResetModel()
        self.allow_edits = value
        self.endResetModel()

    def _set_item(self, row: int, item: T) -> None:
        """Set the given row to the given item."""
        all_items = self._get_items()
        if isinstance(all_items, list):
            all_items[row] = item
        else:
            all_items[list(all_items.keys())[row]] = item

    @override
    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.CheckStateRole}:
            return None

        if index.row() < len(self._get_items()):
            item = self._get_item(index.row())
            field = self._all_columns()[index.column()]

            value = getattr(item, field.field_name)
            if role == Qt.ItemDataRole.CheckStateRole:
                if field.default_factory is not None:
                    if value is not None:
                        return Qt.CheckState.Checked
                    else:
                        return Qt.CheckState.Unchecked
                return None

            if field.default_factory is not None and value is None:
                return ""
            return field.to_qt(value)

        else:
            return ""

    @override
    def setData(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        value: typing.Any,
        role: int | EllipsisType = ...,
    ) -> bool:
        if role in {Qt.ItemDataRole.EditRole, Qt.ItemDataRole.CheckStateRole}:
            all_items = self._get_items()
            if index.row() < len(all_items):
                item = self._get_item(index.row())
                field = self._all_columns()[index.column()]

                if field.from_qt is None:
                    return False

                if role == Qt.ItemDataRole.CheckStateRole:
                    if field.default_factory is None:
                        return False

                    if Qt.CheckState(value) == Qt.CheckState.Checked:
                        valid, new_value = True, field.default_factory()
                    else:
                        valid, new_value = True, None
                else:
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
        return False

    @override
    def flags(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> QtCore.Qt.ItemFlag:
        result = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if self.allow_edits:
            field = self._all_columns()[index.column()]
            if field.from_qt is not None:
                result |= Qt.ItemFlag.ItemIsEditable
            if field.default_factory is not None:
                result |= Qt.ItemFlag.ItemIsUserCheckable
        return result


class AppendableEditableTableModel[T: DataclassInstance](EditableTableModel[T]):
    """
    Extension of EditableTableModel, allowing for new entries to be added.
    """

    def _create_item(self, identifier: str) -> T:
        """Create a new valid item using the provided identifier"""
        raise NotImplementedError

    def _get_item_identifier(self, item: T) -> str:
        """Get a unique identifier for the item, to prevent duplicates"""
        raise NotImplementedError

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | EllipsisType = ...) -> int:
        result = super().rowCount(parent)
        if self.allow_edits:
            result += 1
        return result

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int | EllipsisType = ...
    ) -> typing.Any:
        if index.row() >= len(self._get_items()):
            if role == Qt.ItemDataRole.DisplayRole and index.column() == 0:
                return "New..."
            else:
                return None
        else:
            return super().data(index, role)

    def setData(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        value: typing.Any,
        role: int | EllipsisType = ...,
    ) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            all_items = self._get_items()
            if index.row() >= len(all_items) and value:
                all_items_set = set(self._iterate_items())
                if any(self._get_item_identifier(item) == value for item in all_items_set):
                    return False
                return self.append_item(self._create_item(value))
        return super().setData(index, value, role)

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
        if self.allow_edits and index.row() == len(self._get_items()):
            if index.column() == 0:
                return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
            else:
                return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return super().flags(index)
