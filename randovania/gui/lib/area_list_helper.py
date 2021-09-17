import functools
from typing import List, Callable, FrozenSet, Dict

from PySide2 import QtWidgets, QtCore

from randovania.games.prime import elevators
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.world import World


def dark_world_flags(world: World):
    yield False
    if world.dark_name is not None:
        yield True


class AreaListHelper:
    game_description: GameDescription
    during_batch_check_update: bool

    def areas_by_world_from_locations(self, all_area_locations: List[AreaLocation]):
        worlds = []
        areas_by_world = {}

        for location in all_area_locations:
            world = self.game_description.world_list.world_by_asset_id(location.world_asset_id)
            if world.world_asset_id not in areas_by_world:
                worlds.append(world)
                areas_by_world[world.world_asset_id] = []

            areas_by_world[world.world_asset_id].append(world.area_by_asset_id(location.area_asset_id))

        return worlds, areas_by_world

    def create_area_list_selection(self, parent: QtWidgets.QWidget, layout: QtWidgets.QGridLayout,
                                   all_area_locations: List[AreaLocation],
                                   on_check: Callable[[List[AreaLocation], bool], None],
                                   ):
        world_to_group = {}
        checks_for_world = {}
        checks_for_area = {}

        worlds, areas_by_world = self.areas_by_world_from_locations(all_area_locations)
        worlds.sort(key=lambda it: it.name)

        def _on_check_area(c, _):
            if not self.during_batch_check_update:
                on_check([c.area_location], c.isChecked())

        def _on_check_world(c, _):
            if not self.during_batch_check_update:
                world_list = self.game_description.world_list
                w = world_list.world_by_asset_id(c.world_asset_id)
                world_areas = [world_list.area_to_area_location(a)
                               for a in w.areas if c.is_dark_world == a.in_dark_aether
                               if a.area_asset_id in checks_for_area]
                on_check(world_areas, c.isChecked())

        for row, world in enumerate(worlds):
            for column, is_dark_world in enumerate(dark_world_flags(world)):
                group_box = QtWidgets.QGroupBox(parent)
                world_check = QtWidgets.QCheckBox(group_box)
                world_check.setText(world.correct_name(is_dark_world))
                world_check.world_asset_id = world.world_asset_id
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
            for area in sorted(areas_by_world[world.world_asset_id], key=lambda a: a.name):
                group_box = world_to_group[world.correct_name(area.in_dark_aether)]
                check = QtWidgets.QCheckBox(group_box)
                check.setText(elevators.get_elevator_name_or_default(self.game_description.game, area.area_asset_id, area.name))
                check.area_location = AreaLocation(world.world_asset_id, area.area_asset_id)
                check.stateChanged.connect(functools.partial(_on_check_area, check))
                group_box.vertical_layout.addWidget(check)
                checks_for_area[area.area_asset_id] = check

        return checks_for_world, checks_for_area

    def update_area_list(self, areas_to_check: FrozenSet[AreaLocation],
                         invert_check: bool,
                         location_for_world: Dict[str, QtWidgets.QCheckBox],
                         location_for_area: Dict[int, QtWidgets.QCheckBox],
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
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Checked)
                elif no_areas:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Unchecked)
                else:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.PartiallyChecked)

        self.during_batch_check_update = False
