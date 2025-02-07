from typing import override

from PySide6 import QtCore, QtWidgets

from randovania.game_description.hint_features import HintDetails, HintFeature
from randovania.gui.generated.hint_feature_database_editor_ui import Ui_HintFeatureDatabaseEditor
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.editable_table_model import BoolFieldDefinition, EditableTableModel, FieldDefinition


class HintFeatureDatabaseModel(EditableTableModel[HintFeature]):
    """Model for editing a HintFeature database using a QTableView."""

    def __init__(self, db: dict[str, HintFeature]):
        super().__init__()
        self.db = db

    @override
    def _all_columns(self) -> list[FieldDefinition]:
        return [
            FieldDefinition[str, str]("Short Name", "name"),
            FieldDefinition[str, str]("Long Name", "long_name"),
            FieldDefinition[str, HintDetails](
                "Hint Details",
                "hint_details",
                to_qt=lambda v: v.description,
                from_qt=lambda v: (True, HintDetails("", v)),
            ),
            BoolFieldDefinition("Hidden?", "hidden"),
            FieldDefinition[str, str]("Description", "description"),
        ]

    @override
    def _get_items(self) -> dict[str, HintFeature]:
        return self.db

    @override
    def _create_item(self, identifier: str) -> HintFeature:
        return HintFeature(identifier, identifier, HintDetails("", ""))

    @override
    def _get_item_identifier(self, item: HintFeature) -> str:
        return item.name

    @override
    def append_item(self, item: HintFeature) -> bool:
        assert item.name not in self.db
        return super().append_item(item)


class HintFeatureDatabaseEditor(QtWidgets.QDockWidget, Ui_HintFeatureDatabaseEditor):
    HintFeatureChanged = QtCore.Signal(object)

    def __init__(self, parent: QtWidgets.QWidget, db: dict[str, HintFeature]):
        super().__init__(parent)
        self.setupUi(self)
        set_default_window_icon(self)

        self.db = db

        self.feature_table.setModel(HintFeatureDatabaseModel(db))
        self.feature_table.model().dataChanged.connect(self._on_data_changed)

    def _on_data_changed(
        self,
        top_left: QtCore.QModelIndex,
        bottom_right: QtCore.QModelIndex,
        roles: None,
    ) -> None:
        first_row = top_left.row()
        last_row = bottom_right.row()
        if first_row == last_row:
            self.HintFeatureChanged.emit(self.db[list(self.db.keys())[first_row]])

    def set_allow_edits(self, value: bool) -> None:
        model = self.feature_table.model()
        assert isinstance(model, HintFeatureDatabaseModel)
        model.set_allow_edits(value)
