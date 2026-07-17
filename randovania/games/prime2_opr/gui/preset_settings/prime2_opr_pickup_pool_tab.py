from __future__ import annotations

import dataclasses
from functools import partial

from PySide6 import QtWidgets

from randovania.game_description.game_description import GameDescription
from randovania.game_description.pickup.pickup_definition.standard_pickup import StandardPickupDefinition
from randovania.games.prime2.gui.preset_settings.echoes_pickup_pool_tab import EchoesPresetPickupPool
from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.pickup_pool_tab import _create_separator, _format_expected_counts
from randovania.gui.preset_settings.split_ammo_widget import AmmoPickupWidgets
from randovania.gui.widgets.scroll_protected import ScrollProtectedDoubleSpinBox
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


class EchoesOPRPresetPickupPool(EchoesPresetPickupPool):
    _custom_item_widgets: dict[tuple[StandardPickupDefinition, str], tuple[QtWidgets.QDoubleSpinBox, AmmoPickupWidgets]]

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self._custom_item_widgets = {}

        box, layout = self._boxes_for_category["misc"][:2]
        layout.addWidget(_create_separator(box), layout.rowCount(), 0, 1, -1)

        self._create_custom_item_widget("Massive Damage", "damage_increase_per_massive_damage")
        self._create_custom_item_widget("Defense Up", "damage_reduction_per_defense_up")

    def _create_custom_item_widget(self, pickup_name: str, configuration_field: str) -> None:
        pickup = self.game_description.get_pickup_database().standard_pickups[pickup_name]
        item = self.game_description.get_resource_database_view().get_item(pickup.progression[0])

        percentage_spinbox = ScrollProtectedDoubleSpinBox()
        percentage_spinbox.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
        )
        percentage_spinbox.setMinimum(0.0)
        percentage_spinbox.setMaximum(item.extra.get("maximum_percentage", 100.0))
        percentage_spinbox.setDecimals(1)
        percentage_spinbox.setSuffix(f"% {item.extra.get('suffix', item.long_name)}")
        percentage_spinbox.valueChanged.connect(partial(self._on_custom_item_percentage_updated, configuration_field))

        widgets = self._create_ammo_pickup_box(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed),
            pickup,
            False,
            [percentage_spinbox],
            partial(self._on_custom_item_pickup_count_updated, pickup),
            include_expected_counts=True,
            explain_other_sources=False,
            mention_limit=True,
        )

        self._custom_item_widgets[pickup, configuration_field] = percentage_spinbox, widgets

    def _on_custom_item_pickup_count_updated(self, pickup: StandardPickupDefinition, value: int) -> None:
        with self._editor as editor:
            state = editor.standard_pickup_configuration.pickups_state[pickup]
            state = dataclasses.replace(state, num_shuffled_pickups=value)
            editor.standard_pickup_configuration = editor.standard_pickup_configuration.replace_state_for_pickup(
                pickup, state
            )

    def _on_custom_item_percentage_updated(self, field: str, value: float) -> None:
        with self._editor as editor:
            editor.set_configuration_field(field, value)

    def on_preset_changed(self, preset: Preset[EchoesOPRConfiguration]) -> None:
        super().on_preset_changed(preset)

        for (pickup, percentage_field), (percentage_spinbox, ammo_widgets) in self._custom_item_widgets.items():
            percentage_modifier: float = getattr(preset.configuration, percentage_field)
            percentage_spinbox.setValue(percentage_modifier)

            num_shuffled = preset.configuration.standard_pickup_configuration.pickups_state[pickup].num_shuffled_pickups
            ammo_widgets.pickup_spinbox.setValue(num_shuffled)

            total = num_shuffled * percentage_modifier

            item = self.game_description.get_resource_database_view().get_item(pickup.progression[0])

            if ammo_widgets.expected_count is None:
                continue

            ammo_widgets.expected_count.setText(
                _format_expected_counts(
                    pickup.progression,
                    ammo_widgets.expected_template,
                    dict.fromkeys(pickup.progression, total),
                    {item.short_name: item.extra.get("suffix", item.long_name)},
                    [total],
                    {item.short_name: item.extra.get("maximum_percentage", 100.0)},
                    use_percentage=True,
                )
            )
