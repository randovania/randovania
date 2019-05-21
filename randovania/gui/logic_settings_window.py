import dataclasses
import functools
from typing import Optional, Dict

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import QMainWindow, QComboBox, QLabel, QGridLayout

from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world_list import WorldList
from randovania.games.prime import default_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import set_combo_with_value
from randovania.gui.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common.options import Options
from randovania.layout.hint_configuration import SkyTempleKeyHintMode
from randovania.layout.layout_configuration import LayoutElevators, LayoutTrickLevel, LayoutSkyTempleKeyMode
from randovania.layout.starting_location import StartingLocationConfiguration, StartingLocation
from randovania.layout.translator_configuration import LayoutTranslatorRequirement


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
        "This mode includes strategies that abuses oversights in the game, such as being able to activate the "
        "Hive Dynamo Works portal from the other side of the chasm and bomb jumping in Temple Assembly Site."
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
        "Ing Caches and Dark Water, removing the biggest reasons for a pure random layout to be impossible.",
    ],
}


_CONFIGURABLE_TRICKS = {
    0,  # Scan Dash
    1,  # Difficult Bomb Jump
    2,  # Slope Jump
    3,  # R Jump
    4,  # BSJ
    5,  # Roll Jump
    6,  # Underwater Dash
    7,  # Air Underwater
    8,  # Floaty
    9,  # Infinite Speed
    10,  # SA without SJ
    11,  # Wall Boost
    12,  # Jump off Enemy
    15,  # Instant Morph
}


def _used_tricks(world_list: WorldList):
    result = set()

    for area in world_list.all_areas:
        for node in area.nodes:
            for connection in area.connections[node].values():
                for alternative in connection.alternatives:
                    for individual in alternative.values():
                        if individual.resource.resource_type == ResourceType.TRICK:
                            result.add(individual.resource)

    return result


def _get_trick_level_description(trick_level: LayoutTrickLevel) -> str:
    return "<html><head/><body>{}</body></html>".format(
        "".join(
            '<p align="justify">{}</p>'.format(item)
            for item in _TRICK_LEVEL_DESCRIPTION[trick_level]
        )
    )


