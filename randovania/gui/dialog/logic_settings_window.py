import dataclasses
import functools
from typing import Dict

from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QComboBox, QLabel, QDialog, QGroupBox, QVBoxLayout, QSpinBox

from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.node import PickupNode
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world_list import WorldList
from randovania.games.prime import default_data
from randovania.gui.dialog.trick_details_popup import TrickDetailsPopup
from randovania.gui.game_patches_window import GamePatchesWindow
from randovania.gui.generated.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.common_qt_lib import set_combo_with_value
from randovania.gui.lib.trick_lib import difficulties_for_trick, used_tricks
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.main_rules import MainRulesWindow
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.available_locations import RandomizationMode
from randovania.layout.beam_configuration import BeamAmmoConfiguration
from randovania.layout.hint_configuration import SkyTempleKeyHintMode
from randovania.layout.layout_configuration import LayoutElevators, LayoutSkyTempleKeyMode, LayoutDamageStrictness
from randovania.layout.preset import Preset
from randovania.layout.starting_location import StartingLocation
from randovania.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.layout.trick_level import LayoutTrickLevel, TrickLevelConfiguration


def _update_options_when_true(options: Options, field_name: str, new_value, checked: bool):
    if checked:
        with options:
            setattr(options, field_name, new_value)


def _update_options_by_value(options: Options, combo: QComboBox, new_index: int):
    with options:
        setattr(options, combo.options_field_name, combo.currentData())


_TRICK_LEVEL_DESCRIPTION = {
    LayoutTrickLevel.NO_TRICKS: [
        "This mode requires no knowledge about the game, nor does it require any abuse "
        "of game mechanics, making it ideal for casual and first time players."
    ],
    LayoutTrickLevel.TRIVIAL: [
        "This mode includes strategies that abuses oversights in the game, such as bomb jumping to the item "
        "in Temple Assembly Site and destroying the gate in Trooper Security Station with Screw Attack."
    ],
    LayoutTrickLevel.EASY: ["This mode assumes you can do simple tricks."],
    LayoutTrickLevel.NORMAL: ["This mode expands on the Easy mode, including more difficult to execute tricks."],
    LayoutTrickLevel.HARD: ["This mode expands on Normal with additional tricks, such as Grand Abyss scan dash."],
    LayoutTrickLevel.HYPERMODE: [
        "This mode considers every single trick and path known to Randovania as valid, "
        "such as Polluted Mire without Space Jump. No OOB is included."
    ],
    LayoutTrickLevel.MINIMAL_RESTRICTIONS: [
        "This mode only checks that Screw Attack, Dark Visor and Light Suit won't all be behind "
        "Ing Caches and Dark Water, removing the biggest reasons for a pure random layout to be impossible. "
        "There are no guarantees that a seed will be possible in this case."
    ],
}

_BEAMS = {
    "power": "Power Beam",
    "dark": "Dark Beam",
    "light": "Light Beam",
    "annihilator": "Annihilator Beam",
}


def _get_trick_level_description(trick_level: LayoutTrickLevel) -> str:
    return "<html><head/><body>{}</body></html>".format(
        "".join(
            '<p align="justify">{}</p>'.format(item)
            for item in _TRICK_LEVEL_DESCRIPTION[trick_level]
        )
    )


