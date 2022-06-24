import functools
from typing import Callable

from PySide6 import QtWidgets, QtCore

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

    def areas_by_world_from_locations(self, all_area_locations: list[AreaIdentifier]
                                      ) -> tuple[list[World], dict[str, list[Area]]]:
        world_list = self.game_description.world_list
        worlds = []
        areas_by_world = {}

        for identifier in all_area_locations:
            world, area = world_list.world_and_area_by_area_identifier(identifier)

            if world.name not in areas_by_world:
                worlds.append(world)
                areas_by_world[world.name] = []

            areas_by_world[world.name].append(area)

        return worlds, areas_by_world

    def create_area_list_selection(
            self,
            parent: QtWidgets.QWidget, layout: QtWidgets.QGridLayout,
            all_area_locations: list[AreaIdentifier],
            on_check: Callable[[list[AreaIdentifier], bool], None],
    ) -> tuple[dict[str, QtWidgets.QCheckBox], dict[AreaIdentifier, QtWidgets.QCheckBox]]:
        """"""
        world_to_group: dict[str, QtWidgets.QGroupBox] = {}
        checks_for_world = {}
        checks_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox] = {}

        worlds, areas_by_world = self.areas_by_world_from_locations(all_area_locations)
        worlds.sort(key=lambda it: it.name)

        def _on_check_area(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                on_check([c.area_location], c.isChecked())

        def _on_check_world(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                world_list = self.game_description.world_list
                w = world_list.world_with_name(c.world_name)
                world_areas = [
                    identifier
                    for a in w.areas if c.is_dark_world == a.in_dark_aether
                    if (identifier := world_list.identifier_for_area(a)) in checks_for_area
                ]
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
                check.area_location = self.game_description.world_list.identifier_for_area(area)
                check.stateChanged.connect(functools.partial(_on_check_area, check))
                group_box.vertical_layout.addWidget(check)
                checks_for_area[check.area_location] = check

        return checks_for_world, checks_for_area

    def update_area_list(self, areas_to_check: list[AreaIdentifier],
                         invert_check: bool,
                         location_for_world: dict[str, QtWidgets.QCheckBox],
                         location_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox],
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
                    identifier = self.game_description.world_list.identifier_for_area(area)
                    if identifier in location_for_area:
                        is_checked = identifier in areas_to_check
                        if invert_check:
                            is_checked = not is_checked

                        if is_checked:
                            no_areas = False
                        else:
                            all_areas = False

                        location_for_area[identifier].setChecked(is_checked)

                if all_areas:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Checked)
                elif no_areas:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Unchecked)
                else:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.PartiallyChecked)

        self.during_batch_check_update = False
