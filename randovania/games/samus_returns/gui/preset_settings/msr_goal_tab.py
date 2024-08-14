from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.samus_returns.gui.generated.preset_msr_goal_ui import Ui_PresetMSRGoal
from randovania.games.samus_returns.layout.msr_configuration import (
    FinalBossConfiguration,
    MSRArtifactConfig,
    MSRConfiguration,
)
from randovania.gui.lib.signal_handling import on_checked, set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetMSRGoal(PresetTab, Ui_PresetMSRGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.restrict_placement_radiobutton.toggled.connect(self._on_restrict_placement)
        self.free_placement_radiobutton.toggled.connect(self._on_free_placement)

        on_checked(self.prefer_metroids_check, self._on_prefer_metroids)
        on_checked(self.prefer_stronger_metroids_check, self._on_prefer_stronger_metroids)
        on_checked(self.prefer_bosses_check, self._on_prefer_bosses)

        self.required_slider.valueChanged.connect(self._on_required_slider_changed)
        self.placed_slider.valueChanged.connect(self._on_placed_slider_changed)
        self._update_slider_max()

        for i, final_boss in enumerate(FinalBossConfiguration):
            self.final_boss_combo.setItemData(i, final_boss)
        self.final_boss_combo.currentIndexChanged.connect(self._on_boss_combo_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def starts_new_header(cls) -> bool:
        return False

    def _update_slider_max(self) -> None:
        self.placed_slider.setMaximum(self.num_preferred_locations)
        self.placed_slider.setEnabled(self.num_preferred_locations > 0)

        self.required_slider.setMaximum(self.placed_slider.value())
        self.required_slider.setEnabled(self.placed_slider.value() > 0)

    def _edit_config(self, call: Callable[[MSRArtifactConfig], MSRArtifactConfig]) -> None:
        config = self._editor.configuration
        assert isinstance(config, MSRConfiguration)

        with self._editor as editor:
            editor.set_configuration_field("artifacts", call(config.artifacts))

    @property
    def num_preferred_locations(self) -> int:
        preferred = 0
        if self.free_placement_radiobutton.isChecked():
            preferred = 39
        else:
            if self.prefer_metroids_check.isChecked():
                preferred += 25
            if self.prefer_stronger_metroids_check.isChecked():
                preferred += 14
            if self.prefer_bosses_check.isChecked() and preferred < 36:
                preferred += 4
        return preferred

    def _on_restrict_placement(self, value: bool) -> None:
        if not value:
            return
        self.prefer_metroids_check.setEnabled(True)
        self.prefer_stronger_metroids_check.setEnabled(True)
        self.prefer_bosses_check.setEnabled(True)

        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, prefer_anywhere=False)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_free_placement(self, value: bool) -> None:
        if not value:
            return
        self.prefer_metroids_check.setEnabled(False)
        self.prefer_stronger_metroids_check.setEnabled(False)
        self.prefer_bosses_check.setEnabled(False)

        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, prefer_anywhere=True)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_prefer_metroids(self, value: bool) -> None:
        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, prefer_metroids=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_prefer_stronger_metroids(self, value: bool) -> None:
        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, prefer_stronger_metroids=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_prefer_bosses(self, value: bool) -> None:
        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, prefer_bosses=value)

        self._edit_config(edit)
        self._update_slider_max()

    def _on_required_slider_changed(self) -> None:
        self.required_slider_label.setText(f"{self.required_slider.value()} DNA Required")

        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, required_artifacts=self.required_slider.value())

        self._edit_config(edit)

    def _on_placed_slider_changed(self) -> None:
        self.placed_slider_label.setText(f"{self.placed_slider.value()} DNA in Pool")
        self.required_slider.setMaximum(self.placed_slider.value())
        self.required_slider.setEnabled(self.placed_slider.value() > 0)

        def edit(config: MSRArtifactConfig) -> MSRArtifactConfig:
            return dataclasses.replace(config, placed_artifacts=self.placed_slider.value())

        self._edit_config(edit)

    def _on_boss_combo_changed(self, new_index: int) -> None:
        with self._editor as editor:
            editor.set_configuration_field("final_boss", self.final_boss_combo.currentData())

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, MSRConfiguration)
        artifacts = preset.configuration.artifacts
        self.free_placement_radiobutton.setChecked(artifacts.prefer_anywhere)
        self.restrict_placement_radiobutton.setChecked(not artifacts.prefer_anywhere)
        self.prefer_metroids_check.setChecked(artifacts.prefer_metroids)
        self.prefer_stronger_metroids_check.setChecked(artifacts.prefer_stronger_metroids)
        self.prefer_bosses_check.setChecked(artifacts.prefer_bosses)
        self.placed_slider.setValue(artifacts.placed_artifacts)
        self.required_slider.setValue(artifacts.required_artifacts)

        final_boss = preset.configuration.final_boss
        if final_boss == FinalBossConfiguration.ARACHNUS:
            self.boss_info_label.setText("After defeating Arachnus, you must re-enter Dam Exterior to finish.")
        elif final_boss == FinalBossConfiguration.DIGGERNAUT:
            self.boss_info_label.setText(
                "The top Grapple blocks in Area 6 - Transport to Area 7 will be moved by default."
            )
        elif final_boss == FinalBossConfiguration.QUEEN:
            self.boss_info_label.setText(
                "To fight the Queen, you must also collect Ice Beam and defeat all 10 Larva Metroids.\n"
                "The wall behind the Queen will be removed by default."
            )
        elif final_boss == FinalBossConfiguration.RIDLEY:
            self.boss_info_label.setText("You must also collect the Baby Metroid.")
        else:
            self.boss_info_label.setText("This option will randomly choose one of the four bosses to fight.")

        set_combo_with_value(self.final_boss_combo, final_boss)
