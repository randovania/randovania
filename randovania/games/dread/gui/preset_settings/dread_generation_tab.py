from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.gui.dialog.trick_details_popup import ResourceDetailsPopup
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.generation_tab import PresetGeneration

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetDreadGeneration(PresetGeneration):
    highdanger_logic_check: QtWidgets.QCheckBox
    highdanger_logic_label: QtWidgets.QLabel

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        signal_handling.on_checked(self.highdanger_logic_check, self._on_highdanger_logic_check)
        self.highdanger_logic_label.linkActivated.connect(self._on_click_link_highdanger_logic_details)

    def setupUi(self, obj):
        super().setupUi(obj)

        self.highdanger_logic_check = QtWidgets.QCheckBox("Allow Highly Dangerous Logic", obj)
        self.highdanger_logic_label = QtWidgets.QLabel(obj)
        self.highdanger_logic_label.setText(
            """<html><head/><body>
            <p>Highly Dangerous Logic is a setting which enables dangerous actions that are not as obvious.</p>
            <p>Using these dangerous actions could render a seed unbeatable if the player were to save afterwards.</p>
            <p><a href=\"resource-details://misc/highdanger\"><span style=\" text-decoration: underline;
            color:#0000ff;\">Click here</span></a> to see which rooms are affected.</p></body></html>""",
        )

    @property
    def game_specific_widgets(self) -> Iterable[QtWidgets.QWidget]:
        yield self.highdanger_logic_check
        yield self.highdanger_logic_label

    def on_preset_changed(self, preset: Preset):
        assert isinstance(preset.configuration, DreadConfiguration)
        super().on_preset_changed(preset)
        self.highdanger_logic_check.setChecked(preset.configuration.allow_highly_dangerous_logic)

    def _on_highdanger_logic_check(self, state: bool):
        with self._editor as options:
            options.set_configuration_field(
                "allow_highly_dangerous_logic",
                state,
            )

    def _on_click_link_highdanger_logic_details(self, link: str):
        self._exec_trick_details(
            ResourceDetailsPopup(
                self,
                self._window_manager,
                self.game_description,
                self.game_description.resource_database.get_by_type_and_index(ResourceType.MISC, "HighDanger"),
            )
        )

    def _exec_trick_details(self, popup: ResourceDetailsPopup):
        self._trick_details_popup = popup
        self._trick_details_popup.setWindowModality(QtCore.Qt.WindowModal)
        self._trick_details_popup.open()
