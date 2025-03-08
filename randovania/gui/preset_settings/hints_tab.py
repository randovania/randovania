from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from frozendict import frozendict
from PySide6 import QtCore, QtWidgets

from randovania.gui.generated.preset_hints_ui import Ui_PresetHints
from randovania.gui.lib import signal_handling
from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.layout.base.hint_configuration import SpecificPickupHintMode
from randovania.lib import dataclass_lib

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from randovania.game.hints import SpecificHintDetails
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.preset import Preset


class PresetHints(PresetTab, Ui_PresetHints):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # random hints
        if game_description.has_random_hints:
            signal_handling.on_checked(
                self.enable_random_hints_check, self._persist_hints_field("enable_random_hints", bool)
            )
            signal_handling.on_checked(self.resolver_hints_check, self._persist_hints_field("use_resolver_hints", bool))

            minimum_available_meta = dataclass_lib.get_field(
                editor.hint_configuration, "minimum_available_locations_for_hint_placement"
            ).metadata
            self.minimum_available_locations_spin_box.setMinimum(minimum_available_meta["min"])
            self.minimum_available_locations_spin_box.setMaximum(minimum_available_meta["max"])
            self.minimum_available_locations_spin_box.valueChanged.connect(
                self._persist_hints_field("minimum_available_locations_for_hint_placement", int)
            )

            minimum_weight_meta = dataclass_lib.get_field(
                editor.hint_configuration, "minimum_location_weight_for_hint_placement"
            ).metadata
            self.minimum_weight_spin_box.setMinimum(minimum_weight_meta["min"])
            self.minimum_weight_spin_box.setMaximum(minimum_weight_meta["max"])
            self.minimum_weight_spin_box.setSingleStep(minimum_weight_meta["precision"])
            self.minimum_weight_spin_box.valueChanged.connect(
                self._persist_hints_field("minimum_location_weight_for_hint_placement", float)
            )
        else:
            self.random_hints_box.setVisible(False)

        # specific location hints
        if game_description.has_specific_location_hints:
            signal_handling.on_checked(
                self.enable_specific_location_hints_check,
                self._persist_hints_field("enable_specific_location_hints", bool),
            )
        else:
            self.specific_location_hints_box.setVisible(False)

        # specific pickup hints
        self.specific_pickup_groups: dict[str, QtWidgets.QGroupBox] = {}
        self.specific_pickup_combos: dict[str, QtWidgets.QComboBox] = {}

        if game_description.has_specific_pickup_hints:
            for hint, details in game_description.game.hints.specific_pickup_hints.items():
                self.create_specific_hint_group(hint, details)
        else:
            self.specific_pickup_hints_box.setVisible(False)

    @classmethod
    def tab_title(cls) -> str:
        return "Hints"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset[BaseConfiguration]) -> None:
        hints_config = preset.configuration.hints
        self.enable_random_hints_check.setChecked(hints_config.enable_random_hints)
        self.resolver_hints_check.setChecked(hints_config.use_resolver_hints)
        self.minimum_available_locations_spin_box.setValue(hints_config.minimum_available_locations_for_hint_placement)
        self.minimum_weight_spin_box.setValue(hints_config.minimum_location_weight_for_hint_placement)

        for w in [
            self.resolver_hints_check,
            self.resolver_hints_label,
            self.minimum_weight_widget,
            self.minimum_weight_description,
            self.minimum_available_locations_widget,
            self.minimum_available_locations_description,
        ]:
            w.setEnabled(hints_config.enable_random_hints)

        self.enable_specific_location_hints_check.setChecked(hints_config.enable_specific_location_hints)

        for hint, mode in hints_config.specific_pickup_hints.items():
            set_combo_with_value(self.specific_pickup_combos[hint], mode)

    def _on_specific_hint_combo_changed(self, hint: str, new_index: int) -> None:
        new_dict = dict(self._editor.hint_configuration.specific_pickup_hints)
        new_dict[hint] = self.specific_pickup_combos[hint].currentData()

        with self._editor as editor:
            editor.set_hint_configuration_field("specific_pickup_hints", frozendict(new_dict))

    def _persist_hints_field[T](self, field_name: str, field_type: type[T]) -> Callable[[T], None]:
        def bound(value: T) -> None:
            with self._editor as editor:
                editor.set_hint_configuration_field(field_name, value)

        return bound

    @property
    def development_settings(self) -> Iterator[QtWidgets.QWidget]:
        yield self.resolver_hints_line
        yield self.resolver_hints_check
        yield self.resolver_hints_label

        yield self.minimum_available_locations_description
        yield self.minimum_available_locations_line
        yield self.minimum_available_locations_widget

        yield self.minimum_weight_description
        yield self.minimum_weight_line
        yield self.minimum_weight_widget

    def create_specific_hint_group(self, hint: str, details: SpecificHintDetails) -> None:
        """Create the widget for editing this specific pickup hint, and connect its signal."""

        hint_group = QtWidgets.QGroupBox(self.specific_pickup_hints_box)
        hint_group.setObjectName(f"hint_{hint}_group")
        hint_group.setTitle(details.long_name)
        vertical_layout = QtWidgets.QVBoxLayout(hint_group)
        vertical_layout.setSpacing(6)
        vertical_layout.setContentsMargins(11, 11, 11, 11)
        vertical_layout.setObjectName(f"hint_{hint}_vertical_layout")

        label = QtWidgets.QLabel(hint_group)
        label.setObjectName(f"hint_{hint}_label")
        label.setWordWrap(True)
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        label.setText(
            f"{details.description}\n\n"
            f"{SpecificPickupHintMode.DISABLED.description}: {details.disabled_details}\n\n"
            f"{SpecificPickupHintMode.HIDE_AREA.description}: {details.hide_area_details}\n\n"
            f"{SpecificPickupHintMode.PRECISE.description}: {details.precise_details}"
        )

        vertical_layout.addWidget(label)

        combo = QtWidgets.QComboBox(hint_group)
        for i, mode in enumerate(SpecificPickupHintMode):
            combo.addItem(mode.description, mode)
        combo.setObjectName(f"hint_{hint}_combo")

        vertical_layout.addWidget(combo)

        self.verticalLayout.addWidget(hint_group)
        self.specific_pickup_groups[hint] = hint_group
        self.specific_pickup_combos[hint] = combo
        signal_handling.on_combo(combo, functools.partial(self._on_specific_hint_combo_changed, hint))
