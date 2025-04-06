from __future__ import annotations

import dataclasses
import datetime
from typing import TYPE_CHECKING

from PySide6 import QtCore
from PySide6.QtCore import Qt

from randovania.gui.lib.editable_table_model import (
    AppendableEditableTableModel,
    BoolFieldDefinition,
    DateFieldDefinition,
    EditableTableModel,
    FieldDefinition,
)

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


@dataclasses.dataclass(frozen=True)
class OurData:
    a: int
    b: bool
    c: datetime.datetime
    d: str
    e: str | None


_FIELD_DEFS = [
    FieldDefinition[int, int]("A", "a"),
    BoolFieldDefinition("B", "b"),
    DateFieldDefinition("C", "c"),
    FieldDefinition[str, str]("D", "d", from_qt=None),
    FieldDefinition[str, str]("E", "e", default_factory=lambda: "@@@"),
]


class EditableModelSample(EditableTableModel[OurData]):
    def __init__(self, entries: list[OurData]):
        super().__init__()
        self.entries = entries

    def _all_columns(self) -> list[FieldDefinition]:
        return _FIELD_DEFS

    def _get_items(self) -> list[OurData]:
        return self.entries


class AppendableModelSample(AppendableEditableTableModel[OurData]):
    def __init__(self, entries: list[OurData]):
        super().__init__()
        self.entries = entries

    def _all_columns(self) -> list[FieldDefinition]:
        return _FIELD_DEFS

    def _get_items(self) -> list[OurData]:
        return self.entries

    def _create_item(self, identifier: str) -> OurData:
        return OurData(
            a=0,
            b=False,
            c=datetime.datetime(year=2010, month=5, day=2, hour=10, minute=0, second=0),
            d=identifier,
            e=None,
        )

    def _get_item_identifier(self, item: OurData) -> str:
        return item.d


def test_editable_model(skip_qtbot: QtBot):
    d_py = datetime.datetime(year=2010, month=5, day=2, hour=10, minute=0, second=0)
    d_qt = QtCore.QDateTime(QtCore.QDate(2010, 5, 2), QtCore.QTime(10, 0))

    entries = [
        OurData(a=1, b=False, c=d_py, d="Bar", e=None),
        OurData(a=10, b=True, c=d_py, d="Bax", e="E"),
    ]

    model = EditableModelSample(list(entries))

    def get_data(row: int, role: Qt.ItemDataRole):
        return [model.data(model.index(row, i), role) for i in range(5)]

    assert model.rowCount() == len(entries)

    assert get_data(0, Qt.ItemDataRole.DisplayRole) == [1, "False", d_qt, "Bar", ""]
    assert get_data(0, Qt.ItemDataRole.CheckStateRole) == [None, None, None, None, Qt.CheckState.Unchecked]
    assert get_data(0, Qt.ItemDataRole.DecorationRole) == [None, None, None, None, None]

    assert get_data(1, Qt.ItemDataRole.DisplayRole) == [10, "True", d_qt, "Bax", "E"]
    assert get_data(1, Qt.ItemDataRole.CheckStateRole) == [None, None, None, None, Qt.CheckState.Checked]

    # Can't edit read only
    assert not model.setData(model.index(0, 3), "New Text", Qt.ItemDataRole.EditRole)
    assert model.entries[0] == entries[0]

    # Can't uncheck non-nullable models
    assert not model.setData(model.index(0, 1), 0, Qt.ItemDataRole.CheckStateRole)
    assert model.entries[0] == entries[0]

    # Toggle checkbox
    assert model.setData(model.index(0, 4), 2, Qt.ItemDataRole.CheckStateRole)
    assert model.setData(model.index(1, 4), 0, Qt.ItemDataRole.CheckStateRole)
    assert model.entries[0].e == "@@@"
    assert model.entries[1].e is None

    # Set Date
    assert model.setData(
        model.index(0, 2), QtCore.QDateTime(QtCore.QDate(2011, 5, 2), QtCore.QTime(11, 0)), Qt.ItemDataRole.EditRole
    )
    assert model.entries[0].c == datetime.datetime(year=2011, month=5, day=2, hour=11, minute=0, second=0).astimezone(
        datetime.UTC
    )

    # Set Bool
    assert not model.setData(model.index(0, 1), "foo", Qt.ItemDataRole.EditRole)
    assert model.entries[0].b is False
    assert model.setData(model.index(0, 1), "true", Qt.ItemDataRole.EditRole)
    assert model.entries[0].b is True

    base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    assert [model.flags(model.index(0, i)) for i in range(5)] == [
        base_flags | Qt.ItemFlag.ItemIsEditable,
        base_flags | Qt.ItemFlag.ItemIsEditable,
        base_flags | Qt.ItemFlag.ItemIsEditable,
        base_flags,
        base_flags | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsUserCheckable,
    ]

    model.set_allow_edits(False)
    assert [model.flags(model.index(0, i)) for i in range(5)] == [base_flags] * 5


def test_appendable_model(skip_qtbot: QtBot):
    d_py = datetime.datetime(year=2010, month=5, day=2, hour=10, minute=0, second=0)
    d_qt = QtCore.QDateTime(QtCore.QDate(2010, 5, 2), QtCore.QTime(10, 0))

    model = AppendableModelSample([])

    model.set_allow_edits(False)
    assert model.rowCount() == 0

    model.set_allow_edits(True)
    assert model.rowCount() == 1

    assert [model.data(model.index(0, i), Qt.ItemDataRole.DisplayRole) for i in range(5)] == [
        "New...",
        None,
        None,
        None,
        None,
    ]

    assert model.setData(model.index(0, 0), "new key", Qt.ItemDataRole.EditRole)
    assert model.entries == [
        OurData(a=0, b=False, c=d_py, d="new key", e=None),
    ]
    assert [model.data(model.index(0, i), Qt.ItemDataRole.DisplayRole) for i in range(5)] == [
        0,
        "False",
        d_qt,
        "new key",
        "",
    ]

    base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    assert [model.flags(model.index(1, i)) for i in range(5)] == [
        base_flags | Qt.ItemFlag.ItemIsEditable,
        base_flags,
        base_flags,
        base_flags,
        base_flags,
    ]
