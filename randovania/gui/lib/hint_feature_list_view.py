from typing import override

from PySide6 import QtWidgets

from randovania.game_description.hint_features import HintFeature
from randovania.gui.lib.editable_list_view import EditableListModel, EditableListView


class HintFeatureListModel(EditableListModel[HintFeature]):
    """
    Underlying model for editing lists of HintFeatures
    """

    def __init__(self, hint_features: dict[str, HintFeature]):
        super().__init__()
        self.db = hint_features

    @override
    def _display_item(self, row: int) -> str:
        return self.items[row].long_name

    @override
    def _new_item(self, identifier: str) -> HintFeature:
        return next(v for v in self.db.values() if v.long_name == identifier)


class HintFeatureListView(EditableListView):
    """
    For editing lists of HintFeatures
    """

    def __init__(self, parent: QtWidgets.QWidget | None, model: EditableListModel | None = None):
        super().__init__(parent, model)

        self.no_features_label = QtWidgets.QLabel("No features are defined for this game.")
        self.no_features_label.setObjectName("no_features_label")
        self.no_features_label.setVisible(False)
        self.list_layout.addWidget(self.no_features_label)

    def create_model(self, hint_feature_database: dict[str, HintFeature]) -> None:
        """Initializes the model from the hint feature database"""

        model = HintFeatureListModel(hint_feature_database)
        self.setModel(model)
        self.delegate.items = [ft.long_name for ft in hint_feature_database.values() if not ft.hidden]

        has_items = bool(self.delegate.items)
        self.list.setVisible(has_items)
        self.remove_selected_button.setVisible(has_items)
        self.no_features_label.setVisible(not has_items)
