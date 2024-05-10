from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from randovania.game_description.db.area import Area
from randovania.games.common import elevators

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription


def dark_name_flags(region: Region):
    yield False
    if region.dark_name is not None:
        yield True


class NodeListHelper:
    game_description: GameDescription
    during_batch_check_update: bool

    def nodes_by_areas_by_region_from_locations(
        self, all_node_locations: list[NodeIdentifier]
    ) -> tuple[list[Region], dict[str, list[Area]], dict[AreaIdentifier, list[Node]]]:
        region_list = self.game_description.region_list
        regions = []
        areas_by_region = {}
        nodes_by_area = {}

        for identifier in all_node_locations:
            region, area = region_list.region_and_area_by_area_identifier(identifier.area_identifier)

            if region.name not in areas_by_region:
                regions.append(region)
                areas_by_region[region.name] = []

            if area not in areas_by_region[region.name]:
                areas_by_region[region.name].append(area)
            if identifier.area_identifier not in nodes_by_area:
                nodes_by_area[identifier.area_identifier] = []
            nodes_by_area[identifier.area_identifier].append(area.node_with_name(identifier.node))

        return regions, areas_by_region, nodes_by_area

    def create_node_list_selection(
        self,
        parent: QtWidgets.QWidget,
        layout: QtWidgets.QGridLayout,
        all_node_locations: list[NodeIdentifier],
        on_check: Callable[[list[NodeIdentifier], bool], None],
    ) -> tuple[
        dict[str, QtWidgets.QCheckBox],
        dict[AreaIdentifier, QtWidgets.QCheckBox],
        dict[NodeIdentifier, QtWidgets.QCheckBox],
    ]:
        """"""
        region_to_group: dict[str, QtWidgets.QGroupBox] = {}
        checks_for_region = {}
        checks_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox] = {}
        checks_for_node: dict[NodeIdentifier, QtWidgets.QCheckBox] = {}

        regions, areas_by_region, nodes_by_area = self.nodes_by_areas_by_region_from_locations(all_node_locations)
        regions.sort(key=lambda it: it.name)

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

        def _on_check_region(c: QtWidgets.QCheckBox, _):
            if not self.during_batch_check_update:
                region_list = self.game_description.region_list
                areas = areas_by_region[c.region_name]
                new_node_list = [
                    identifier
                    for area in areas
                    if c.use_dark_name == area.in_dark_aether
                    for node in nodes_by_area[region_list.identifier_for_area(area)]
                    if (identifier := node.identifier) in checks_for_node
                ]

                on_check(new_node_list, c.isChecked())

        for row, region in enumerate(regions):
            for column, use_dark_name in enumerate(dark_name_flags(region)):
                group_box = QtWidgets.QGroupBox(parent)
                region_check = QtWidgets.QCheckBox(group_box)
                region_check.setText(region.correct_name(use_dark_name).replace("&", "&&"))
                region_check.region_name = region.name
                region_check.use_dark_name = use_dark_name
                region_check.stateChanged.connect(functools.partial(_on_check_region, region_check))
                region_check.setTristate(True)
                vertical_layout = QtWidgets.QVBoxLayout(group_box)
                vertical_layout.setContentsMargins(8, 4, 8, 4)
                vertical_layout.setSpacing(2)
                vertical_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
                separator = QtWidgets.QFrame()
                separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
                group_box.vertical_layout = vertical_layout
                group_box.vertical_layout.addWidget(region_check)
                group_box.vertical_layout.addWidget(separator)

                region_to_group[region.correct_name(use_dark_name)] = group_box
                layout.addWidget(group_box, row, column)
                checks_for_region[region.correct_name(use_dark_name)] = region_check

        for region in regions:
            for area in sorted(areas_by_region[region.name], key=lambda a: a.name):
                assert isinstance(area, Area)
                group_box = region_to_group[region.correct_name(area.in_dark_aether)]
                area_check = QtWidgets.QCheckBox(group_box)
                area_check.area_location = self.game_description.region_list.identifier_for_area(area)
                area_text = area.name
                if len(nodes_by_area[area_check.area_location]) == 1:
                    first_node = nodes_by_area[area_check.area_location][0]
                    area_text = elevators.get_elevator_name_or_default(
                        self.game_description, first_node.identifier, area_text
                    )
                area_text = area_text.replace("&", "&&")
                area_check.setText(area_text)
                area_check.stateChanged.connect(functools.partial(_on_check_area, area_check))
                area_check.setTristate(True)
                group_box.vertical_layout.addWidget(area_check)
                checks_for_area[area_check.area_location] = area_check

                for node in nodes_by_area[area_check.area_location]:
                    node_check = QtWidgets.QCheckBox(group_box)
                    node_check.setText(
                        elevators.get_elevator_name_or_default(
                            self.game_description, node.identifier, node.name
                        ).replace("&", "&&")
                    )
                    node_check.node_location = node.identifier
                    node_check.stateChanged.connect(functools.partial(_on_check_node, node_check))

                    if len(nodes_by_area[area_check.area_location]) > 1:
                        node_inner_layout = QtWidgets.QHBoxLayout()
                        node_inner_layout.setSpacing(2)
                        spacer = QtWidgets.QSpacerItem(
                            20, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum
                        )
                        node_inner_layout.addItem(spacer)
                        node_inner_layout.addWidget(node_check)
                        group_box.vertical_layout.addLayout(node_inner_layout)
                    else:
                        node_check.setVisible(False)
                    checks_for_node[node_check.node_location] = node_check

        return checks_for_region, checks_for_area, checks_for_node

    def update_node_list(
        self,
        nodes_to_check: Sequence[NodeIdentifier],
        invert_check: bool,
        location_for_region: dict[str, QtWidgets.QCheckBox],
        location_for_area: dict[AreaIdentifier, QtWidgets.QCheckBox],
        location_for_nodes: dict[NodeIdentifier, QtWidgets.QCheckBox],
    ):
        self.during_batch_check_update = True

        for region in self.game_description.region_list.regions:
            for use_dark_name in dark_name_flags(region):
                all_areas = True
                no_areas = True
                areas = [
                    area
                    for area in region.areas
                    if area.in_dark_aether == use_dark_name
                    and self.game_description.region_list.identifier_for_area(area) in location_for_area
                ]
                correct_name = region.correct_name(use_dark_name)
                if correct_name not in location_for_region:
                    continue

                for area in areas:
                    area_identifier = self.game_description.region_list.identifier_for_area(area)
                    all_nodes = True
                    no_nodes = True
                    starting_locations_for_area = [
                        k for k, v in location_for_nodes.items() if k.area_identifier == area_identifier
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
                            location_for_area[area_identifier].setCheckState(QtCore.Qt.CheckState.Checked)
                            no_areas = False
                        elif no_nodes:
                            location_for_area[area_identifier].setCheckState(QtCore.Qt.CheckState.Unchecked)
                            all_areas = False
                        else:
                            no_areas = False
                            all_areas = False
                            location_for_area[area_identifier].setCheckState(QtCore.Qt.CheckState.PartiallyChecked)

                if all_areas:
                    location_for_region[correct_name].setCheckState(QtCore.Qt.CheckState.Checked)
                elif no_areas:
                    location_for_region[correct_name].setCheckState(QtCore.Qt.CheckState.Unchecked)
                else:
                    location_for_region[correct_name].setCheckState(QtCore.Qt.CheckState.PartiallyChecked)

        self.during_batch_check_update = False
