from typing import Dict, Optional, List, Iterable

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QRadioButton, QWidget, QLabel, QGroupBox, QVBoxLayout

from randovania.game_description.data_reader import WorldReader, read_resource_database, read_dock_weakness_database
from randovania.game_description.world import World
from randovania.game_description.area import Area
from randovania.game_description.node import Node, DockNode, TeleporterNode
from randovania.game_description.requirements import RequirementList, IndividualRequirement, RequirementSet
from randovania.gui.data_editor_ui import Ui_DataEditorWindow


def _sort_alternative(alternative: RequirementList) -> Iterable[IndividualRequirement]:
    return sorted(alternative.values())


class DataEditorWindow(QMainWindow, Ui_DataEditorWindow):
    selected_node_button: QRadioButton = None
    radio_button_to_node: Dict[QRadioButton, Node] = {}
    connection_widgets: List[QWidget] = []

    def __init__(self, data: dict):
        super().__init__()
        self.setupUi(self)
        self.world_selector_box.currentIndexChanged.connect(self.on_select_world)
        self.area_selector_box.currentIndexChanged.connect(self.on_select_area)
        self.other_node_connection_combo.currentIndexChanged.connect(self.update_connections)
        self.verticalLayout.setAlignment(Qt.AlignTop)

        resource_database = read_resource_database(data["resource_database"])
        dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)

        world_reader = WorldReader(resource_database, dock_weakness_database, False)
        self.worlds = world_reader.read_world_list(data["worlds"])

        for world in sorted(self.worlds, key=lambda x: x.name):
            self.world_selector_box.addItem(world.name, userData=world)

    def on_select_world(self):
        self.area_selector_box.clear()
        for area in sorted(self.current_world.areas, key=lambda x: x.name):
            self.area_selector_box.addItem(area.name, userData=area)
        self.area_selector_box.setEnabled(True)

    def on_select_area(self):
        for node in self.radio_button_to_node.keys():
            node.deleteLater()

        self.radio_button_to_node.clear()
        self.other_node_connection_combo.clear()

        current_area = self.current_area
        if not current_area:
            self.other_node_connection_combo.setEnabled(False)
            return

        self.other_node_connection_combo.setEnabled(True)

        is_first = True
        for node in sorted(current_area.nodes, key=lambda x: x.name):
            button = QRadioButton(self.scroll_area_widget_contents)
            button.toggled.connect(self.on_select_node)
            button.setText(node.name)
            self.radio_button_to_node[button] = node
            button.setChecked(is_first)
            is_first = False
            self.verticalLayout.addWidget(button)
            self.other_node_connection_combo.addItem(node.name, userData=node)

    def on_select_node(self, active):
        if active:
            self.selected_node_button = self.sender()
            node = self.current_node
            assert node is not None

            self.node_heals_check.setChecked(node.heal)

            if isinstance(node, DockNode):
                msg = "{} to {} #{}".format(
                    node.default_dock_weakness.name,
                    node.default_connection.area_asset_id,
                    node.default_connection.dock_index)
            elif node.is_resource_node:
                msg = "Provides {}".format(node.resource())
            elif isinstance(node, TeleporterNode):
                msg = "Connects to {} at {}".format(
                    node.default_connection.area_asset_id,
                    node.default_connection.world_asset_id)
            else:
                msg = ""

            self.node_details_label.setText(msg)
            self.update_connections()

    def _add_box_with_labels(self, index: int, labels: Iterable[str]):
        group_box = QGroupBox(self.other_node_alternatives_contents)
        self.connection_widgets.append(group_box)
        self.other_node_alternatives_contents.layout()

        num_columns = 2
        self.gridLayout_3.addWidget(group_box, index // num_columns, index % num_columns)

        vertical_layout = QVBoxLayout(group_box)
        vertical_layout.setContentsMargins(11, 11, 11, 11)
        vertical_layout.setSpacing(6)

        for text in labels:
            label = QLabel(group_box)
            label.setText(text)
            vertical_layout.addWidget(label)
            self.connection_widgets.append(label)

    def update_connections(self):
        current_node = self.current_node
        current_connection_node = self.current_connection_node

        for widget in self.connection_widgets:
            widget.deleteLater()
        self.connection_widgets.clear()

        if current_node and current_connection_node and current_node != current_connection_node:
            requirement_set = self.current_area.connections[self.current_node].get(self.current_connection_node)

            if requirement_set == RequirementSet.impossible() or requirement_set is None:
                self._add_box_with_labels(0, ["Impossible to Reach"])
            else:
                for i, alternative in enumerate(requirement_set.alternatives):
                    if alternative.items:
                        contents = (individual_requirement.pretty_text
                                    for individual_requirement in _sort_alternative(alternative))
                    else:
                        contents = ["No Requirement"]
                    self._add_box_with_labels(i, contents)

        else:
            self._add_box_with_labels(0, [
                "Connection to self is impossible."
            ])

    @property
    def current_world(self) -> World:
        return self.world_selector_box.currentData()

    @property
    def current_area(self) -> Area:
        return self.area_selector_box.currentData()

    @property
    def current_node(self) -> Optional[Node]:
        return self.radio_button_to_node.get(self.selected_node_button)

    @property
    def current_connection_node(self) -> Node:
        return self.other_node_connection_combo.currentData()
