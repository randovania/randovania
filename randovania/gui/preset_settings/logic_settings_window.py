import collections
import copy
import dataclasses
import functools
import re
from typing import Dict, Optional, List, Callable, FrozenSet

from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QComboBox, QDialog, QGroupBox, QVBoxLayout

from randovania.game_description import default_database
from randovania.game_description.area import Area
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.node import PickupNode, TeleporterNode
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.game_description.teleporter import Teleporter
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.generator import elevator_distributor
from randovania.gui.dialog.trick_details_popup import TrickDetailsPopup
from randovania.gui.generated.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.common_qt_lib import set_combo_with_value
from randovania.gui.lib.trick_lib import difficulties_for_trick, used_tricks
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.echoes_beam_configuration_tab import PresetEchoesBeamConfiguration
from randovania.gui.preset_settings.echoes_goal_tab import PresetEchoesGoal
from randovania.gui.preset_settings.echoes_hints_tab import PresetEchoesHints
from randovania.gui.preset_settings.echoes_patches_tab import PresetEchoesPatches
from randovania.gui.preset_settings.echoes_translators_tab import PresetEchoesTranslators
from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.enum_lib import iterate_enum
from randovania.interface_common.options import Options
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.available_locations import RandomizationMode
from randovania.layout.base_configuration import StartingLocationList
from randovania.layout.damage_strictness import LayoutDamageStrictness
from randovania.layout.echoes_configuration import EchoesConfiguration
from randovania.layout.location_list import LocationList
from randovania.layout.preset import Preset
from randovania.layout.teleporters import TeleporterShuffleMode, TeleporterTargetList, TeleporterList
from randovania.layout.trick_level import LayoutTrickLevel


def _update_options_when_true(options: Options, field_name: str, new_value, checked: bool):
    if checked:
        with options:
            setattr(options, field_name, new_value)


def dark_world_flags(world: World):
    yield False
    if world.dark_name is not None:
        yield True


def _update_options_by_value(options: Options, combo: QComboBox, new_index: int):
    with options:
        setattr(options, combo.options_field_name, combo.currentData())


