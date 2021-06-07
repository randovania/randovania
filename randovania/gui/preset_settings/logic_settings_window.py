from typing import Optional, List

from PySide2.QtWidgets import QDialog

from randovania.game_description import default_database
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.echoes_beam_configuration_tab import PresetEchoesBeamConfiguration
from randovania.gui.preset_settings.echoes_goal_tab import PresetEchoesGoal
from randovania.gui.preset_settings.echoes_hints_tab import PresetEchoesHints
from randovania.gui.preset_settings.echoes_patches_tab import PresetEchoesPatches
from randovania.gui.preset_settings.echoes_translators_tab import PresetEchoesTranslators
from randovania.gui.preset_settings.elevators_tab import PresetElevators
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
from randovania.gui.preset_settings.logic_damage_tab import PresetLogicDamage
from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.gui.preset_settings.prime_goal_tab import PresetPrimeGoal
from randovania.gui.preset_settings.prime_patches_tab import PresetPrimePatches
from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea
from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


def _update_options_when_true(options: Options, field_name: str, new_value, checked: bool):
    if checked:
        with options:
            setattr(options, field_name, new_value)


def dark_world_flags(world: World):
    yield False
    if world.dark_name is not None:
        yield True


class LogicSettingsWindow(QDialog, Ui_LogicSettingsWindow):
    _extra_tabs: List[PresetTab]
    _editor: PresetEditor

    def __init__(self, window_manager: Optional[WindowManager], editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._editor = editor
        self._extra_tabs = []

        game_enum = editor.game
        game_description = default_database.game_description_for(game_enum)

        if game_enum == RandovaniaGame.PRIME1:
            self._extra_tabs.append(PresetTrickLevel(editor, game_description, window_manager))
            self._extra_tabs.append(PresetPatcherEnergy(editor, game_enum))
            self._extra_tabs.append(PresetElevators(editor, game_description))
            self._extra_tabs.append(PresetStartingArea(editor, game_description))
            self._extra_tabs.append(PresetLogicDamage(editor))
            self._extra_tabs.append(PresetPrimeGoal(editor))
            self._extra_tabs.append(PresetPrimePatches(editor))
            self._extra_tabs.append(PresetLocationPool(editor, game_description))
            self._extra_tabs.append(PresetItemPool(editor))

        elif game_enum == RandovaniaGame.PRIME2:
            self._extra_tabs.append(PresetTrickLevel(editor, game_description, window_manager))
            self._extra_tabs.append(PresetPatcherEnergy(editor, game_enum))
            self._extra_tabs.append(PresetElevators(editor, game_description))
            self._extra_tabs.append(PresetStartingArea(editor, game_description))
            self._extra_tabs.append(PresetLogicDamage(editor))
            self._extra_tabs.append(PresetEchoesGoal(editor))
            self._extra_tabs.append(PresetEchoesHints(editor))
            self._extra_tabs.append(PresetEchoesTranslators(editor))
            self._extra_tabs.append(PresetEchoesBeamConfiguration(editor))
            self._extra_tabs.append(PresetEchoesPatches(editor))
            self._extra_tabs.append(PresetLocationPool(editor, game_description))
            self._extra_tabs.append(PresetItemPool(editor))

        elif game_enum == RandovaniaGame.PRIME3:
            self._extra_tabs.append(PresetTrickLevel(editor, game_description, window_manager))
            self._extra_tabs.append(PresetPatcherEnergy(editor, game_enum))
            self._extra_tabs.append(PresetElevators(editor, game_description))
            self._extra_tabs.append(PresetStartingArea(editor, game_description))
            self._extra_tabs.append(PresetLogicDamage(editor))
            self._extra_tabs.append(PresetLocationPool(editor, game_description))
            self._extra_tabs.append(PresetItemPool(editor))

        else:
            raise ValueError(f"Unknown game: {game_enum}")

        for extra_tab in self._extra_tabs:
            if extra_tab.uses_patches_tab:
                tab = self.patches_tab_widget
            else:
                tab = self.logic_tab_widget
            tab.addTab(extra_tab, extra_tab.tab_title)

        self.name_edit.textEdited.connect(self._edit_name)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    # Options
    def on_preset_changed(self, preset: Preset):
        common_qt_lib.set_edit_if_different(self.name_edit, preset.name)
        for extra_tab in self._extra_tabs:
            extra_tab.on_preset_changed(preset)

    def _edit_name(self, value: str):
        with self._editor as editor:
            editor.name = value
