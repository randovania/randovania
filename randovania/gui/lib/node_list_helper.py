import functools
from typing import Callable, Sequence

from PySide6 import QtWidgets, QtCore

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import Node
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.world import World
from randovania.patching.prime import elevators

def dark_world_flags(world: World):
    yield False
    if world.dark_name is not None:
        yield True


class NodeListHelper:
    game_description: GameDescription
    during_batch_check_update: bool

    def nodes_by_areas_by_world_from_locations(self, all_node_locations: list[NodeIdentifier]
                                      ) -> tuple[list[World], dict[str, list[Area]], dict[AreaIdentifier, list[Node]]]:
        world_list = self.game_description.world_list
        worlds = []
        areas_by_world = {}
        nodes_by_area = {}

        for identifier in all_node_locations:
            world, area = world_list.world_and_area_by_area_identifier(identifier.area_identifier)

            if world.name not in areas_by_world:
                worlds.append(world)
                areas_by_world[world.name] = []

            if area not in areas_by_world[world.name]:
                areas_by_world[world.name].append(area)
            if identifier.area_identifier not in nodes_by_area:
                nodes_by_area[identifier.area_identifier] = []
            nodes_by_area[identifier.area_identifier].append(area.node_with_name(identifier.node_name))

        return worlds, areas_by_world, nodes_by_area

    def create_node_list_selection(
            self,
            parent: QtWidgets.QWidget, layout: QtWidgets.QGridLayout,
            all_node_locations: list[NodeIdentifier],
            on_check: Callable[[list[NodeIdentifier], bool], None],
    ) -> tuple[
            dict[str, QtWidgets.QCheckBox],
            dict[AreaIdentifier, QtWidgets.QCheckBox],
            dict[NodeIdentifier, QtWidgets.QCheckBox]
         ]:
        """"""
        world_to_group: dict[str, QtWidgets.QGroupBox] = {}
        checks_for_world = {}
        checks_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox] = {}
        checks_for_node: dict[NodeIdentifier, QtWidgets.QCheckBox] = {}

        worlds, areas_by_world, nodes_by_area = self.nodes_by_areas_by_world_from_locations(all_node_locations)
        worlds.sort(key=lambda it: it.name)
    
        def _on_check_node(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                on_check([c.node_location], c.isChecked())

        def _on_check_area(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                area_identifier = c.area_location
                new_node_list = [
                    identifier
                    for node in nodes_by_area[area_identifier]
                    if (identifier := node.identifier) in checks_for_node
                ]

                on_check(new_node_list, c.isChecked())

        def _on_check_world(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                world_list = self.game_description.world_list
                areas = areas_by_world[c.world_name]
                new_node_list = [
                    identifier
                    for area in areas if c.is_dark_world == area.in_dark_aether
                    for node in nodes_by_area[world_list.identifier_for_area(area)]
                    if (identifier := node.identifier) in checks_for_node
                ]

                on_check(new_node_list, c.isChecked())

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
                area_check = QtWidgets.QCheckBox(group_box)
                area_check.setText(elevators.get_elevator_name_or_default(
                    self.game_description.game, world.name, area.name, area.name
                ))
                area_check.area_location = self.game_description.world_list.identifier_for_area(area)
                area_check.stateChanged.connect(functools.partial(_on_check_area, area_check))
                area_check.setTristate(True)
                group_box.vertical_layout.addWidget(area_check)
                checks_for_area[area_check.area_location] = area_check

                for node in nodes_by_area[area_check.area_location]:
                    node_check = QtWidgets.QCheckBox(group_box)
                    node_check.setText(node.name)
                    node_check.node_location = node.identifier
                    node_check.stateChanged.connect(functools.partial(_on_check_node, node_check))

                    if len(nodes_by_area[area_check.area_location]) > 1:
                        node_inner_layout = QtWidgets.QHBoxLayout()
                        node_inner_layout.setSpacing(2)
                        spacer = QtWidgets.QSpacerItem(20, 20, 
                                                       QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
                        node_inner_layout.addItem(spacer)
                        node_inner_layout.addWidget(node_check)
                        group_box.vertical_layout.addLayout(node_inner_layout)
                    else:
                        node_check.setVisible(False)
                    checks_for_node[node_check.node_location] = node_check

        return checks_for_world, checks_for_area, checks_for_node

    def update_node_list(self, nodes_to_check: Sequence[NodeIdentifier],
                         invert_check: bool,
                         location_for_world: dict[str, QtWidgets.QCheckBox],
                         location_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox],
                         location_for_nodes: dict[NodeIdentifier, QtWidgets.QCheckBox],
                         ):
        self.during_batch_check_update = True

        for world in self.game_description.world_list.worlds:
            for is_dark_world in dark_world_flags(world):
                all_areas = True
                no_areas = True
                areas = [area for area in world.areas if area.in_dark_aether == is_dark_world and
                         self.game_description.world_list.identifier_for_area(area) in location_for_area]
                correct_name = world.correct_name(is_dark_world)
                if correct_name not in location_for_world:
                    continue

                for area in areas:
                    area_identifier = self.game_description.world_list.identifier_for_area(area)
                    all_nodes = True
                    no_nodes = True
                    starting_locations_for_area = [
                        k for k, v in location_for_nodes.items()
                        if k.area_identifier == area_identifier
                    ]
                    if len(starting_locations_for_area) != 0:
                        for node_identifier in starting_locations_for_area:
                            if node_identifier in location_for_nodes:
                                is_checked = node_identifier in nodes_to_check
                                if invert_check:
                                    is_checked = not is_checked
                                if is_checked:
                                    no_nodes = False
                                else:
                                    all_nodes = False
                                location_for_nodes[node_identifier].setChecked(is_checked)

                        if all_nodes:
                            location_for_area[area_identifier].setCheckState(QtCore.Qt.Checked)
                            no_areas = False
                        elif no_nodes:
                            location_for_area[area_identifier].setCheckState(QtCore.Qt.Unchecked)
                            all_areas = False
                        else:
                            no_areas = False
                            all_areas = False
                            location_for_area[area_identifier].setCheckState(QtCore.Qt.PartiallyChecked)

                if all_areas:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Checked)
                elif no_areas:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.Unchecked)
                else:
                    location_for_world[correct_name].setCheckState(QtCore.Qt.PartiallyChecked)

        self.during_batch_check_update = False
