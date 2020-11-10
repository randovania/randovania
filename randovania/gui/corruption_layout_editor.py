import hashlib

from PySide2 import QtWidgets

from randovania.game_description import data_reader, default_database
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.node import PickupNode
from randovania.games.prime import default_data
from randovania.gui.generated.corruption_layout_editor_ui import Ui_CorruptionLayoutEditor
from randovania.gui.lib import common_qt_lib


def _fill_combo(item_database: ItemDatabase, combo: QtWidgets.QComboBox):
    items = []
    items.extend(item.name for item in item_database.major_items.values())
    items.extend(item.name for item in item_database.ammo.values())
    items.extend(f"Energy Cell {i}" for i in range(1, 10))

    for item in sorted(items):
        combo.addItem(item, item)


_LETTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ(){}[]<>=,.!#^-+?"
_ITEM_TO_INDEX = {
    "Power Beam": 0,
    "Plasma Beam": 1,
    "Nova Beam": 2,
    "Charge Beam": 3,

    "Missile Launcher": 4,
    "Ice Missile": 5,
    "Seeker Missile": 6,

    "Grapple Lasso": 7,
    "Grapple Swing": 8,
    "Grapple Voltage": 9,

    "Combat Visor": 11,
    "Scan Visor": 12,
    "Command Visor": 13,
    "X-Ray Visor": 14,

    "Space Jump Boots": 15,
    "Screw Attack": 16,

    "Hazard Shield": 17,
    "Energy Tank": 20,

    "Morph Ball": 32,
    "Morph Ball Bombs": 10,
    "Boost Ball": 33,
    "Spider Ball": 34,

    "Hypermode": 35,
    "Hyper Missile": 37,
    "Hyper Ball": 38,
    "Hyper Grapple": 39,

    "Ship Grapple": 44,
    "Ship Missile": 45,
    "Missile Expansion": 46,
    "Ship Missile Expansion": 47
}
letter_to_item_mapping = {
    "0": ["Power Beam"],
    "1": ["Plasma Beam"],
    "2": ["Nova Beam"],
    "3": ["Charge Beam"],
    "4": ["Missile Expansion"],
    "5": ["Ice Missile"],
    "6": ["Seeker Missile"],
    "7": ["Grapple Lasso"],
    "8": ["Grapple Swing"],
    "9": ["Grapple Voltage"],
    "a": ["Morph Ball Bombs"],
    "b": ["Combat Visor"],
    "c": ["Scan Visor"],
    "d": ["Command Visor"],
    "e": ["X-Ray Visor"],
    "f": ["Space Jump Boots"],
    "g": ["Screw Attack"],
    "h": ["Hazard Shield"],
    # "i": ["Energy"],
    # "j": ["HyperModeEnergy"],
    "k": ["Energy Tank"],
    # "l": ["ItemPercentage"],
    # "m": ["Fuses"],
    "n": ["Energy Cell 1"],
    "o": ["Energy Cell 2"],
    "p": ["Energy Cell 3"],
    "q": ["Energy Cell 4"],
    "r": ["Energy Cell 5"],
    "s": ["Energy Cell 6"],
    "t": ["Energy Cell 7"],
    "u": ["Energy Cell 8"],
    "v": ["Energy Cell 9"],
    "w": ["Morph Ball"],
    "x": ["Boost Ball"],
    "y": ["Spider Ball"],
    "z": ["Hypermode"],
    # "A": ["HyperModeBeam"],
    "B": ["Hyper Missile"],
    "C": ["Hyper Ball"],
    "D": ["Hyper Grapple"],
    # "E": ["HyperModePermanent"],
    # "F": ["HyperModePhaaze"],
    # "G": ["HyperModeOriginal"],
    "H": ["Ship Grapple"],
    "I": ["Ship Missile Expansion"],
    # "J": ["FaceCorruptionLevel"],
    # "K": ["PhazonBall"],
    # "L": ["CannonBall"],
    # "M": ["ActivateMorphballBoost"],
    # "N": ["HyperShot"],
    # "O": ["CommandVisorJammed"],
    # "P": ["Stat_Enemies_Killed"],
    # "Q": ["Stat_ShotsFired"],
    # "R": ["Stat_DamageReceived"],
    # "S": ["Stat_DataSaves"],
    # "T": ["Stat_HypermodeUses"],
    # "U": ["Stat_CommandoKills"],
    # "V": ["Stat_TinCanHighScore"],
    # "W": ["Stat_TinCanCurrentScore"],
    "X": ["Missile Expansion"] * 2,
    "Y": ["Missile Expansion"] * 3,
    "Z": ["Missile Expansion"] * 4,
    "(": ["Missile Expansion"] * 5,
    ")": ["Missile Expansion"] * 6,
    "{": ["Missile Expansion"] * 7,
    "}": ["Missile Expansion"] * 8,
    "[": ["Energy Tank", "Energy Tank"],
    "]": ["Energy Tank", "Energy Tank", "Energy Tank"],
    "<": ["Ship Missile Expansion", "Ship Missile Expansion"],
    ">": ["Missile", "Energy Tank"],
    "=": ["Energy Tank", "Missile"],
    ",": ["Missile", "Energy Tank", "Missile"],
    ".": ["Missile", "Ship Missile Expansion"],
    "!": ["Ship Missile Expansion", "Missile"],
    "#": ["Missile Launcher"],
    "^": ["Ship Missile"],
    "-": ["Ship Missile Expansion", "Energy Tank"],
    "+": ["Energy Tank", "Ship Missile Expansion"],
    "?": ["Missile", "Ship Missile Expansion", "Missile"],
}

item_to_letter_mapping = {
    items[0]: letter
    for letter, items in letter_to_item_mapping.items()
    if len(items) == 1
}


class CorruptionLayoutEditor(QtWidgets.QMainWindow, Ui_CorruptionLayoutEditor):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game_description = data_reader.decode_data(default_data.decode_default_prime3())
        item_database = default_database.default_prime3_item_database()
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

        letters = [_LETTERS[0]] * 2
        for item in item_names:
            letters.append(item_to_letter_mapping[item])

        result = "".join(letters)
        sha = hashlib.sha256(result.encode("ascii"))
        result += sha.hexdigest()[:5]

        self.layout_edit.setText(result)
