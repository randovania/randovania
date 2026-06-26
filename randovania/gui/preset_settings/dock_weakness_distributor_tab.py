from __future__ import annotations

import dataclasses
import sys
from collections import defaultdict
from typing import TYPE_CHECKING, override

import natsort
from PySide6 import QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.gui.generated.preset_dock_rando_ui import Ui_PresetDockRando
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_weakness_distributor_configuration import DockWeaknessDistributorMode

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.db.dock import DockType, DockWeakness, WeaknessDistributorSettings
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetDockWeaknessDistributor[BaseConfigurationT: BaseConfiguration](
    PresetTab[BaseConfigurationT], Ui_PresetDockRando
):
    weakness_checks: dict[DockWeakness, dict[str, QtWidgets.QCheckBox]]

    def __init__(
        self, editor: PresetEditor[BaseConfigurationT], game_description: GameDescription, window_manager: WindowManager
    ):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)
        # FIXME: .ui file still has many references to Door

        self.changes_box.setVisible(False)

        # Mode
        for mode in DockWeaknessDistributorMode:
            self.mode_combo.addItem(mode.long_name, mode)

        signal_handling.on_combo(self.mode_combo, self._on_mode_changed)

        # Types
        self._add_dock_type(self.dock_type, self.dock_type.get_weakness_distributor())

    @classmethod
    def subclass_for_dock_type(cls, dock_type: DockType) -> type[PresetDockWeaknessDistributor]:
        """Creates a new subclass that is specific for the given DockType."""
        distributor_settings = dock_type.get_weakness_distributor()

        class SpecificPresetDockWeaknessDistributor(cls):  # type: ignore[valid-type, misc]
            @override
            @classmethod
            def tab_title(cls) -> str:
                return distributor_settings.ui_label

            @override
            @property
            def dock_type(self) -> DockType:
                return dock_type

        SpecificPresetDockWeaknessDistributor.__name__ = f"Preset{dock_type.short_name.title()}DockWeaknessDistributor"
        return SpecificPresetDockWeaknessDistributor

    @classmethod
    def subclass_for_compatible_dock_types(cls, game: RandovaniaGame) -> list[type[PresetDockWeaknessDistributor]]:
        """
        Creates a subclasses for every DockType in the given game that has Dock Weakness Distributor enabled.
        Can be an empty list.
        """
        return [
            cls.subclass_for_dock_type(dock_type)
            for dock_type in game.game_description.get_dock_type_database().dock_types
            if dock_type.weakness_distributor is not None
        ]

    @classmethod
    def tab_title(cls) -> str:
        raise NotImplementedError

    @property
    def dock_type(self) -> DockType:
        raise NotImplementedError

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset[BaseConfiguration]) -> None:
        weakness_distributor_config = preset.configuration.dock_weakness_distributor

        mode = weakness_distributor_config.get_mode_for(self.dock_type)
        signal_handling.set_combo_with_value(self.mode_combo, mode)
        self.mode_description.setText(mode.description)

        self.multiworld_label.setVisible(len(weakness_distributor_config.settings_incompatible_with_multiworld()) > 0)
        self.line.setVisible(self.multiworld_label.isVisible())
        self.dock_types_group.setVisible(mode != DockWeaknessDistributorMode.ORIGINAL)

        rando_params = self.dock_type.get_weakness_distributor()
        unlocked_check_from = self.weakness_checks[rando_params.unlocked]["can_change_from"]
        unlocked_check_from.setEnabled(mode != DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS)
        unlocked_check_to = self.weakness_checks[rando_params.unlocked]["can_change_to"]
        unlocked_check_to.setEnabled(mode == DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS)
        if mode == DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS:
            unlocked_check_from.setChecked(False)
        else:
            unlocked_check_to.setChecked(True)

        state = weakness_distributor_config.types_state[self.dock_type]
        for weakness, checks in self.weakness_checks.items():
            if "can_change_from" in checks:
                checks["can_change_from"].setChecked(weakness in state.can_change_from)
            if "can_change_to" in checks:
                checks["can_change_to"].setChecked(weakness in state.can_change_to)

    def _add_dock_type(self, dock_type: DockType, type_params: WeaknessDistributorSettings):
        self.weakness_checks = defaultdict(dict)

        def add_group(name: str, layout: QtWidgets.QVBoxLayout, weaknesses: dict[DockWeakness, bool]):
            for weakness, enabled in weaknesses.items():
                check = QtWidgets.QCheckBox()
                check.setObjectName(f"{name}_check {dock_type.short_name} {weakness.name}")
                check.setText(weakness.long_name)
                check.setEnabled(enabled)
                signal_handling.on_checked(check, self._persist_weakness_setting(name, weakness))
                layout.addWidget(check)
                self.weakness_checks[weakness][name] = check

            vertical_spacer = QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
            )
            layout.addSpacerItem(vertical_spacer)

        def names(weaknesses: set[DockWeakness]) -> set[str]:
            return {weak.long_name for weak in weaknesses}

        change_from_and_to = names(type_params.change_from) & names(type_params.change_to)

        def keyfunc(weakness: DockWeakness) -> tuple[bool, int, str]:
            if weakness == type_params.unlocked:
                # unlocked always first
                return False, 0, ""

            if weakness == type_params.locked:
                # locked always last
                return True, sys.maxsize, ""

            # shared weaknesses first, then by length, then by name
            return (weakness.long_name not in change_from_and_to), len(weakness.long_name), weakness.long_name

        change_from = dict.fromkeys(natsort.natsorted(type_params.change_from, key=keyfunc), True)
        change_to = {
            weakness: weakness != type_params.unlocked
            for weakness in natsort.natsorted(type_params.change_to, key=keyfunc)
        }
        add_group("can_change_from", self.can_change_from_layout, change_from)
        add_group("can_change_to", self.can_change_to_layout, change_to)

    def _persist_weakness_setting(
        self,
        field: str,
        dock_weakness: DockWeakness,
    ) -> Callable[[bool], None]:
        def _persist(value: bool):
            with self._editor as editor:
                state = editor.dock_weakness_distributor.types_state[self.dock_type]
                can_change: set[DockWeakness] = getattr(state, field)
                if value:
                    can_change.add(dock_weakness)
                elif dock_weakness in can_change:
                    can_change.remove(dock_weakness)
                state = dataclasses.replace(state, **{field: can_change})
                editor.dock_weakness_distributor = editor.dock_weakness_distributor.replace_state(self.dock_type, state)

        return _persist

    def _on_mode_changed(self, value: DockWeaknessDistributorMode):
        with self._editor as editor:
            state = editor.dock_weakness_distributor.types_state[self.dock_type]
            state = dataclasses.replace(state, mode=value)
            editor.dock_weakness_distributor = editor.dock_weakness_distributor.replace_state(self.dock_type, state)
