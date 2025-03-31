from __future__ import annotations

import typing

from randovania.games.prime1.gui.generated.preset_prime_qol_ui import Ui_PresetPrimeQol
from randovania.games.prime1.layout.prime_configuration import LayoutCutsceneMode, PrimeConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_FIELDS = [
    "warp_to_start",
    "main_plaza_door",
    "blue_save_doors",
    "backwards_frigate",
    "backwards_labs",
    "backwards_upper_mines",
    "backwards_lower_mines",
    "phazon_elite_without_dynamo",
    "spring_ball",
    "remove_bars_great_tree_hall",
]


class PresetPrimeQol(PresetTab[PrimeConfiguration], Ui_PresetPrimeQol):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.description_label.setText(self.description_label.text().replace("color:#0000ff;", ""))

        # Signals
        self.cutscene_combo.setItemData(0, LayoutCutsceneMode.ORIGINAL)
        self.cutscene_combo.setItemData(1, LayoutCutsceneMode.SKIPPABLE)
        self.cutscene_combo.setItemData(2, LayoutCutsceneMode.SKIPPABLE_COMPETITIVE)
        self.cutscene_combo.setItemData(3, LayoutCutsceneMode.MAJOR)

        if editor._options.experimental_settings:
            self.cutscene_label.setText(
                """
<html>
<head/>
<body>
<p><span style=" font-weight:600;">Original</span>: No changes to the cutscenes are made.</p>
<p><span style=" font-weight:700;">Skippable</span>: Keeps all of the cutscenes in the game, but makes it so that
they can be skipped with the START button.</p>
<p><span style=" font-weight:700;">Competitive</span>: Removes some cutscenes from the game which hinder the flow of
competitive play. All others are skippable.</p>
<p><span style=" font-weight:600;">Major [Deprecated]</span>: Allows you to continue playing the game while
cutscenes happen. Inferior to the above options, but kept around because it's funny.</p>
</body>
</html>
            """
            )
        else:
            self.cutscene_combo.removeItem(3)

        signal_handling.on_combo(self.cutscene_combo, self._on_cutscene_changed)
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Quality of Life"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def _on_cutscene_changed(self, value: LayoutCutsceneMode) -> None:
        with self._editor as editor:
            try:
                editor.set_configuration_field("qol_cutscenes", value)
            except ValueError:
                editor.set_configuration_field("qol_cutscenes", LayoutCutsceneMode.COMPETITIVE)
                signal_handling.set_combo_with_value(self.cutscene_combo, LayoutCutsceneMode.COMPETITIVE)

    def on_preset_changed(self, preset: Preset[PrimeConfiguration]) -> None:
        config = preset.configuration
        for f in _FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
        signal_handling.set_combo_with_value(self.cutscene_combo, config.qol_cutscenes)
