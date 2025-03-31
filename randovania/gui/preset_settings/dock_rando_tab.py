from __future__ import annotations

import dataclasses
import sys
from collections import defaultdict
from typing import TYPE_CHECKING

import natsort
from PySide6 import QtWidgets

from randovania.gui.generated.preset_dock_rando_ui import Ui_PresetDockRando
from randovania.gui.lib import signal_handling
from randovania.gui.lib.foldable import Foldable
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.dock_rando_configuration import DockRandoMode

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from randovania.game_description.db.dock import DockRandoParams, DockType, DockWeakness
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetDockRando(PresetTab, Ui_PresetDockRando):
    type_checks: dict[DockType, dict[DockWeakness, dict[str, QtWidgets.QCheckBox]]]

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # Mode
        for mode in DockRandoMode:
            self.mode_combo.addItem(mode.long_name, mode)

        signal_handling.on_combo(self.mode_combo, self._on_mode_changed)
        signal_handling.on_checked(self.two_sided_door_search_check, self._persist_two_sided_door_lock_search)

        # Types
        self.type_checks = {}
        for dock_type, type_params in game_description.dock_weakness_database.dock_rando_params.items():
            self._add_dock_type(dock_type, type_params)

    @classmethod
    def tab_title(cls) -> str:
        return "Door Locks"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    @property
    def experimental_settings(self) -> Iterable[QtWidgets.QWidget]:
        yield self.two_sided_door_search_line
        yield self.two_sided_door_search_label
        yield self.two_sided_door_search_check

    def on_preset_changed(self, preset: Preset):
        dock_rando = preset.configuration.dock_rando
        signal_handling.set_combo_with_value(self.mode_combo, dock_rando.mode)
        self.mode_description.setText(dock_rando.mode.description)

        self.two_sided_door_search_check.setChecked(preset.configuration.two_sided_door_lock_search)
        self.multiworld_label.setVisible(len(dock_rando.settings_incompatible_with_multiworld()) > 0)
        self.line.setVisible(self.multiworld_label.isVisible())
        self.dock_types_group.setVisible(dock_rando.mode != DockRandoMode.VANILLA)

        for dock_type, weakness_checks in self.type_checks.items():
            rando_params = self.game_description.dock_weakness_database.dock_rando_params[dock_type]
            unlocked_check = weakness_checks[rando_params.unlocked]["can_change_from"]
            unlocked_check.setEnabled(dock_rando.mode != DockRandoMode.WEAKNESSES)
            unlocked_check_to = weakness_checks[rando_params.unlocked]["can_change_to"]
            unlocked_check_to.setEnabled(dock_rando.mode == DockRandoMode.WEAKNESSES)
            if dock_rando.mode == DockRandoMode.WEAKNESSES:
                unlocked_check.setChecked(False)
            else:
                unlocked_check_to.setChecked(True)

            state = dock_rando.types_state[dock_type]
            for weakness, checks in weakness_checks.items():
                if "can_change_from" in checks:
                    checks["can_change_from"].setChecked(weakness in state.can_change_from)
                if "can_change_to" in checks:
                    checks["can_change_to"].setChecked(weakness in state.can_change_to)

    def _add_dock_type(self, dock_type: DockType, type_params: DockRandoParams):
        self.type_checks[dock_type] = defaultdict(dict)

        type_box = Foldable(self.dock_types_group, dock_type.long_name)
        type_box.setObjectName(f"type_box {dock_type.short_name}")
        type_layout = QtWidgets.QHBoxLayout()
        type_layout.setObjectName(f"type_layout {dock_type.short_name}")
        type_box.set_content_layout(type_layout)

        self.dock_types_group.layout().addWidget(type_box)

        def add_group(name: str, desc: str, weaknesses: dict[DockWeakness, bool]):
            group = QtWidgets.QGroupBox()
            group.setObjectName(f"{name}_group {dock_type.short_name}")
            group.setTitle(desc)
            layout = QtWidgets.QVBoxLayout()
            group.setLayout(layout)

            for weakness, enabled in weaknesses.items():
                check = QtWidgets.QCheckBox()
                check.setObjectName(f"{name}_check {dock_type.short_name} {weakness.name}")
                check.setText(weakness.long_name)
                check.setEnabled(enabled)
                signal_handling.on_checked(check, self._persist_weakness_setting(name, dock_type, weakness))
                layout.addWidget(check)
                self.type_checks[dock_type][weakness][name] = check

            vertical_spacer = QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
            )
            layout.addSpacerItem(vertical_spacer)

            type_layout.addWidget(group)

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
        add_group("can_change_from", "Doors to Change", change_from)
        add_group("can_change_to", "Change Doors To", change_to)

    def _persist_weakness_setting(
        self,
        field: str,
        dock_type: DockType,
        dock_weakness: DockWeakness,
    ) -> Callable[[bool], None]:
        def _persist(value: bool):
            with self._editor as editor:
                state = editor.dock_rando_configuration.types_state[dock_type]
                can_change: set[DockWeakness] = getattr(state, field)
                if value:
                    can_change.add(dock_weakness)
                elif dock_weakness in can_change:
                    can_change.remove(dock_weakness)
                state = dataclasses.replace(state, **{field: can_change})
                editor.dock_rando_configuration.types_state[dock_type] = state

        return _persist

    def _on_mode_changed(self, value: DockRandoMode):
        with self._editor as editor:
            editor.dock_rando_configuration = dataclasses.replace(editor.dock_rando_configuration, mode=value)

    def _persist_two_sided_door_lock_search(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("two_sided_door_lock_search", value)