class LogicSettingsWindow(QDialog, Ui_LogicSettingsWindow):
    _extra_tabs: List[PresetTab]
    _combo_for_gate: Dict[TranslatorGate, QComboBox]
    _location_pool_for_node: Dict[PickupNode, QtWidgets.QCheckBox]
    _elevator_source_for_location: Dict[Teleporter, QtWidgets.QCheckBox]
    _elevator_source_destination: Dict[Teleporter, Optional[Teleporter]]
    _elevator_target_for_world: Dict[str, QtWidgets.QCheckBox]
    _elevator_target_for_area: Dict[int, QtWidgets.QCheckBox]
    _starting_location_for_world: Dict[str, QtWidgets.QCheckBox]
    _starting_location_for_area: Dict[int, QtWidgets.QCheckBox]
    _slider_for_trick: Dict[TrickResourceInfo, QtWidgets.QSlider]
    _editor: PresetEditor
    world_list: WorldList
    _during_batch_check_update: bool = False

    def __init__(self, window_manager: Optional[WindowManager], editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._editor = editor
        self._window_manager = window_manager
        self._extra_tabs = []

        self.game_enum = editor.game
        self.game_description = default_database.game_description_for(self.game_enum)
        self.world_list = self.game_description.world_list
        self.resource_database = self.game_description.resource_database

        if self.game_enum == RandovaniaGame.PRIME2:
            self._extra_tabs.append(PresetEchoesGoal(editor))
            self._extra_tabs.append(PresetEchoesHints(editor))
            self._extra_tabs.append(PresetEchoesTranslators(editor))
            self._extra_tabs.append(PresetEchoesBeamConfiguration(editor))
            self._extra_tabs.append(PresetEchoesPatches(editor))

        elif self.game_enum == RandovaniaGame.PRIME3:
            pass

        self._extra_tabs.append(PresetItemPool(editor))

        for extra_tab in self._extra_tabs:
            if extra_tab.uses_patches_tab:
                tab = self.patches_tab_widget
            else:
                tab = self.logic_tab_widget
            tab.addTab(extra_tab, extra_tab.tab_title)

        self.name_edit.textEdited.connect(self._edit_name)
        self.setup_trick_level_elements()
        self.setup_damage_elements()
        self.setup_elevator_elements()
        self.setup_starting_area_elements()
        self.setup_location_pool_elements()

        # Alignment
        self.trick_level_layout.setAlignment(QtCore.Qt.AlignTop)
        self.elevator_layout.setAlignment(QtCore.Qt.AlignTop)
        self.starting_area_layout.setAlignment(QtCore.Qt.AlignTop)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    # Options
    def on_preset_changed(self, preset: Preset):
        for extra_tab in self._extra_tabs:
            extra_tab.on_preset_changed(preset)

        # Variables
        config = preset.configuration

        # Title
        common_qt_lib.set_edit_if_different(self.name_edit, preset.name)

        # Trick Level
        trick_level_configuration = preset.configuration.trick_level
        self.trick_level_minimal_logic_check.setChecked(trick_level_configuration.minimal_logic)

        for trick, slider in self._slider_for_trick.items():
            assert self._slider_for_trick[trick] is slider
            slider.setValue(trick_level_configuration.level_for_trick(trick).as_number)
            slider.setEnabled(not trick_level_configuration.minimal_logic)

        # Damage
        set_combo_with_value(self.damage_strictness_combo, config.damage_strictness)
        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)
        self.dangerous_tank_check.setChecked(config.dangerous_energy_tank)
        if self.game_enum == RandovaniaGame.PRIME2:
            self.safe_zone_logic_heal_check.setChecked(config.safe_zone.fully_heal)
            self.safe_zone_regen_spin.setValue(config.safe_zone.heal_per_second)
            self.varia_suit_spin_box.setValue(config.varia_suit_damage)
            self.dark_suit_spin_box.setValue(config.dark_suit_damage)

        # Elevator
        self.on_preset_changed_elevators(preset)

        # Starting Area
        self.on_preset_changed_starting_area(preset)

        # Location Pool
        available_locations = config.available_locations
        set_combo_with_value(self.randomization_mode_combo, available_locations.randomization_mode)

        self._during_batch_check_update = True
        for node, check in self._location_pool_for_node.items():
            check.setChecked(node.pickup_index not in available_locations.excluded_indices)
            check.setEnabled(available_locations.randomization_mode == RandomizationMode.FULL or node.major_location)
        self._during_batch_check_update = False

    def _edit_name(self, value: str):
        with self._editor as editor:
            editor.name = value

    # Trick Level

    def _create_difficulty_details_row(self):
        row = 1

        trick_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
        trick_label.setWordWrap(True)
        trick_label.setText("Difficulty Details")

        self.trick_difficulties_layout.addWidget(trick_label, row, 1, 1, -1)

        slider_layout = QtWidgets.QGridLayout()
        slider_layout.setHorizontalSpacing(0)
        for i in range(12):
            slider_layout.setColumnStretch(i, 1)
        #
        # if self._window_manager is not None:
        #     for i, trick_level in enumerate(LayoutTrickLevel):
        #         if trick_level not in {LayoutTrickLevel.NO_TRICKS, LayoutTrickLevel.MINIMAL_LOGIC}:
        #             tool_button = QtWidgets.QToolButton(self.trick_level_scroll_contents)
        #             tool_button.setText(trick_level.long_name)
        #             tool_button.clicked.connect(functools.partial(self._open_difficulty_details_popup, trick_level))
        #
        #             slider_layout.addWidget(tool_button, 1, 2 * i, 1, 2)

        self.trick_difficulties_layout.addLayout(slider_layout, row, 2, 1, 1)

    def setup_trick_level_elements(self):
        self.trick_level_minimal_logic_check.stateChanged.connect(self._on_trick_level_minimal_logic_check)

        self.trick_difficulties_layout = QtWidgets.QGridLayout()
        self._slider_for_trick = {}

        tricks_in_use = used_tricks(self.game_description)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

        self._create_difficulty_details_row()

        row = 2
        for trick in sorted(self.resource_database.trick, key=lambda _trick: _trick.long_name):
            if trick not in tricks_in_use:
                continue

            if row > 1:
                self.trick_difficulties_layout.addItem(QtWidgets.QSpacerItem(20, 40,
                                                                             QtWidgets.QSizePolicy.Minimum,
                                                                             QtWidgets.QSizePolicy.Expanding))

            trick_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
            trick_label.setSizePolicy(size_policy)
            trick_label.setWordWrap(True)
            trick_label.setFixedWidth(100)
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

            used_difficulties = difficulties_for_trick(self.game_description, trick)
            for i, trick_level in enumerate(iterate_enum(LayoutTrickLevel)):
                if trick_level == LayoutTrickLevel.DISABLED or trick_level in used_difficulties:
                    difficulty_label = QtWidgets.QLabel(self.trick_level_scroll_contents)
                    difficulty_label.setAlignment(QtCore.Qt.AlignHCenter)
                    difficulty_label.setText(trick_level.long_name)

                    slider_layout.addWidget(difficulty_label, 1, 2 * i, 1, 2)

            self.trick_difficulties_layout.addLayout(slider_layout, row, 2, 1, 1)

            if self._window_manager is not None:
                tool_button = QtWidgets.QToolButton(self.trick_level_scroll_contents)
                tool_button.setText("?")
                tool_button.clicked.connect(functools.partial(self._open_trick_details_popup, trick))
                self.trick_difficulties_layout.addWidget(tool_button, row, 3, 1, 1)

            row += 1

        self.trick_level_layout.addLayout(self.trick_difficulties_layout)

    def _on_slide_trick_slider(self, trick: TrickResourceInfo, value: int):
        if self._slider_for_trick[trick].isEnabled():
            with self._editor as options:
                options.set_configuration_field(
                    "trick_level",
                    options.configuration.trick_level.set_level_for_trick(
                        trick,
                        LayoutTrickLevel.from_number(value)
                    )
                )

    def _on_trick_level_minimal_logic_check(self, state: int):
        with self._editor as options:
            options.set_configuration_field(
                "trick_level",
                dataclasses.replace(options.configuration.trick_level,
                                    minimal_logic=bool(state))
            )

    def _exec_trick_details(self, popup: TrickDetailsPopup):
        self._trick_details_popup = popup
        self._trick_details_popup.setWindowModality(Qt.WindowModal)
        self._trick_details_popup.open()

    def _open_trick_details_popup(self, trick: TrickResourceInfo):
        self._exec_trick_details(TrickDetailsPopup(
            self,
            self._window_manager,
            self.game_description,
            trick,
            self._editor.configuration.trick_level.level_for_trick(trick),
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
                    options.set_configuration_field(attribute_name, value)

            return persist

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        self.dangerous_tank_check.stateChanged.connect(self._persist_dangerous_tank)

        if self.game_enum == RandovaniaGame.PRIME2:
            config_fields = {
                field.name: field
                for field in dataclasses.fields(EchoesConfiguration)
            }
            self.varia_suit_spin_box.setMinimum(config_fields["varia_suit_damage"].metadata["min"])
            self.varia_suit_spin_box.setMaximum(config_fields["varia_suit_damage"].metadata["max"])
            self.dark_suit_spin_box.setMinimum(config_fields["dark_suit_damage"].metadata["min"])
            self.dark_suit_spin_box.setMaximum(config_fields["dark_suit_damage"].metadata["max"])

            self.safe_zone_logic_heal_check.stateChanged.connect(self._persist_safe_zone_logic_heal)
            self.safe_zone_regen_spin.valueChanged.connect(self._persist_safe_zone_regen)
            self.varia_suit_spin_box.valueChanged.connect(_persist_float("varia_suit_damage"))
            self.dark_suit_spin_box.valueChanged.connect(_persist_float("dark_suit_damage"))
        else:
            self.dark_aether_box.setVisible(False)
            self.safe_zone_box.setVisible(False)

    def _persist_tank_capacity(self):
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _persist_safe_zone_regen(self):
        with self._editor as editor:
            safe_zone = dataclasses.replace(
                editor.configuration.safe_zone,
                heal_per_second=self.safe_zone_regen_spin.value()
            )
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_safe_zone_logic_heal(self):
        with self._editor as editor:
            safe_zone = dataclasses.replace(
                editor.configuration.safe_zone,
                fully_heal=self.safe_zone_logic_heal_check.isChecked()
            )
            editor.set_configuration_field("safe_zone", safe_zone)

    def _persist_dangerous_tank(self):
        with self._editor as editor:
            editor.set_configuration_field("dangerous_energy_tank", self.dangerous_tank_check.isChecked())

    # Area List

    def _areas_by_world_from_locations(self, all_area_locations: List[AreaLocation]):
        worlds = []
        areas_by_world = {}

        for location in all_area_locations:
            world = self.game_description.world_list.world_by_asset_id(location.world_asset_id)
            if world.world_asset_id not in areas_by_world:
                worlds.append(world)
                areas_by_world[world.world_asset_id] = []

            areas_by_world[world.world_asset_id].append(world.area_by_asset_id(location.area_asset_id))

        return worlds, areas_by_world

    def _create_area_list_selection(self, parent: QtWidgets.QWidget, layout: QtWidgets.QGridLayout,
                                    all_area_locations: List[AreaLocation],
                                    on_check: Callable[[List[AreaLocation], bool], None],
                                    ):
        world_to_group = {}
        checks_for_world = {}
        checks_for_area = {}

        worlds, areas_by_world = self._areas_by_world_from_locations(all_area_locations)
        worlds.sort(key=lambda it: it.name)

        def _on_check_area(c, _):
            if not self._during_batch_check_update:
                on_check([c.area_location], c.isChecked())

        def _on_check_world(c, _):
            if not self._during_batch_check_update:
                world_list = self.game_description.world_list
                w = world_list.world_by_asset_id(c.world_asset_id)
                world_areas = [world_list.area_to_area_location(a)
                               for a in w.areas if c.is_dark_world == a.in_dark_aether
                               if a.area_asset_id in checks_for_area]
                on_check(world_areas, c.isChecked())

        for row, world in enumerate(worlds):
            for column, is_dark_world in enumerate(dark_world_flags(world)):
                group_box = QGroupBox(parent)
                world_check = QtWidgets.QCheckBox(group_box)
                world_check.setText(world.correct_name(is_dark_world))
                world_check.world_asset_id = world.world_asset_id
                world_check.is_dark_world = is_dark_world
                world_check.stateChanged.connect(functools.partial(_on_check_world, world_check))
                world_check.setTristate(True)
                vertical_layout = QVBoxLayout(group_box)
                vertical_layout.setContentsMargins(8, 4, 8, 4)
                vertical_layout.setSpacing(2)
                vertical_layout.setAlignment(QtCore.Qt.AlignTop)
                separator = QtWidgets.QFrame()
                separator.setFrameShape(QtWidgets.QFrame.HLine)
                separator.setFrameShadow(QtWidgets.QFrame.Sunken)
                group_box.vertical_layout = vertical_layout
                group_box.vertical_layout.addWidget(world_check)
                group_box.vertical_layout.addWidget(separator)

                world_to_group[world.correct_name(is_dark_world)] = group_box
                layout.addWidget(group_box, row, column)
                checks_for_world[world.correct_name(is_dark_world)] = world_check

        for world in worlds:
            for area in sorted(areas_by_world[world.world_asset_id], key=lambda a: a.name):
                group_box = world_to_group[world.correct_name(area.in_dark_aether)]
                check = QtWidgets.QCheckBox(group_box)
                check.setText(area.name)
                check.area_location = AreaLocation(world.world_asset_id, area.area_asset_id)
                check.stateChanged.connect(functools.partial(_on_check_area, check))
                group_box.vertical_layout.addWidget(check)
                checks_for_area[area.area_asset_id] = check

        return checks_for_world, checks_for_area

    def _update_area_list(self, areas_to_check: FrozenSet[AreaLocation],
                          invert_check: bool,
                          location_for_world: Dict[str, QtWidgets.QCheckBox],
                          location_for_area: Dict[int, QtWidgets.QCheckBox],
                          ):
        self._during_batch_check_update = True
        for world in self.game_description.world_list.worlds:
            for is_dark_world in dark_world_flags(world):
                all_areas = True
                no_areas = True
                areas = [area for area in world.areas if area.in_dark_aether == is_dark_world]
                correct_name = world.correct_name(is_dark_world)
                if correct_name not in location_for_world:
                    continue

                for area in areas:
                    if area.area_asset_id in location_for_area:
                        is_checked = AreaLocation(world.world_asset_id, area.area_asset_id) in areas_to_check
                        if invert_check:
                            is_checked = not is_checked

                        if is_checked:
                            no_areas = False
                        else:
                            all_areas = False
                        location_for_area[area.area_asset_id].setChecked(is_checked)
                if all_areas:
                    location_for_world[correct_name].setCheckState(Qt.Checked)
                elif no_areas:
                    location_for_world[correct_name].setCheckState(Qt.Unchecked)
                else:
                    location_for_world[correct_name].setCheckState(Qt.PartiallyChecked)
        self._during_batch_check_update = False

    # Elevator
    def _create_check_for_source_elevator(self, location: Teleporter):
        area = self.game_description.world_list.area_by_area_location(location.area_location)
        name = elevator_distributor.CUSTOM_NAMES_FOR_ELEVATORS.get(area.area_asset_id)
        if name is None:
            name = self.game_description.world_list.area_name(area)

        check = QtWidgets.QCheckBox(self.elevators_source_group)
        check.setText(name)
        check.area_location = location
        check.stateChanged.connect(functools.partial(self._on_elevator_source_check_changed, location))
        return check

    def _create_source_elevators(self):
        row = 0

        custom_weights = {}
        if self.game_enum == RandovaniaGame.PRIME2:
            custom_weights = {
                2252328306: 0,  # Great Temple
                1119434212: 1,  # Agon Wastes
                1039999561: 2,  # Torvus Bog
                464164546: 3,  # Sanctuary Fortress
                1006255871: 5,  # Temple Grounds
            }
        locations = TeleporterList.areas_list(self.game_enum)
        areas: Dict[Teleporter, Area] = {
            loc: self.game_description.world_list.area_by_area_location(loc.area_location)
            for loc in locations
        }
        checks: Dict[Teleporter, QtWidgets.QCheckBox] = {
            loc: self._create_check_for_source_elevator(loc) for loc in locations
        }
        self._elevator_source_for_location = copy.copy(checks)
        self._elevator_source_destination = {}

        for location in sorted(locations,
                               key=lambda loc: (custom_weights.get(loc.world_asset_id, 0),
                                                checks[loc].text())):
            if location not in checks:
                continue

            self.elevators_source_layout.addWidget(checks.pop(location), row, 1)

            other_locations = [
                node.default_connection
                for node in areas[location].nodes
                if isinstance(node, TeleporterNode) and node.teleporter_instance_id == location.instance_id
            ]
            assert len(other_locations) == 1
            teleporters_in_target = [
                Teleporter(other_locations[0].world_asset_id,
                           other_locations[0].area_asset_id,
                           node.teleporter_instance_id)
                for node in self.game_description.world_list.area_by_area_location(other_locations[0]).nodes
                if isinstance(node, TeleporterNode)
            ]
            assert teleporters_in_target
            other_loc = teleporters_in_target[0]

            self._elevator_source_destination[location] = None

            if other_loc in checks:
                self.elevators_source_layout.addWidget(checks.pop(other_loc), row, 2)
                self._elevator_source_destination[location] = other_loc

            row += 1

    def setup_elevator_elements(self):
        for value in iterate_enum(TeleporterShuffleMode):
            self.elevators_combo.addItem(value.long_name, value)
        self.elevators_combo.currentIndexChanged.connect(self._update_elevator_mode)
        self.skip_final_bosses_check.stateChanged.connect(self._update_require_final_bosses)
        self.elevators_allow_unvisited_names_check.stateChanged.connect(self._update_allow_unvisited_names)

        # Elevator Source
        self._create_source_elevators()

        # Elevator Target
        self._elevator_target_for_world, self._elevator_target_for_area = self._create_area_list_selection(
            self.elevators_target_group,
            self.elevators_target_layout,
            TeleporterTargetList.areas_list(self.game_enum),
            self._on_elevator_target_check_changed,
        )

        if self.game_enum == RandovaniaGame.PRIME3:
            self.patches_tab_widget.setTabText(self.patches_tab_widget.indexOf(self.elevator_tab),
                                               "Teleporters")
            self.elevators_description_label.setText(
                self.elevators_description_label.text().replace("elevator", "teleporter")
            )

    def _update_elevator_mode(self):
        with self._editor as editor:
            editor.layout_configuration_elevators = dataclasses.replace(
                editor.layout_configuration_elevators,
                mode=self.elevators_combo.currentData(),
            )

    def _update_require_final_bosses(self, checked: int):
        with self._editor as editor:
            editor.layout_configuration_elevators = dataclasses.replace(
                editor.layout_configuration_elevators,
                skip_final_bosses=bool(checked),
            )

    def _update_allow_unvisited_names(self, checked: int):
        with self._editor as editor:
            editor.layout_configuration_elevators = dataclasses.replace(
                editor.layout_configuration_elevators,
                allow_unvisited_room_names=bool(checked),
            )

    def _on_elevator_source_check_changed(self, location: Teleporter, checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_elevators
            editor.layout_configuration_elevators = dataclasses.replace(
                config,
                excluded_teleporters=config.excluded_teleporters.ensure_has_location(location, not checked),
            )

    def _on_elevator_target_check_changed(self, world_areas, checked: bool):
        with self._editor as editor:
            config = editor.layout_configuration_elevators
            editor.layout_configuration_elevators = dataclasses.replace(
                config,
                excluded_targets=config.excluded_targets.ensure_has_locations(world_areas, not checked),
            )

    def on_preset_changed_elevators(self, preset: Preset):
        config = preset.configuration

        set_combo_with_value(self.elevators_combo, config.elevators.mode)
        can_shuffle_target = config.elevators.mode not in (TeleporterShuffleMode.VANILLA,
                                                           TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
                                                           TeleporterShuffleMode.TWO_WAY_UNCHECKED)
        static_areas = set(
            teleporter.area_location
            for teleporter in config.elevators.static_teleporters.keys()
        )

        for origin, destination in self._elevator_source_destination.items():
            origin_check = self._elevator_source_for_location[origin]
            dest_check = self._elevator_source_for_location.get(destination)

            origin_check.setEnabled(not config.elevators.is_vanilla and origin not in static_areas)
            origin_check.setChecked(origin not in config.elevators.excluded_teleporters.locations)

            origin_check.setToolTip("The destination for this teleporter is locked due to other settings."
                                    if origin in static_areas else "")

            if dest_check is None:
                if not can_shuffle_target:
                    origin_check.setEnabled(False)
                continue

            dest_check.setEnabled(can_shuffle_target)
            if can_shuffle_target:
                dest_check.setChecked(destination not in config.elevators.excluded_teleporters.locations)
            else:
                dest_check.setChecked(origin_check.isChecked())

        self.elevators_target_group.setEnabled(config.elevators.has_shuffled_target)
        self.skip_final_bosses_check.setChecked(config.elevators.skip_final_bosses)
        self.elevators_allow_unvisited_names_check.setChecked(config.elevators.allow_unvisited_room_names)
        self._update_area_list(
            config.elevators.excluded_targets.locations,
            True,
            self._elevator_target_for_world,
            self._elevator_target_for_area,
        )

    # Starting Area
    def setup_starting_area_elements(self):
        self._starting_location_for_world, self._starting_location_for_area = self._create_area_list_selection(
            self.starting_locations_contents,
            self.starting_locations_layout,
            StartingLocationList.areas_list(self.game_enum),
            self._on_starting_area_check_changed,
        )
        self.starting_area_quick_fill_ship.clicked.connect(self._starting_location_on_select_ship)
        self.starting_area_quick_fill_save_station.clicked.connect(self._starting_location_on_select_save_station)

    def _on_starting_area_check_changed(self, world_areas, checked: bool):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                editor.configuration.starting_location.ensure_has_locations(world_areas, checked)
            )

    def _starting_location_on_select_ship(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                LocationList.with_elements([self.game_description.starting_location], self.game_enum)
            )

    def _starting_location_on_select_save_station(self):
        world_list = self.game_description.world_list
        save_stations = [world_list.node_to_area_location(node)
                         for node in world_list.all_nodes if node.name == "Save Station"]

        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location",
                LocationList.with_elements(save_stations, self.game_enum)
            )

    def on_preset_changed_starting_area(self, preset: Preset):
        self._update_area_list(
            preset.configuration.starting_location.locations,
            False,
            self._starting_location_for_world,
            self._starting_location_for_area,
        )

    # Location Pool
    def setup_location_pool_elements(self):
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
            group_box = QGroupBox(self.excluded_locations_area_contents)
            group_box.setTitle(world_name)
            vertical_layout = QVBoxLayout(group_box)
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
