from PySide2 import QtWidgets

from randovania.game_description import default_database
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.world.node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.games.patchers.gollop_corruption_patcher import layout_string_for_items
from randovania.gui.generated.corruption_layout_editor_ui import Ui_CorruptionLayoutEditor
from randovania.gui.lib import common_qt_lib


def _fill_combo(item_database: ItemDatabase, combo: QtWidgets.QComboBox):
    items = []
    items.extend(item.name for item in item_database.major_items.values())
    items.extend(item.name for item in item_database.ammo.values())
    items.extend(f"Energy Cell {i}" for i in range(1, 10))

    for item in sorted(items):
        combo.addItem(item, item)


class CorruptionLayoutEditor(QtWidgets.QMainWindow, Ui_CorruptionLayoutEditor):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game_description = default_database.game_description_for(RandovaniaGame.METROID_PRIME_CORRUPTION)
        item_database = default_database.item_database_for_game(RandovaniaGame.METROID_PRIME_CORRUPTION)
        world_list = self.game_description.world_list
        self._index_to_combo = {}

        columns = []
        for i in range(2):
            columns.append(QtWidgets.QVBoxLayout(self.scroll_area_contents))
            self.scroll_area_layout.addLayout(columns[-1])

        ids_to_merge = [5406397194789083955,  # Phaaze
                        16039522250714156185,
                        10717625015048596485,
                        14806081023590793725,
                        ]
        nodes_to_merge = []

        world_count = 0
        for i, world in enumerate(world_list.worlds):
            if world.world_asset_id in ids_to_merge:
                nodes_to_merge.extend(
                    node
                    for area in world.areas
                    for node in area.nodes
                    if isinstance(node, PickupNode)
                )
                continue

            group = QtWidgets.QGroupBox(self.scroll_area_contents)
            group.setTitle(world.name)

            layout = QtWidgets.QGridLayout(group)

            area_count = 0
            for area in world.areas:
                for node in area.nodes:
                    if not isinstance(node, PickupNode):
                        continue

                    node_label = QtWidgets.QLabel(world_list.node_name(node), group)
                    layout.addWidget(node_label, area_count, 0)

                    node_combo = QtWidgets.QComboBox(group)
                    _fill_combo(item_database, node_combo)
                    node_combo.currentIndexChanged.connect(self.update_layout_string)
                    layout.addWidget(node_combo, area_count, 1)

                    self._index_to_combo[node.pickup_index] = node_combo
                    area_count += 1

            columns[world_count % len(columns)].addWidget(group)
            world_count += 1

        group = QtWidgets.QGroupBox(self.scroll_area_contents)
        group.setTitle("Seeds")

        layout = QtWidgets.QGridLayout(group)
        area_count = 0
        for node in nodes_to_merge:
            if not isinstance(node, PickupNode):
                continue

            node_label = QtWidgets.QLabel(world_list.node_name(node), group)
            layout.addWidget(node_label, area_count, 0)

            node_combo = QtWidgets.QComboBox(group)
            _fill_combo(item_database, node_combo)
            node_combo.currentIndexChanged.connect(self.update_layout_string)
            layout.addWidget(node_combo, area_count, 1)

            self._index_to_combo[node.pickup_index] = node_combo
            area_count += 1

        columns[0].addWidget(group)
        # world_count += 1
        self.update_layout_string()

    def update_layout_string(self):
        item_names = [
            combo.currentData()
            for combo in self._index_to_combo.values()
        ]
        self.layout_edit.setText(layout_string_for_items(item_names))
