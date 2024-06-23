from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description import default_database
from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.games.prime3.gui.generated.corruption_layout_editor_ui import Ui_CorruptionLayoutEditor
from randovania.games.prime3.patcher.gollop_corruption_patcher import layout_string_for_items

if TYPE_CHECKING:
    from randovania.game_description.pickup.pickup_database import PickupDatabase


def _fill_combo(pickup_database: PickupDatabase, combo: QtWidgets.QComboBox) -> None:
    items: list[str] = []
    items.extend(item.name for item in pickup_database.standard_pickups.values())
    items.extend(item.name for item in pickup_database.ammo_pickups.values())
    items.extend(f"Energy Cell {i}" for i in range(1, 10))

    for item in sorted(items):
        combo.addItem(item, item)


class CorruptionLayoutEditor(QtWidgets.QWidget, Ui_CorruptionLayoutEditor):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.game_description = default_database.game_description_for(RandovaniaGame.METROID_PRIME_CORRUPTION)
        pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_PRIME_CORRUPTION)
        region_list = self.game_description.region_list
        self._index_to_combo = {}

        ids_to_merge = [
            5406397194789083955,  # Phaaze
            16039522250714156185,
            10717625015048596485,
            14806081023590793725,
        ]
        nodes_to_merge: list[PickupNode] = []

        region_count = 0
        for i, region in enumerate(region_list.regions):
            if region.extra["asset_id"] in ids_to_merge:
                nodes_to_merge.extend(
                    node for area in region.areas for node in area.nodes if isinstance(node, PickupNode)
                )
                continue

            group = QtWidgets.QGroupBox(self.scroll_area_contents)
            group.setTitle(region.name)

            layout = QtWidgets.QGridLayout(group)

            area_count = 0
            for area in region.areas:
                for node in area.nodes:
                    if not isinstance(node, PickupNode):
                        continue

                    node_label = QtWidgets.QLabel(region_list.node_name(node), group)
                    layout.addWidget(node_label, area_count, 0)

                    node_combo = QtWidgets.QComboBox(group)
                    _fill_combo(pickup_database, node_combo)
                    node_combo.currentIndexChanged.connect(self.update_layout_string)
                    layout.addWidget(node_combo, area_count, 1)

                    self._index_to_combo[node.pickup_index] = node_combo
                    area_count += 1

            self.scroll_area_layout.addWidget(group)
            region_count += 1

        group = QtWidgets.QGroupBox(self.scroll_area_contents)
        group.setTitle("Seeds")

        layout = QtWidgets.QGridLayout(group)
        area_count = 0
        for node in nodes_to_merge:
            if not isinstance(node, PickupNode):
                continue

            node_label = QtWidgets.QLabel(region_list.node_name(node), group)
            layout.addWidget(node_label, area_count, 0)

            node_combo = QtWidgets.QComboBox(group)
            _fill_combo(pickup_database, node_combo)
            node_combo.currentIndexChanged.connect(self.update_layout_string)
            layout.addWidget(node_combo, area_count, 1)

            self._index_to_combo[node.pickup_index] = node_combo
            area_count += 1

        self.scroll_area_layout.addWidget(group)
        # region_count += 1
        self.update_layout_string()

    def update_layout_string(self) -> None:
        item_names = [combo.currentData() for combo in self._index_to_combo.values()]
        self.layout_edit.setText(layout_string_for_items(item_names))