class LogicSettingsWindow(QDialog, Ui_LogicSettingsWindow):
    _combo_for_gate: Dict[TranslatorGate, QComboBox]
    _checkbox_for_trick: Dict[SimpleResourceInfo, QtWidgets.QCheckBox]
    _location_pool_for_node: Dict[PickupNode, QtWidgets.QCheckBox]
    _starting_location_for_area: Dict[int, QtWidgets.QCheckBox]
    _slider_for_trick: Dict[SimpleResourceInfo, QtWidgets.QSlider]
    _editor: PresetEditor
    world_list: WorldList
    _during_batch_check_update: bool = False

    def __init__(self, window_manager: WindowManager, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._editor = editor
        self._window_manager = window_manager
        self._main_rules = MainRulesWindow(editor)
        self._game_patches = GamePatchesWindow(editor)

        self.game_description = default_database.default_prime2_game_description()
        self.world_list = self.game_description.world_list
        self.resource_database = self.game_description.resource_database

        # Update with Options
        self.logic_tab_widget.addTab(self._main_rules.centralWidget, "Item Pool")
        self.patches_tab_widget.addTab(self._game_patches.centralWidget, "Other")

        self.name_edit.textEdited.connect(self._edit_name)
        self.setup_trick_level_elements()
        self.setup_damage_elements()
        self.setup_elevator_elements()
        self.setup_sky_temple_elements()
        self.setup_starting_area_elements()
        self.setup_location_pool_elements()
        self.setup_translators_elements()
        self.setup_hint_elements()
        self.setup_beam_configuration_elements()

        # Alignment
        self.trick_level_layout.setAlignment(QtCore.Qt.AlignTop)
        self.elevator_layout.setAlignment(QtCore.Qt.AlignTop)
        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        self.starting_area_layout.setAlignment(QtCore.Qt.AlignTop)
        self.translators_layout.setAlignment(QtCore.Qt.AlignTop)
        self.hint_layout.setAlignment(QtCore.Qt.AlignTop)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    # Options
    def on_preset_changed(self, preset: Preset):
        self._main_rules.on_preset_changed(preset)
        self._game_patches.on_preset_changed(preset)

        # Variables
        layout_config = preset.layout_configuration
        patcher_config = preset.patcher_configuration

        # Title
        common_qt_lib.set_edit_if_different(self.name_edit, preset.name)

        # Trick Level
        trick_level_configuration = preset.layout_configuration.trick_level_configuration
        trick_level = trick_level_configuration.global_level

        set_combo_with_value(self.logic_combo_box, trick_level)
        self.logic_level_label.setText(_get_trick_level_description(trick_level))

        for (trick, checkbox), slider in zip(self._checkbox_for_trick.items(), self._slider_for_trick.values()):
            assert self._slider_for_trick[trick] is slider

            has_specific_level = trick_level_configuration.has_specific_level_for_trick(trick)

            checkbox.setEnabled(trick_level != LayoutTrickLevel.MINIMAL_RESTRICTIONS)
            slider.setEnabled(has_specific_level)
            slider.setValue(trick_level_configuration.level_for_trick(trick).as_number)
            checkbox.setChecked(has_specific_level)

        # Damage
        set_combo_with_value(self.damage_strictness_combo, layout_config.damage_strictness)
        self.energy_tank_capacity_spin_box.setValue(layout_config.energy_per_tank)
        self.varia_suit_spin_box.setValue(patcher_config.varia_suit_damage)
        self.dark_suit_spin_box.setValue(patcher_config.dark_suit_damage)

        # Elevator
        set_combo_with_value(self.elevators_combo, layout_config.elevators)

        # Sky Temple Keys
        keys = layout_config.sky_temple_keys
        if isinstance(keys.value, int):
            self.skytemple_slider.setValue(keys.value)
            data = int
        else:
            data = keys
        set_combo_with_value(self.skytemple_combo, data)

        # Starting Area
        starting_locations = layout_config.starting_location.locations

        self._during_batch_check_update = True
        for world in self.game_description.world_list.worlds:
            for area in world.areas:
                is_checked = AreaLocation(world.world_asset_id, area.area_asset_id) in starting_locations
                self._starting_location_for_area[area.area_asset_id].setChecked(is_checked)
        self._during_batch_check_update = False

        # Location Pool
        available_locations = layout_config.available_locations
        set_combo_with_value(self.randomization_mode_combo, available_locations.randomization_mode)

        self._during_batch_check_update = True
        for node, check in self._location_pool_for_node.items():
            check.setChecked(node.pickup_index not in available_locations.excluded_indices)
            check.setEnabled(available_locations.randomization_mode == RandomizationMode.FULL or node.major_location)
        self._during_batch_check_update = False

        # Translator Gates
        translator_configuration = preset.layout_configuration.translator_configuration
        for gate, combo in self._combo_for_gate.items():
            set_combo_with_value(combo, translator_configuration.translator_requirement[gate])

        # Hints
        set_combo_with_value(self.hint_sky_temple_key_combo, preset.layout_configuration.hints.sky_temple_keys)

        # Beam Configuration
        self.on_preset_changed_beam_configuration(preset)

    def _edit_name(self, value: str):
        with self._editor as editor:
            editor.name = value

    # Trick Level

    def _create_difficulty_details_row(self):
        row = 1

        trick_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
        trick_label.setWordWrap(True)
        trick_label.setFixedWidth(80)
        trick_label.setText("Difficulty Details")

        self.trick_difficulties_layout.addWidget(trick_label, row, 1, 1, 1)

        slider_layout = QtWidgets.QGridLayout()
        slider_layout.setHorizontalSpacing(0)
        for i in range(12):
            slider_layout.setColumnStretch(i, 1)

        for i, trick_level in enumerate(LayoutTrickLevel):
            if trick_level not in {LayoutTrickLevel.NO_TRICKS, LayoutTrickLevel.MINIMAL_RESTRICTIONS}:
                tool_button = QtWidgets.QToolButton(self.trick_level_scroll_contents)
                tool_button.setText(trick_level.long_name)
                tool_button.clicked.connect(functools.partial(self._open_difficulty_details_popup, trick_level))

                slider_layout.addWidget(tool_button, 1, 2 * i, 1, 2)

        self.trick_difficulties_layout.addLayout(slider_layout, row, 2, 1, 1)

    def setup_trick_level_elements(self):
        # logic_combo_box
        for i, trick_level in enumerate(LayoutTrickLevel):
            self.logic_combo_box.setItemData(i, trick_level)

        self.logic_combo_box.currentIndexChanged.connect(self._on_trick_level_changed)

        self.trick_difficulties_layout = QtWidgets.QGridLayout()
        self._checkbox_for_trick = {}
        self._slider_for_trick = {}

        configurable_tricks = TrickLevelConfiguration.all_possible_tricks()
        tricks_in_use = used_tricks(self.world_list)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

        self._create_difficulty_details_row()

        row = 2
        for trick in sorted(self.resource_database.trick, key=lambda _trick: _trick.long_name):
            if trick.index not in configurable_tricks or trick not in tricks_in_use:
                continue

            if row > 1:
                self.trick_difficulties_layout.addItem(QtWidgets.QSpacerItem(20, 40,
                                                                             QtWidgets.QSizePolicy.Minimum,
                                                                             QtWidgets.QSizePolicy.Expanding))

            trick_configurable = QtWidgets.QCheckBox(self.trick_level_scroll_contents)
            trick_configurable.setFixedWidth(16)
            trick_configurable.stateChanged.connect(functools.partial(self._on_check_trick_configurable, trick))
            self._checkbox_for_trick[trick] = trick_configurable
            self.trick_difficulties_layout.addWidget(trick_configurable, row, 0, 1, 1)

            trick_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
            trick_label.setSizePolicy(size_policy)
            trick_label.setWordWrap(True)
            trick_label.setFixedWidth(80)
            trick_label.setText(trick.long_name)

            self.trick_difficulties_layout.addWidget(trick_label, row, 1, 1, 1)

            slider_layout = QtWidgets.QGridLayout()
            slider_layout.setHorizontalSpacing(0)
            for i in range(12):
                slider_layout.setColumnStretch(i, 1)

            horizontal_slider = QtWidgets.QSlider(self.trick_level_scroll_contents)
            horizontal_slider.setMaximum(5)
            horizontal_slider.setPageStep(2)
            horizontal_slider.setOrientation(QtCore.Qt.Horizontal)
            horizontal_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            horizontal_slider.setEnabled(False)
            horizontal_slider.valueChanged.connect(functools.partial(self._on_slide_trick_slider, trick))
            self._slider_for_trick[trick] = horizontal_slider
            slider_layout.addWidget(horizontal_slider, 0, 1, 1, 10)

            used_difficulties = difficulties_for_trick(self.world_list, trick)
            for i, trick_level in enumerate(LayoutTrickLevel):
                if trick_level == LayoutTrickLevel.NO_TRICKS or trick_level in used_difficulties:
                    difficulty_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
                    difficulty_label.setAlignment(QtCore.Qt.AlignHCenter)
                    difficulty_label.setText(trick_level.long_name)

                    slider_layout.addWidget(difficulty_label, 1, 2 * i, 1, 2)

            self.trick_difficulties_layout.addLayout(slider_layout, row, 2, 1, 1)

            tool_button = QtWidgets.QToolButton(self.trick_level_scroll_contents)
            tool_button.setText("?")
            tool_button.clicked.connect(functools.partial(self._open_trick_details_popup, trick))
            self.trick_difficulties_layout.addWidget(tool_button, row, 3, 1, 1)

            row += 1

        self.trick_level_layout.addLayout(self.trick_difficulties_layout)

    def _on_check_trick_configurable(self, trick: SimpleResourceInfo, enabled: int):
        enabled = bool(enabled)

        with self._editor as options:
            if options.layout_configuration.trick_level_configuration.has_specific_level_for_trick(trick) != enabled:
                options.set_layout_configuration_field(
                    "trick_level_configuration",
                    options.layout_configuration.trick_level_configuration.set_level_for_trick(
                        trick,
                        self.logic_combo_box.currentData() if enabled else None
                    )
                )

    def _on_slide_trick_slider(self, trick: SimpleResourceInfo, value: int):
        if self._slider_for_trick[trick].isEnabled():
            with self._editor as options:
                options.set_layout_configuration_field(
                    "trick_level_configuration",
                    options.layout_configuration.trick_level_configuration.set_level_for_trick(
                        trick,
                        LayoutTrickLevel.from_number(value)
                    )
                )

    def _on_trick_level_changed(self):
        trick_level = self.logic_combo_box.currentData()
        with self._editor as options:
            options.set_layout_configuration_field(
                "trick_level_configuration",
                dataclasses.replace(options.layout_configuration.trick_level_configuration,
                                    global_level=trick_level)
            )

    def _exec_trick_details(self, popup: TrickDetailsPopup):
        self._trick_details_popup = popup
        self._trick_details_popup.setWindowModality(Qt.WindowModal)
        self._trick_details_popup.open()

    def _open_trick_details_popup(self, trick: SimpleResourceInfo):
        self._exec_trick_details(TrickDetailsPopup(
            self,
            self._window_manager,
            self.game_description,
            trick,
            self._editor.layout_configuration.trick_level_configuration.level_for_trick(trick),
        ))

    def _open_difficulty_details_popup(self, difficulty: LayoutTrickLevel):
        self._exec_trick_details(TrickDetailsPopup(
            self,
            self._window_manager,
            self.game_description,
            None,
            difficulty,
        ))

    # Damage strictness
    def setup_damage_elements(self):
        self.damage_strictness_combo.setItemData(0, LayoutDamageStrictness.STRICT)
        self.damage_strictness_combo.setItemData(1, LayoutDamageStrictness.MEDIUM)
        self.damage_strictness_combo.setItemData(2, LayoutDamageStrictness.LENIENT)

        self.damage_strictness_combo.options_field_name = "layout_configuration_damage_strictness"
        self.damage_strictness_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                                   self._editor,
                                                                                   self.damage_strictness_combo))

        def _persist_float(attribute_name: str):
            def persist(value: float):
                with self._editor as options:
                    options.set_patcher_configuration_field(attribute_name, value)

            return persist

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        self.varia_suit_spin_box.valueChanged.connect(_persist_float("varia_suit_damage"))
        self.dark_suit_spin_box.valueChanged.connect(_persist_float("dark_suit_damage"))

    def _persist_tank_capacity(self):
        with self._editor as editor:
            editor.set_layout_configuration_field("energy_per_tank", self.energy_tank_capacity_spin_box.value())

    # Elevator
    def setup_elevator_elements(self):
        self.elevators_combo.setItemData(0, LayoutElevators.VANILLA)
        self.elevators_combo.setItemData(1, LayoutElevators.TWO_WAY_RANDOMIZED)
        self.elevators_combo.setItemData(2, LayoutElevators.TWO_WAY_UNCHECKED)
        self.elevators_combo.setItemData(3, LayoutElevators.ONE_WAY_ELEVATOR)
        self.elevators_combo.setItemData(4, LayoutElevators.ONE_WAY_ANYTHING)

        self.elevators_combo.options_field_name = "layout_configuration_elevators"
        self.elevators_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                           self._editor,
                                                                           self.elevators_combo))

    # Sky Temple Key
    def setup_sky_temple_elements(self):
        self.skytemple_combo.setItemData(0, LayoutSkyTempleKeyMode.ALL_BOSSES)
        self.skytemple_combo.setItemData(1, LayoutSkyTempleKeyMode.ALL_GUARDIANS)
        self.skytemple_combo.setItemData(2, int)

        self.skytemple_combo.options_field_name = "layout_configuration_sky_temple_keys"
        self.skytemple_combo.currentIndexChanged.connect(self._on_sky_temple_key_combo_changed)
        self.skytemple_slider.valueChanged.connect(self._on_sky_temple_key_combo_slider_changed)

    def _on_sky_temple_key_combo_changed(self):
        combo_enum = self.skytemple_combo.currentData()
        with self._editor:
            if combo_enum is int:
                self.skytemple_slider.setEnabled(True)
                self._editor.layout_configuration_sky_temple_keys = LayoutSkyTempleKeyMode(
                    self.skytemple_slider.value())
            else:
                self.skytemple_slider.setEnabled(False)
                self._editor.layout_configuration_sky_temple_keys = combo_enum

    def _on_sky_temple_key_combo_slider_changed(self):
        self.skytemple_slider_label.setText(str(self.skytemple_slider.value()))
        self._on_sky_temple_key_combo_changed()

    # Starting Area
    def setup_starting_area_elements(self):
        game_description = default_prime2_game_description()
        world_to_group = {}
        self._starting_location_for_area = {}

        for row, world in enumerate(game_description.world_list.worlds):
            for column, is_dark_world in enumerate([False, True]):
                group_box = QGroupBox(self.starting_locations_contents)
                group_box.setTitle(world.correct_name(is_dark_world))
                vertical_layout = QVBoxLayout(group_box)
                vertical_layout.setContentsMargins(8, 4, 8, 4)
                vertical_layout.setSpacing(2)
                vertical_layout.setAlignment(QtCore.Qt.AlignTop)
                group_box.vertical_layout = vertical_layout

                world_to_group[world.correct_name(is_dark_world)] = group_box
                self.starting_locations_layout.addWidget(group_box, row, column)

        for world in game_description.world_list.worlds:
            for area in sorted(world.areas, key=lambda a: a.name):
                group_box = world_to_group[world.correct_name(area.in_dark_aether)]
                check = QtWidgets.QCheckBox(group_box)
                check.setText(area.name)
                check.area_location = AreaLocation(world.world_asset_id, area.area_asset_id)
                check.stateChanged.connect(functools.partial(self._on_check_starting_area, check))
                group_box.vertical_layout.addWidget(check)
                self._starting_location_for_area[area.area_asset_id] = check

        self.starting_area_quick_fill_ship.clicked.connect(self._starting_location_on_select_ship)
        self.starting_area_quick_fill_save_station.clicked.connect(self._starting_location_on_select_save_station)

    def _on_check_starting_area(self, check, _):
        if self._during_batch_check_update:
            return
        with self._editor as editor:
            editor.set_layout_configuration_field(
                "starting_location",
                editor.layout_configuration.starting_location.ensure_has_location(check.area_location,
                                                                                  check.isChecked())
            )

    def _starting_location_on_select_ship(self):
        with self._editor as editor:
            editor.set_layout_configuration_field(
                "starting_location",
                StartingLocation.with_elements([self.game_description.starting_location])
            )

    def _starting_location_on_select_save_station(self):
        world_list = self.game_description.world_list
        save_stations = [world_list.node_to_area_location(node)
                         for node in world_list.all_nodes if node.name == "Save Station"]

        with self._editor as editor:
            editor.set_layout_configuration_field(
                "starting_location",
                StartingLocation.with_elements(save_stations)
            )

    # Location Pool
    def setup_location_pool_elements(self):
        self.randomization_mode_combo.setItemData(0, RandomizationMode.FULL)
        self.randomization_mode_combo.setItemData(1, RandomizationMode.MAJOR_MINOR_SPLIT)
        self.randomization_mode_combo.currentIndexChanged.connect(self._on_update_randomization_mode)

        game_description = default_prime2_game_description()
        world_to_group = {}
        self._location_pool_for_node = {}

        for world in game_description.world_list.worlds:
            for is_dark_world in [False, True]:
                group_box = QGroupBox(self.excluded_locations_area_contents)
                group_box.setTitle(world.correct_name(is_dark_world))
                vertical_layout = QVBoxLayout(group_box)
                vertical_layout.setContentsMargins(8, 4, 8, 4)
                vertical_layout.setSpacing(2)
                group_box.vertical_layout = vertical_layout

                world_to_group[world.correct_name(is_dark_world)] = group_box
                self.excluded_locations_area_layout.addWidget(group_box)

        for world, area, node in game_description.world_list.all_worlds_areas_nodes:
            if not isinstance(node, PickupNode):
                continue

            group_box = world_to_group[world.correct_name(area.in_dark_aether)]
            check = QtWidgets.QCheckBox(group_box)
            check.setText(game_description.world_list.node_name(node))
            check.node = node
            check.stateChanged.connect(functools.partial(self._on_check_location, check))
            group_box.vertical_layout.addWidget(check)
            self._location_pool_for_node[node] = check

    def _on_update_randomization_mode(self):
        with self._editor as editor:
            editor.available_locations = dataclasses.replace(
                editor.available_locations, randomization_mode=self.randomization_mode_combo.currentData())

    def _on_check_location(self, check: QtWidgets.QCheckBox, _):
        if self._during_batch_check_update:
            return
        with self._editor as editor:
            editor.available_locations = editor.available_locations.ensure_index(check.node.pickup_index,
                                                                                 not check.isChecked())

    # Translator Gates
    def setup_translators_elements(self):
        randomizer_data = default_data.decode_randomizer_data()

        self.translator_randomize_all_button.clicked.connect(self._on_randomize_all_gates_pressed)
        self.translator_vanilla_actual_button.clicked.connect(self._on_vanilla_actual_gates_pressed)
        self.translator_vanilla_colors_button.clicked.connect(self._on_vanilla_colors_gates_pressed)

        self._combo_for_gate = {}

        for i, gate in enumerate(randomizer_data["TranslatorLocationData"]):
            label = QLabel(self.translators_scroll_contents)
            label.setText(gate["Name"])
            self.translators_layout.addWidget(label, 3 + i, 0, 1, 1)

            combo = QComboBox(self.translators_scroll_contents)
            combo.gate = TranslatorGate(gate["Index"])
            for item in LayoutTranslatorRequirement:
                combo.addItem(item.long_name, item)
            combo.currentIndexChanged.connect(functools.partial(self._on_gate_combo_box_changed, combo))

            self.translators_layout.addWidget(combo, 3 + i, 1, 1, 2)
            self._combo_for_gate[combo.gate] = combo

    def _on_randomize_all_gates_pressed(self):
        with self._editor as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                options.layout_configuration.translator_configuration.with_full_random())

    def _on_vanilla_actual_gates_pressed(self):
        with self._editor as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                options.layout_configuration.translator_configuration.with_vanilla_actual())

    def _on_vanilla_colors_gates_pressed(self):
        with self._editor as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                options.layout_configuration.translator_configuration.with_vanilla_colors())

    def _on_gate_combo_box_changed(self, combo: QComboBox, new_index: int):
        with self._editor as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                options.layout_configuration.translator_configuration.replace_requirement_for_gate(
                    combo.gate, combo.currentData()))

    # Hints
    def setup_hint_elements(self):
        for i, stk_hint_mode in enumerate(SkyTempleKeyHintMode):
            self.hint_sky_temple_key_combo.setItemData(i, stk_hint_mode)

        self.hint_sky_temple_key_combo.currentIndexChanged.connect(self._on_stk_combo_changed)

    def _on_stk_combo_changed(self, new_index: int):
        with self._editor as options:
            options.set_layout_configuration_field(
                "hints",
                dataclasses.replace(options.layout_configuration.hints,
                                    sky_temple_keys=self.hint_sky_temple_key_combo.currentData()))

    # Beam Configuration
    def setup_beam_configuration_elements(self):

        def _add_header(text: str, col: int):
            label = QLabel(self.beam_configuration_group)
            label.setText(text)
            self.beam_configuration_layout.addWidget(label, 0, col)

        _add_header("Ammo A", 1)
        _add_header("Ammo B", 2)
        _add_header("Uncharged", 3)
        _add_header("Charged", 4)
        _add_header("Combo", 5)
        _add_header("Missiles for Combo", 6)

        self._beam_ammo_a = {}
        self._beam_ammo_b = {}
        self._beam_uncharged = {}
        self._beam_charged = {}
        self._beam_combo = {}
        self._beam_missile = {}

        def _create_ammo_combo():
            combo = QComboBox(self.beam_configuration_group)
            combo.addItem("None", -1)
            combo.addItem("Power Bomb", 43)
            combo.addItem("Missile", 44)
            combo.addItem("Dark Ammo", 45)
            combo.addItem("Light Ammo", 46)
            return combo

        row = 1
        for beam, beam_name in _BEAMS.items():
            label = QLabel(self.beam_configuration_group)
            label.setText(beam_name)
            self.beam_configuration_layout.addWidget(label, row, 0)

            ammo_a = _create_ammo_combo()
            ammo_a.currentIndexChanged.connect(functools.partial(
                self._on_ammo_type_combo_changed, beam, ammo_a, False))
            self._beam_ammo_a[beam] = ammo_a
            self.beam_configuration_layout.addWidget(ammo_a, row, 1)

            ammo_b = _create_ammo_combo()
            ammo_b.currentIndexChanged.connect(functools.partial(
                self._on_ammo_type_combo_changed, beam, ammo_b, True))
            self._beam_ammo_b[beam] = ammo_b
            self.beam_configuration_layout.addWidget(ammo_b, row, 2)

            spin_box = QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" ammo")
            spin_box.setMaximum(250)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "uncharged_cost"
            ))
            self._beam_uncharged[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 3)

            spin_box = QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" ammo")
            spin_box.setMaximum(250)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "charged_cost"
            ))
            self._beam_charged[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 4)

            spin_box = QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" ammo")
            spin_box.setMaximum(250)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "combo_ammo_cost"
            ))
            self._beam_combo[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 5)

            spin_box = QSpinBox(self.beam_configuration_group)
            spin_box.setSuffix(" missile")
            spin_box.setMaximum(250)
            spin_box.setMinimum(1)
            spin_box.valueChanged.connect(functools.partial(
                self._on_ammo_cost_spin_changed, beam, "combo_missile_cost"
            ))
            self._beam_missile[beam] = spin_box
            self.beam_configuration_layout.addWidget(spin_box, row, 6)

            row += 1

    def _on_ammo_type_combo_changed(self, beam: str, combo: QComboBox, is_ammo_b: bool, _):
        with self._editor as editor:
            beam_configuration = editor.layout_configuration.beam_configuration
            old_config: BeamAmmoConfiguration = getattr(beam_configuration, beam)
            if is_ammo_b:
                new_config = dataclasses.replace(old_config, ammo_b=combo.currentData())
            else:
                new_config = dataclasses.replace(old_config, ammo_a=combo.currentData())

            editor.set_layout_configuration_field("beam_configuration",
                                                  dataclasses.replace(beam_configuration, **{beam: new_config}))

    def _on_ammo_cost_spin_changed(self, beam: str, field_name: str, value: int):
        with self._editor as editor:
            beam_configuration = editor.layout_configuration.beam_configuration
            new_config = dataclasses.replace(getattr(beam_configuration, beam),
                                             **{field_name: value})
            editor.set_layout_configuration_field("beam_configuration",
                                                  dataclasses.replace(beam_configuration, **{beam: new_config}))

    def on_preset_changed_beam_configuration(self, preset: Preset):
        beam_configuration = preset.layout_configuration.beam_configuration

        for beam in _BEAMS:
            config: BeamAmmoConfiguration = getattr(beam_configuration, beam)

            self._beam_ammo_a[beam].setCurrentIndex(self._beam_ammo_a[beam].findData(config.ammo_a))
            self._beam_ammo_b[beam].setCurrentIndex(self._beam_ammo_b[beam].findData(config.ammo_b))
            self._beam_ammo_b[beam].setEnabled(config.ammo_a != -1)
            self._beam_uncharged[beam].setValue(config.uncharged_cost)
            self._beam_charged[beam].setValue(config.charged_cost)
            self._beam_combo[beam].setValue(config.combo_ammo_cost)
            self._beam_missile[beam].setValue(config.combo_missile_cost)
