from typing import override

from randovania.gui.lib.editable_table_model import DataclassTableModel, DateFieldDefinition, FieldDefinition
from randovania.network_common.audit import AuditEntry


class AuditEntryListDatabaseModel(DataclassTableModel[AuditEntry]):
    """Model for viewing a list of AuditEntry using a QTableView."""

    def __init__(self, db: list[AuditEntry]):
        super().__init__()
        self.db = db

    @override
    def _all_columns(self) -> list[FieldDefinition]:
        return [
            FieldDefinition("User", "user"),
            FieldDefinition("Message", "message"),
            DateFieldDefinition("Date", "time"),
        ]

    @override
    def _get_items(self) -> list[AuditEntry]:
        return self.db
