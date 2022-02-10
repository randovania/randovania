from PySide2 import QtCore, QtWidgets

from randovania.game_description import default_database
from randovania.game_description.world.node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.layout_description_editor_window_ui import Ui_LayoutDescriptionEditorWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.foldable import Foldable
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.generator_parameters import GeneratorParameters


class LayoutDescriptionEditorWindow(QtWidgets.QMainWindow, Ui_LayoutDescriptionEditorWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Layout Editor")
        common_qt_lib.set_default_window_icon(self)

        game = RandovaniaGame.METROID_PRIME_ECHOES
        self._preset_manager = PresetManager(None)

        self._current_parameters = GeneratorParameters(
            seed_number=0,
            spoiler=True,
            presets=[
                self._preset_manager.default_preset_for_game(game).get_preset(),
                self._preset_manager.default_preset_for_game(game).get_preset(),
            ],
        )
        self.player_index_combo.setItemData(0, 0)
        self.player_index_combo.setItemData(1, 1)

        self.pickup_layout.setAlignment(QtCore.Qt.AlignTop)

        self.update_player_index()

    def update_player_index(self):
        current_index: int = self.player_index_combo.currentData()

        while self.pickup_layout.children():
            child: QtWidgets.QWidget = self.pickup_layout.takeAt(0)
            child.deleteLater()

        preset = self._current_parameters.get_preset(current_index)
        game = default_database.game_description_for(preset.game)

        for world in game.world_list.worlds:
            world_box = Foldable(world.name)
            world_box.setObjectName(f"pickups world_box {world.name}")
            world_layout = QtWidgets.QGridLayout()
            world_layout.setObjectName(f"pickups world_layout {world.name}")
            world_box.set_content_layout(world_layout)

            self.pickup_layout.addWidget(world_box)

            row = 0
            for node in world.all_nodes:
                if not isinstance(node, PickupNode):
                    continue

                pickup_label = QtWidgets.QLabel(world_box)
                pickup_label.setText(game.world_list.node_name(node))
                world_layout.addWidget(pickup_label, row, 0)

                target_spinbox = QtWidgets.QSpinBox(world_box)
                target_spinbox.setMinimum(1)
                target_spinbox.setMaximum(self._current_parameters.player_count)
                target_spinbox.setPrefix("Player ")
                target_spinbox.setSuffix("'s")
                world_layout.addWidget(target_spinbox, row, 1)

                target_combo = QtWidgets.QComboBox(world_box)
                world_layout.addWidget(target_combo, row, 2)

                row += 1
