import typing
from types import EllipsisType
from typing import override

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from randovania.gui.generated.async_race_admin_dialog_ui import Ui_AsyncRaceAdminDialog
from randovania.gui.lib.editable_table_model import (
    BoolFieldDefinition,
    DateFieldDefinition,
    EditableTableModel,
    FieldDefinition,
)
from randovania.network_common.async_race_room import AsyncRaceEntryData, AsyncRaceRoomAdminData


class AsyncRaceEntryDataDatabaseModel(EditableTableModel[AsyncRaceEntryData]):
    """Model for editing a AsyncRaceEntryData database using a QTableView."""

    def __init__(self, db: list[AsyncRaceEntryData]):
        super().__init__()
        self.db = db

    @override
    def _all_columns(self) -> list[FieldDefinition]:
        return [
            FieldDefinition("User", "user", to_qt=lambda v: v.name, from_qt=None),
            DateFieldDefinition("Join Date", "join_date", read_only=True),
            DateFieldDefinition("Start Date", "start_date", optional=True),
            DateFieldDefinition("Finish Date", "finish_date", optional=True),
            BoolFieldDefinition("Forfeited?", "forfeit"),
            FieldDefinition("Pauses?", "pauses", to_qt=lambda v: len(v), from_qt=None),
            FieldDefinition("Submission Notes", "submission_notes"),
            FieldDefinition("Proof URL", "proof_url"),
        ]

    @override
    def _get_items(self) -> list[AsyncRaceEntryData]:
        return self.db

    def setData(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        value: typing.Any,
        role: int | EllipsisType = ...,
    ) -> bool:
        result = super().setData(index, value, role)
        if result:
            self.dataChanged.emit(self.index(index.row(), 0), self.index(index.row(), self.columnCount()))
        return result

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int | EllipsisType = ...
    ) -> typing.Any:
        if role == Qt.ItemDataRole.DecorationRole:
            if index.row() < len(self._get_items()):
                item = self.db[index.row()]
                match index.column():
                    case 2:  # Start Date
                        if item.start_date is not None and item.start_date <= item.join_date:
                            return QtGui.QColorConstants.Red
                    case 3:  # Finish
                        if item.finish_date is not None and (
                            item.start_date is None or item.finish_date <= item.start_date
                        ):
                            return QtGui.QColorConstants.Red
                return None
            return QtGui.QColorConstants.Red
        return super().data(index, role)


class AsyncRaceAdminDialog(QtWidgets.QDialog):
    """A dialog for viewing and modifying an AsyncRaceRoomAdminData."""

    ui: Ui_AsyncRaceAdminDialog

    def __init__(self, parent: QtWidgets.QWidget, admin_data: AsyncRaceRoomAdminData):
        super().__init__(parent)
        self.ui = Ui_AsyncRaceAdminDialog()
        self.ui.setupUi(self)

        self.model = AsyncRaceEntryDataDatabaseModel(list(admin_data.users))
        self.ui.table_view.setModel(self.model)
        self.ui.table_view.resizeColumnsToContents()

        self.model.dataChanged.connect(self.validate)
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.reject)

    def admin_data(self) -> AsyncRaceRoomAdminData:
        """Creates a new AsyncRaceRoomAdminData with potentially modified data by the user."""
        return AsyncRaceRoomAdminData(
            users=list(self.model.db),
        )

    def validate(self, top_left: QtCore.QModelIndex, bottom_right: QtCore.QModelIndex, roles: list[int]) -> None:
        self.ui.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setEnabled(
            all(entry.is_valid() for entry in self.model.db)
        )