class LogicSettingsWindow(QMainWindow, Ui_LogicSettingsWindow):
    _combo_for_gate: Dict[TranslatorGate, QComboBox]
    _checkbox_for_trick: Dict[SimpleResourceInfo, QtWidgets.QCheckBox]
    _slider_for_trick: Dict[SimpleResourceInfo, QtWidgets.QSlider]
    _options: Options
    world_list: WorldList

    def __init__(self, tab_service: TabService, background_processor: BackgroundTaskMixin, options: Options):
        super().__init__()
        self.setupUi(self)
        self._options = options

        game_description = default_database.default_prime2_game_description(False)
        self.world_list = game_description.world_list
        self.resource_database = game_description.resource_database

        # Update with Options
        self.setup_trick_level_elements()
        self.setup_elevator_elements()
        self.setup_sky_temple_elements()
        self.setup_starting_area_elements()
        self.setup_translators_elements()
        self.setup_hint_elements()

        # Alignment
        self.trick_level_layout.setAlignment(QtCore.Qt.AlignTop)
        self.elevator_layout.setAlignment(QtCore.Qt.AlignTop)
        self.goal_layout.setAlignment(QtCore.Qt.AlignTop)
        self.starting_area_layout.setAlignment(QtCore.Qt.AlignTop)
        self.translators_layout.setAlignment(QtCore.Qt.AlignTop)
        self.hint_layout.setAlignment(QtCore.Qt.AlignTop)

    # Options
    def on_options_changed(self, options: Options):
        # Trick Level
        trick_level = options.layout_configuration_trick_level

        set_combo_with_value(self.logic_combo_box, trick_level)
        self.logic_level_label.setText(_get_trick_level_description(trick_level))

        per_trick_level = options.layout_configuration.per_trick_level

        for trick, checkbox in self._checkbox_for_trick.items():
            checkbox.setEnabled(trick_level != LayoutTrickLevel.MINIMAL_RESTRICTIONS)
            checkbox.setChecked(trick.index in per_trick_level.values)

        for trick, slider in self._slider_for_trick.items():
            level = per_trick_level.values.get(trick.index, trick_level)
            slider.setValue(list(LayoutTrickLevel).index(level))

        # Elevator
        set_combo_with_value(self.elevators_combo, options.layout_configuration_elevators)

        # Sky Temple Keys
        keys = options.layout_configuration_sky_temple_keys
        if isinstance(keys.value, int):
            self.skytemple_slider.setValue(keys.value)
            data = int
        else:
            data = keys
        set_combo_with_value(self.skytemple_combo, data)

        # Starting Area
        starting_location = options.layout_configuration.starting_location
        set_combo_with_value(self.startingarea_combo, starting_location.configuration)

        if starting_location.configuration == StartingLocationConfiguration.CUSTOM:
            area_location = starting_location.custom_location
            world = self.world_list.world_by_asset_id(area_location.world_asset_id)

            set_combo_with_value(self.specific_starting_world_combo, world)
            set_combo_with_value(self.specific_starting_area_combo, world.area_by_asset_id(area_location.area_asset_id))

        # Translator Gates
        translator_configuration = options.layout_configuration.translator_configuration
        self.always_up_gfmc_compound_check.setChecked(translator_configuration.fixed_gfmc_compound)
        self.always_up_torvus_temple_check.setChecked(translator_configuration.fixed_torvus_temple)
        self.always_up_great_temple_check.setChecked(translator_configuration.fixed_great_temple)
        for gate, combo in self._combo_for_gate.items():
            set_combo_with_value(combo, translator_configuration.translator_requirement[gate])

        # Hints
        set_combo_with_value(self.hint_sky_temple_key_combo, options.layout_configuration.hints.sky_temple_keys)

    # Trick Level
    def setup_trick_level_elements(self):
        # logic_combo_box
        for i, trick_level in enumerate(LayoutTrickLevel):
            self.logic_combo_box.setItemData(i, trick_level)

        self.logic_combo_box.currentIndexChanged.connect(self._on_trick_level_changed)

        self.trick_difficulties_layout = QtWidgets.QGridLayout()
        self._checkbox_for_trick = {}
        self._slider_for_trick = {}
        row = 0

        used_tricks = _used_tricks(self.world_list)

        row = 1
        for trick in sorted(self.resource_database.trick, key=lambda trick: trick.long_name):
            if trick.index not in _CONFIGURABLE_TRICKS or trick not in used_tricks:
                continue

            trick_configurable = QtWidgets.QCheckBox(self.trick_level_tab)
            trick_configurable.setFixedWidth(20)
            trick_configurable.stateChanged.connect(functools.partial(self._on_check_trick_configurable, trick))
            self._checkbox_for_trick[trick] = trick_configurable
            self.trick_difficulties_layout.addWidget(trick_configurable, row, 0, 1, 1)

            trick_label = QtWidgets.QLabel(self.trick_level_tab)
            trick_label.setText(trick.long_name)

            self.trick_difficulties_layout.addWidget(trick_label, row, 1, 1, 1)
            
            slider_layout = QtWidgets.QGridLayout()
            slider_layout.setHorizontalSpacing(0)
            for i in range(12):
                slider_layout.setColumnStretch(i, 1)
            
            horizontal_slider = QtWidgets.QSlider(self.trick_level_tab)
            horizontal_slider.setMaximum(5)
            horizontal_slider.setPageStep(2)
            horizontal_slider.setOrientation(QtCore.Qt.Horizontal)
            horizontal_slider.setTickPosition(QtWidgets.QSlider.TicksAbove)
            horizontal_slider.setEnabled(False)
            horizontal_slider.valueChanged.connect(functools.partial(self._on_slide_trick_slider, trick))
            self._slider_for_trick[trick] = horizontal_slider
            slider_layout.addWidget(horizontal_slider, 0, 1, 1, 10)
            
            for i, trick_level in enumerate(LayoutTrickLevel):
                if trick_level == LayoutTrickLevel.MINIMAL_RESTRICTIONS:
                    continue
                
                difficulty_label = QtWidgets.QLabel(self.trick_level_tab)
                difficulty_label.setAlignment(QtCore.Qt.AlignHCenter)
                difficulty_label.setText(trick_level.long_name)
            
                slider_layout.addWidget(difficulty_label, 1, 2*i, 1, 2)
            
            self.trick_difficulties_layout.addLayout(slider_layout, row, 2, 1, 1)

            tool_button = QtWidgets.QToolButton(self.trick_level_tab)
            tool_button.setText("?")
            self.trick_difficulties_layout.addWidget(tool_button, row, 3, 1, 1)

            row += 1

        self.trick_level_layout.addLayout(self.trick_difficulties_layout)

    def _on_check_trick_configurable(self, trick: SimpleResourceInfo, enabled: int):
        enabled = bool(enabled)

        with self._options:
            values = self._options.layout_configuration.per_trick_level.values
            if enabled:
                values[trick.index] = self.logic_combo_box.currentData()
            else:
                del values[trick.index]
            self._options._check_editable_and_mark_dirty()

        self._slider_for_trick[trick].setEnabled(enabled)

    def _on_slide_trick_slider(self, trick: SimpleResourceInfo, value: int):
        if self._slider_for_trick[trick].isEnabled():
            with self._options:
                values = self._options.layout_configuration.per_trick_level.values
                values[trick.index] = list(LayoutTrickLevel)[value]
                self._options._check_editable_and_mark_dirty()

    def _on_trick_level_changed(self):
        trick_level = self.logic_combo_box.currentData()
        _update_options_when_true(self._options, "layout_configuration_trick_level", trick_level, True)

    # Elevator
    def setup_elevator_elements(self):
        self.elevators_combo.setItemData(0, LayoutElevators.VANILLA)
        self.elevators_combo.setItemData(1, LayoutElevators.RANDOMIZED)

        self.elevators_combo.options_field_name = "layout_configuration_elevators"
        self.elevators_combo.currentIndexChanged.connect(functools.partial(_update_options_by_value,
                                                                           self._options,
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
        with self._options:
            if combo_enum is int:
                self.skytemple_slider.setEnabled(True)
                self._options.layout_configuration_sky_temple_keys = LayoutSkyTempleKeyMode(
                    self.skytemple_slider.value())
            else:
                self.skytemple_slider.setEnabled(False)
                self._options.layout_configuration_sky_temple_keys = combo_enum

    def _on_sky_temple_key_combo_slider_changed(self):
        self.skytemple_slider_label.setText(str(self.skytemple_slider.value()))
        self._on_sky_temple_key_combo_changed()

    # Starting Area
    def setup_starting_area_elements(self):
        self.startingarea_combo.setItemData(0, StartingLocationConfiguration.SHIP)
        self.startingarea_combo.setItemData(1, StartingLocationConfiguration.RANDOM_SAVE_STATION)
        self.startingarea_combo.setItemData(2, StartingLocationConfiguration.CUSTOM)

        for world in sorted(self.world_list.worlds, key=lambda x: x.name):
            self.specific_starting_world_combo.addItem(world.name, userData=world)

        self.specific_starting_world_combo.currentIndexChanged.connect(self._on_select_world)
        self.specific_starting_area_combo.currentIndexChanged.connect(self._on_select_area)
        self.startingarea_combo.currentIndexChanged.connect(self._on_starting_area_configuration_changed)

    def _on_starting_area_configuration_changed(self):
        specific_enabled = self.startingarea_combo.currentData() == StartingLocationConfiguration.CUSTOM
        self.specific_starting_world_combo.setEnabled(specific_enabled)
        self.specific_starting_area_combo.setEnabled(specific_enabled)
        self._on_select_world()
        self._update_starting_location()

    def _on_select_world(self):
        self.specific_starting_area_combo.clear()
        for area in sorted(self.specific_starting_world_combo.currentData().areas, key=lambda x: x.name):
            self.specific_starting_area_combo.addItem(area.name, userData=area)

    def _on_select_area(self):
        if self.specific_starting_area_combo.currentData() is not None:
            self._update_starting_location()

    def _update_starting_location(self):
        if self._has_valid_starting_location():
            with self._options as options:
                options.set_layout_configuration_field(
                    "starting_location",
                    StartingLocation(self.startingarea_combo.currentData(), self.current_starting_area_location))

    @property
    def current_starting_area_location(self) -> Optional[AreaLocation]:
        if self.specific_starting_world_combo.isEnabled():
            return AreaLocation(
                self.specific_starting_world_combo.currentData().world_asset_id,
                self.specific_starting_area_combo.currentData().area_asset_id,
            )
        else:
            return None

    def _has_valid_starting_location(self):
        current_config = self.startingarea_combo.currentData()
        if current_config == StartingLocationConfiguration.CUSTOM:
            return self.specific_starting_area_combo.currentData() is not None
        else:
            return True

    # Translator Gates
    def setup_translators_elements(self):
        randomizer_data = default_data.decode_randomizer_data()

        self.always_up_gfmc_compound_check.stateChanged.connect(
            functools.partial(self._on_always_up_check_changed, "fixed_gfmc_compound"))
        self.always_up_torvus_temple_check.stateChanged.connect(
            functools.partial(self._on_always_up_check_changed, "fixed_torvus_temple"))
        self.always_up_great_temple_check.stateChanged.connect(
            functools.partial(self._on_always_up_check_changed, "fixed_great_temple"))

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

    def _on_always_up_check_changed(self, field_name: str, new_value: int):
        with self._options as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                dataclasses.replace(options.layout_configuration.translator_configuration,
                                    **{field_name: bool(new_value)}))

    def _on_randomize_all_gates_pressed(self):
        with self._options as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                options.layout_configuration.translator_configuration.with_full_random())

    def _on_vanilla_actual_gates_pressed(self):
        with self._options as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                options.layout_configuration.translator_configuration.with_vanilla_actual())

    def _on_vanilla_colors_gates_pressed(self):
        with self._options as options:
            options.set_layout_configuration_field(
                "translator_configuration",
                options.layout_configuration.translator_configuration.with_vanilla_colors())

    def _on_gate_combo_box_changed(self, combo: QComboBox, new_index: int):
        with self._options as options:
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
        with self._options as options:
            options.set_layout_configuration_field(
                "hints",
                dataclasses.replace(options.layout_configuration.hints,
                                    sky_temple_keys=self.hint_sky_temple_key_combo.currentData()))
