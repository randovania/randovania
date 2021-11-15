import functools
from typing import List, Callable, FrozenSet, Dict

from PySide2 import QtWidgets, QtCore

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.world import World
from randovania.patching.prime import elevators


def dark_world_flags(world: World):
    yield False
    if world.dark_name is not None:
        yield True


class AreaListHelper:
    game_description: GameDescription
    during_batch_check_update: bool

    def areas_by_world_from_locations(self, all_area_locations: List[AreaIdentifier]
                                      ) -> tuple[list[World], dict[str, list[Area]]]:
        world_list = self.game_description.world_list
        worlds = []
        areas_by_world = {}

        for location in all_area_locations:
            world = world_list.world_by_area_location(location)
            if world.name not in areas_by_world:
                worlds.append(world)
                areas_by_world[world.name] = []

            areas_by_world[world.name].append(world.area_by_identifier(location))

        return worlds, areas_by_world

    def create_area_list_selection(self, parent: QtWidgets.QWidget, layout: QtWidgets.QGridLayout,
                                   all_area_locations: List[AreaIdentifier],
                                   on_check: Callable[[List[AreaIdentifier], bool], None],
                                   ):
        world_to_group = {}
        checks_for_world = {}
        checks_for_area: dict[tuple[str, str], QtWidgets.QCheckBox] = {}

        worlds, areas_by_world = self.areas_by_world_from_locations(all_area_locations)
        worlds.sort(key=lambda it: it.name)

        def _on_check_area(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                on_check([c.area_location], c.isChecked())

        def _on_check_world(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                world_list = self.game_description.world_list
                w = world_list.world_with_name(c.world_name)
                world_areas = [world_list.area_to_area_location(a)
                               for a in w.areas if c.is_dark_world == a.in_dark_aether
                               if (w.name, a.name) in checks_for_area]
                on_check(world_areas, c.isChecked())

        for row, world in enumerate(worlds):
            for column, is_dark_world in enumerate(dark_world_flags(world)):
                group_box = QtWidgets.QGroupBox(parent)
                world_check = QtWidgets.QCheckBox(group_box)
                world_check.setText(world.correct_name(is_dark_world))
                world_check.world_name = world.name
                world_check.is_dark_world = is_dark_world
                world_check.stateChanged.connect(functools.partial(_on_check_world, world_check))
                world_check.setTristate(True)
                vertical_layout = QtWidgets.QVBoxLayout(group_box)
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
            for area in sorted(areas_by_world[world.name], key=lambda a: a.name):
                assert isinstance(area, Area)
                group_box = world_to_group[world.correct_name(area.in_dark_aether)]
                check = QtWidgets.QCheckBox(group_box)
                check.setText(elevators.get_elevator_name_or_default(
                    self.game_description.game, world.name, area.name, area.name
                ))
                check.area_location = AreaIdentifier(world.name, area.name)
                check.stateChanged.connect(functools.partial(_on_check_area, check))
                group_box.vertical_layout.addWidget(check)
                checks_for_area[(world.name, area.name)] = check

        return checks_for_world, checks_for_area

    def update_area_list(self, areas_to_check: FrozenSet[AreaIdentifier],
                         invert_check: bool,
                         location_for_world: Dict[str, QtWidgets.QCheckBox],
                         location_for_area: Dict[tuple[str, str], QtWidgets.QCheckBox],
                         ):
        self.during_batch_check_update = True

        for world in self.game_description.world_list.worlds:
            for is_dark_world in dark_world_flags(world):
                all_areas = True
                no_areas = True
                areas = [area for area in world.areas if area.in_dark_aether == is_dark_world]
                correct_name = world.correct_name(is_dark_world)
                if correct_name not in location_for_world:
                    continue

                for area in areas:
                    if (world.name, area.name) in location_for_area:
                        is_checked = AreaIdentifier(world.name, area.name) in areas_to_check
                        if invert_check:
                            is_checked = not is_checked

                        if is_checked:
                            no_areas = False
                        else:
                            all_areas = False
                        location_for_area[(world.name, area.name)].setChecked(is_checked)
                if all_areas:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Checked)
                elif no_areas:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Unchecked)
                else:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.PartiallyChecked)

        self.during_batch_check_update = False
