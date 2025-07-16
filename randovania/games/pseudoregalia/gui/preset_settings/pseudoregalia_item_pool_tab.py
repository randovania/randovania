from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description import default_database
from randovania.gui.lib.scroll_protected import ScrollProtectedSpinBox
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool, _create_separator
from randovania.layout.base.standard_pickup_state import DEFAULT_MAXIMUM_SHUFFLED

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PseudoregaliaPresetItemPool(PresetItemPool):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        pickup_database = default_database.pickup_database_for_game(self.game)
        self._health_piece_item = pickup_database.standard_pickups["Health Piece"]
        self._create_health_piece_box(game_description.resource_database.get_item("HealthPiece"))

    def on_preset_changed(self, preset: Preset) -> None:
        super().on_preset_changed(preset)
        layout = preset.configuration
        major_configuration = layout.standard_pickup_configuration

        # Health Piece
        health_piece_state = major_configuration.pickups_state[self._health_piece_item]
        self.health_piece_starting_spinbox.setValue(health_piece_state.num_included_in_starting_pickups)
        self.health_piece_shuffled_spinbox.setValue(health_piece_state.num_shuffled_pickups)

    def _create_health_piece_box(self, health_piece_resource: ItemResourceInfo) -> None:
        category_box, category_layout, _ = self._boxes_for_category["health"]

        category_layout.addWidget(_create_separator(category_box), category_layout.rowCount(), 0, 1, -1)

        starting_label = QtWidgets.QLabel(category_box)
        starting_label.setText("<b>Starting Health Pieces</b>")

        self.health_piece_starting_spinbox = ScrollProtectedSpinBox(category_box)
        self.health_piece_starting_spinbox.setMaximum(health_piece_resource.max_capacity)
        self.health_piece_starting_spinbox.valueChanged.connect(self._on_update_starting_health_piece)

        starting_layout_index = category_layout.rowCount()
        category_layout.addWidget(starting_label, starting_layout_index, 0)
        category_layout.addWidget(self.health_piece_starting_spinbox, starting_layout_index, 1)

        shuffled_label = QtWidgets.QLabel(category_box)
        shuffled_label.setText("<b>Shuffled Health Pieces</b>")

        self.health_piece_shuffled_spinbox = ScrollProtectedSpinBox(category_box)
        self.health_piece_shuffled_spinbox.setMaximum(DEFAULT_MAXIMUM_SHUFFLED[-1])
        self.health_piece_shuffled_spinbox.valueChanged.connect(self._on_update_shuffled_health_piece)

        shuffled_layout_index = category_layout.rowCount()
        category_layout.addWidget(shuffled_label, shuffled_layout_index, 0)
        category_layout.addWidget(self.health_piece_shuffled_spinbox, shuffled_layout_index, 1)

    def _on_update_starting_health_piece(self, value: int) -> None:
        with self._editor as options:
            pickup_config = options.standard_pickup_configuration
            options.standard_pickup_configuration = pickup_config.replace_state_for_pickup(
                self._health_piece_item,
                dataclasses.replace(
                    pickup_config.pickups_state[self._health_piece_item], num_included_in_starting_pickups=value
                ),
            )

    def _on_update_shuffled_health_piece(self, value: int) -> None:
        with self._editor as options:
            pickup_config = options.standard_pickup_configuration
            options.standard_pickup_configuration = pickup_config.replace_state_for_pickup(
                self._health_piece_item,
                dataclasses.replace(pickup_config.pickups_state[self._health_piece_item], num_shuffled_pickups=value),
            )
