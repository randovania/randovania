import dataclasses
from collections import defaultdict
from typing import Callable

from PySide6 import QtWidgets

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.dock import DockRandoParams, DockType, DockWeakness
from randovania.gui.generated.preset_dock_rando_ui import Ui_PresetDockRando
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.gui.lib.foldable import Foldable
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.preset import Preset


class PresetDockRando(PresetTab, Ui_PresetDockRando):
    type_checks: dict[DockType, dict[DockWeakness, dict[str, QtWidgets.QCheckBox]]]

    def __init__(self, editor: PresetEditor, game_description: GameDescription) -> None:
        super().__init__(editor)
        self.setupUi(self)

        # Mode
        self.mode_combo.setItemData(0, DockRandoMode.VANILLA)
        self.mode_combo.setItemData(1, DockRandoMode.TWO_WAY)
        self.mode_combo.setItemData(2, DockRandoMode.ONE_WAY)
        signal_handling.on_combo(self.mode_combo, self._on_mode_changed)

        # Types
        self.type_checks = {}
        for dock_type, type_params in game_description.dock_weakness_database.dock_rando_params.items():
            if (
                    type_params.locked is None or type_params.unlocked is None
                    or not type_params.change_from or not type_params.change_to
            ):
                continue
            self._add_dock_type(dock_type, type_params)

    @classmethod
    def tab_title(cls) -> str:
        return "Door Locks"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        dock_rando = preset.configuration.dock_rando
        common_qt_lib.set_combo_with_value(self.mode_combo, dock_rando.mode)
        self.mode_description.setText(dock_rando.mode.description)

        for dock_type, weakness_checks in self.type_checks.items():
            state = dock_rando.types_state[dock_type]
            for weakness, checks in weakness_checks.items():
                if "can_change_from" in checks:
                    checks["can_change_from"].setChecked(weakness in state.can_change_from)
                if "can_change_to" in checks:
                    checks["can_change_to"].setChecked(weakness in state.can_change_to)

    def _add_dock_type(self, dock_type: DockType, type_params: DockRandoParams):
        self.type_checks[dock_type] = defaultdict(dict)

        type_box = Foldable(dock_type.long_name)
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
                signal_handling.on_checked(check, self._persist_weakness_setting(
                    name, dock_type, weakness
                ))
                layout.addWidget(check)
                self.type_checks[dock_type][weakness][name] = check

            type_layout.addWidget(group)

        def keyfunc(weakness: DockWeakness):
            if weakness == type_params.unlocked:
                return 0
            return len(weakness.long_name)

        change_from = {weakness: True for weakness in sorted(type_params.change_from, key=keyfunc)}
        change_to = {weakness: weakness != type_params.unlocked for weakness in
                     sorted(type_params.change_to, key=keyfunc)}
        add_group("can_change_from", "Doors to Change", change_from)
        add_group("can_change_to", "Change Doors To", change_to)

    def _persist_weakness_setting(self, field: str, dock_type: DockType, dock_weakness: DockWeakness) -> Callable[
        [bool], None]:
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
            editor.dock_rando_configuration = dataclasses.replace(
                editor.dock_rando_configuration,
                mode=value
            )
