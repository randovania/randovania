from typing import override

from randovania.game_description.hint_features import HintFeature
from randovania.gui.lib.editable_list_view import EditableListModel


class HintFeatureListModel(EditableListModel[HintFeature]):
    """
    For editing lists of HintFeatures
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
