import collections
import dataclasses
import functools
import re
from typing import Dict

from PySide2 import QtWidgets

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.preset_location_pool_ui import Ui_PresetLocationPool
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.area_list_helper import AreaListHelper, dark_world_flags
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.preset import Preset


class PresetLocationPool(PresetTab, Ui_PresetLocationPool, AreaListHelper):
    _editor: PresetEditor

    _starting_location_for_world: Dict[str, QtWidgets.QCheckBox]
    _starting_location_for_area: Dict[int, QtWidgets.QCheckBox]

    def __init__(self, editor: PresetEditor, game: GameDescription):
        super().__init__()
        self.setupUi(self)
        self._editor = editor
        self.game_description = game

        self.randomization_mode_combo.setItemData(0, RandomizationMode.FULL)
        self.randomization_mode_combo.setItemData(1, RandomizationMode.MAJOR_MINOR_SPLIT)
        self.randomization_mode_combo.currentIndexChanged.connect(self._on_update_randomization_mode)

        vertical_layouts = [
            QtWidgets.QVBoxLayout(self.excluded_locations_area_contents),
            QtWidgets.QVBoxLayout(self.excluded_locations_area_contents),
        ]
        for layout in vertical_layouts:
            self.excluded_locations_area_layout.addLayout(layout)

        world_list = self.game_description.world_list
        self._location_pool_for_node = {}

        nodes_by_world = collections.defaultdict(list)
        node_names = {}
        pickup_match = re.compile(r"Pickup \(([^\)]+)\)")

        for world in world_list.worlds:
            for is_dark_world in dark_world_flags(world):
                for area in world.areas:
                    if area.in_dark_aether != is_dark_world:
                        continue
                    for node in area.nodes:
                        if isinstance(node, PickupNode):
                            nodes_by_world[world.correct_name(is_dark_world)].append(node)
                            match = pickup_match.match(node.name)
                            if match is not None:
                                node_name = match.group(1)
                            else:
                                node_name = node.name
                            node_names[node] = f"{world_list.nodes_to_area(node).name} ({node_name})"

        for i, world_name in enumerate(sorted(nodes_by_world.keys())):
            group_box = QtWidgets.QGroupBox(self.excluded_locations_area_contents)
            group_box.setTitle(world_name)
            vertical_layout = QtWidgets.QVBoxLayout(group_box)
            vertical_layout.setContentsMargins(8, 4, 8, 4)
            vertical_layout.setSpacing(2)
            group_box.vertical_layout = vertical_layout
            vertical_layouts[i % len(vertical_layouts)].addWidget(group_box)

            for node in sorted(nodes_by_world[world_name], key=node_names.get):
                check = QtWidgets.QCheckBox(group_box)
                check.setText(node_names[node])
                check.node = node
                check.stateChanged.connect(functools.partial(self._on_check_location, check))
                group_box.vertical_layout.addWidget(check)
                self._location_pool_for_node[node] = check

        for layout in vertical_layouts:
            layout.addSpacerItem(
                QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

    @property
    def uses_patches_tab(self) -> bool:
        return False

    @property
    def game_enum(self) -> RandovaniaGame:
        return self.game_description.game

    def on_preset_changed(self, preset: Preset):
        available_locations = preset.configuration.available_locations
        common_qt_lib.set_combo_with_value(self.randomization_mode_combo, available_locations.randomization_mode)

        self.during_batch_check_update = True
        for node, check in self._location_pool_for_node.items():
            check.setChecked(node.pickup_index not in available_locations.excluded_indices)
            check.setEnabled(available_locations.randomization_mode == RandomizationMode.FULL or node.major_location)
        self.during_batch_check_update = False

    def _on_update_randomization_mode(self):
        with self._editor as editor:
            editor.available_locations = dataclasses.replace(
                editor.available_locations, randomization_mode=self.randomization_mode_combo.currentData())

    def _on_check_location(self, check: QtWidgets.QCheckBox, _):
        if self.during_batch_check_update:
            return
        with self._editor as editor:
            editor.available_locations = editor.available_locations.ensure_index(check.node.pickup_index,
                                                                                 not check.isChecked())
