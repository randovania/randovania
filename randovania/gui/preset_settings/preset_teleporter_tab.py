from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from randovania.games.common import elevators
from randovania.gui.lib import signal_handling
from randovania.gui.lib.node_list_helper import NodeListHelper
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.lib.teleporters import (
    TeleporterList,
    TeleporterShuffleMode,
    TeleporterTargetList,
)

if TYPE_CHECKING:
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor


class PresetTeleporterTab(PresetTab, NodeListHelper):
    _teleporters_source_for_location: dict[NodeIdentifier, QtWidgets.QCheckBox]
    _teleporters_target_for_region: dict[str, QtWidgets.QCheckBox]
    _teleporters_target_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox]
    _teleporters_target_for_node: dict[NodeIdentifier, QtWidgets.QCheckBox]
    teleporter_mode_to_description: dict[TeleporterShuffleMode, str] = {}
    teleporters_layout: QtWidgets.QVBoxLayout
    teleporters_combo: ScrollProtectedComboBox
    teleporters_description_label: QtWidgets.QLabel
    teleporters_source_group: QtWidgets.QGroupBox
    teleporters_target_group: QtWidgets.QGroupBox
    teleporters_target_layout: QtWidgets.QGridLayout

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setup_ui()

        self.teleporters_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.teleporter_types = game_description.dock_weakness_database.all_teleporter_dock_types

        for value in self.teleporter_mode_to_description:
            self.teleporters_combo.addItem(value.long_name, value)

        self.teleporters_combo.currentIndexChanged.connect(self._update_teleporter_mode)

        # Teleporters Source
        self._create_source_teleporters()

        # Teleporter Target
        result = self.create_node_list_selection(
            self.teleporters_target_group,
            self.teleporters_target_layout,
            TeleporterTargetList.nodes_list(self.game_enum),
            self._on_teleporter_target_check_changed,
        )
        (
            self._teleporters_target_for_region,
            self._teleporters_target_for_area,
            self._teleporters_target_for_node,
        ) = result

    def setup_ui(self):
        raise NotImplementedError

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    @property
    def game_enum(self):
        return self.game_description.game

    def _update_teleporter_mode(self):
        with self._editor as editor:
            editor.layout_configuration_teleporters = dataclasses.replace(
                editor.layout_configuration_teleporters,
                mode=self.teleporters_combo.currentData(),
            )

    def _on_teleporter_source_check_changed(self, checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_teleporters
            editor.layout_configuration_teleporters = dataclasses.replace(
                config,
                excluded_teleporters=TeleporterList.with_elements(
                    [
                        location
                        for location, check in self._teleporters_source_for_location.items()
                        if not check.isChecked()
                    ],
                    self.game_enum,
                ),
            )

    def _on_teleporter_target_check_changed(self, areas: list[NodeIdentifier], checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_teleporters
            editor.layout_configuration_teleporters = dataclasses.replace(
                config,
                excluded_targets=config.excluded_targets.ensure_has_locations(areas, not checked),
            )

    def _create_check_for_source_teleporters(self, location: NodeIdentifier) -> QtWidgets.QCheckBox:
        name = elevators.get_elevator_or_area_name(
            self.game_description, self.game_description.region_list, location, True
        )

        check = QtWidgets.QCheckBox(self.teleporters_source_group)
        check.setText(name)
        check.area_location = location
        signal_handling.on_checked(check, self._on_teleporter_source_check_changed)
        return check

    def _create_source_teleporters(self):
        raise NotImplementedError
