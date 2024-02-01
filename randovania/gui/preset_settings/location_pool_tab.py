from __future__ import annotations

import collections
import dataclasses
import re
from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QSizePolicy, QSpacerItem

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.location_category import LocationCategory
from randovania.gui.generated.preset_location_pool_ui import Ui_PresetLocationPool
from randovania.gui.lib.foldable import Foldable
from randovania.gui.lib.node_list_helper import NodeListHelper, dark_name_flags
from randovania.gui.preset_settings.location_pool_row_widget import LocationPoolRowWidget
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.available_locations import RandomizationMode

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.games.game import RandovaniaGame
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetLocationPool(PresetTab, Ui_PresetLocationPool, NodeListHelper):
    _starting_location_for_region: dict[str, QtWidgets.QCheckBox]
    _starting_location_for_area: dict[int, QtWidgets.QCheckBox]
    _row_widget_for_node: dict[PickupNode, LocationPoolRowWidget]
    _during_batch_update: bool
    _major_minor: bool

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)
        self._during_batch_update = False

        self._row_widget_for_node = {}

        region_list = self.game_description.region_list

        nodes_by_region: dict[str, list[PickupNode]] = collections.defaultdict(list)
        node_names = {}
        # Needs to start with "Pickup (", then needs to
        # contain at least one character in there, and needs to end with ")"
        pickup_match = re.compile(r"^Pickup \((.+)\)$")

        for region in region_list.regions:
            for use_dark_name in dark_name_flags(region):
                for area in region.areas:
                    if area.in_dark_aether != use_dark_name:
                        continue
                    for node in area.nodes:
                        if isinstance(node, PickupNode):
                            nodes_by_region[region.correct_name(use_dark_name)].append(node)
                            match = pickup_match.match(node.name)
                            if match is not None:
                                node_name = match.group(1)
                            else:
                                node_name = node.name
                            node_names[node] = f"{region_list.nodes_to_area(node).name} ({node_name})"

        for region_name in sorted(nodes_by_region.keys()):
            spoiler = Foldable(None, region_name)
            vbox_layout = QtWidgets.QVBoxLayout()

            first_node = True
            for node in sorted(nodes_by_region[region_name], key=node_names.get):
                if not first_node:
                    separator_line = QFrame()
                    separator_line.setFrameShape(QFrame.HLine)
                    separator_line.setFrameShadow(QFrame.Sunken)
                    transparent = QGraphicsOpacityEffect(separator_line)
                    transparent.setOpacity(0.33)
                    separator_line.setGraphicsEffect(transparent)
                    vbox_layout.addWidget(separator_line)
                else:
                    first_node = False

                row_widget = LocationPoolRowWidget(node, node_names[node])
                vbox_layout.addWidget(row_widget)
                row_widget.changed.connect(self._on_location_changed)
                self._row_widget_for_node[node] = row_widget

            spoiler.set_content_layout(vbox_layout)
            self.locations_scroll_area_layout.addWidget(spoiler)

        self.locations_scroll_area_layout.addItem(QSpacerItem(5, 5, QSizePolicy.Expanding, QSizePolicy.Expanding))

    @classmethod
    def tab_title(cls) -> str:
        return "Location Pool"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    @property
    def game_enum(self) -> RandovaniaGame:
        return self.game_description.game

    def on_preset_changed(self, preset: Preset):
        available_locations = preset.configuration.available_locations

        self._during_batch_update = True

        self._major_minor = available_locations.randomization_mode == RandomizationMode.MAJOR_MINOR_SPLIT
        self._on_update_randomization_mode()

        for node, row_widget in self._row_widget_for_node.items():
            can_have_progression = node.pickup_index not in available_locations.excluded_indices
            row_widget.set_can_have_progression(can_have_progression)

        self._during_batch_update = False

    def _on_update_randomization_mode(self):
        with self._editor as editor:
            mode = RandomizationMode.MAJOR_MINOR_SPLIT if self._major_minor else RandomizationMode.FULL
            editor.available_locations = dataclasses.replace(editor.available_locations, randomization_mode=mode)
            for node, row_widget in self._row_widget_for_node.items():
                if mode == RandomizationMode.MAJOR_MINOR_SPLIT and node.location_category == LocationCategory.MINOR:
                    row_widget.set_can_have_progression(False)
                    row_widget.setEnabled(False)
                else:
                    row_widget.setEnabled(True)
                    row_widget.set_can_have_progression(True)

    def _on_location_changed(self, node: PickupNode):
        if self._during_batch_update:
            return
        with self._editor as editor:
            editor.available_locations = editor.available_locations.ensure_index(
                node.pickup_index, not self._row_widget_for_node[node].can_have_progression
            )
