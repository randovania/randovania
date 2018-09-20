from typing import Dict, Optional, List, Iterable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QWidget, QLabel, QGroupBox, QVBoxLayout, QSizePolicy

from randovania.games.prime import binary_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.data_editor_ui import Ui_DataEditorWindow
from randovania.resolver.data_reader import WorldReader, read_resource_database, read_dock_weakness_database
from randovania.resolver.game_description import World, Area
from randovania.resolver.node import Node
from randovania.resolver.requirements import RequirementList, IndividualRequirement
from randovania.resolver.resources import DamageResourceInfo, SimpleResourceInfo


def _sort_alternative(alternative: RequirementList) -> Iterable[IndividualRequirement]:
    filtered = set()

    for individual in alternative:
        if isinstance(individual.resource, SimpleResourceInfo) and individual.resource.long_name == "Difficulty Level":
            filtered.add(individual)
            yield individual

    for individual in alternative:
        if isinstance(individual.resource, DamageResourceInfo):
            filtered.add(individual)
            yield individual

    for individual in sorted(alternative):
        if individual not in filtered:
            yield individual


class DataEditorWindow(QMainWindow, Ui_DataEditorWindow):
    selected_node_button: QRadioButton = None
    radio_button_to_node: Dict[QRadioButton, Node] = {}
    connection_widgets: List[QWidget] = []

    def __init__(self, main_window, background_processor: BackgroundTaskMixin):
        super().__init__()
        self.setupUi(self)
        self.worldSelectorBox.currentIndexChanged.connect(self.on_select_world)
        self.areaSelectorBox.currentIndexChanged.connect(self.on_select_area)
        self.otherNodeConnectionBox.currentIndexChanged.connect(self.update_connections)
        self.verticalLayout.setAlignment(Qt.AlignTop)

        self.nodeInfoBox.hide()
        data = binary_data.decode_default_prime2()

        resource_database = read_resource_database(data["resource_database"])
        dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)

        world_reader = WorldReader(resource_database,
                                   dock_weakness_database,
                                   [])
        self.worlds = world_reader.read_world_list(data["worlds"])

        for world in sorted(self.worlds, key=lambda x: x.name):
            self.worldSelectorBox.addItem(world.name, userData=world)

    def on_select_world(self):
        self.areaSelectorBox.clear()
        for area in sorted(self.current_world.areas, key=lambda x: x.name):
            self.areaSelectorBox.addItem(area.name, userData=area)
        self.areaSelectorBox.setEnabled(True)

    def on_select_area(self):
        for node in self.radio_button_to_node.keys():
            node.deleteLater()

        self.radio_button_to_node.clear()
        self.otherNodeConnectionBox.clear()

        current_area = self.current_area
        if not current_area:
            self.otherNodeConnectionBox.setEnabled(False)
            return

        self.otherNodeConnectionBox.setEnabled(True)

        is_first = True
        for node in sorted(current_area.nodes, key=lambda x: x.name):
            button = QRadioButton(self.pointOfInterestBox)
            button.toggled.connect(self.on_select_node)
            button.setText(node.name)
            self.radio_button_to_node[button] = node
            button.setChecked(is_first)
            is_first = False
            self.verticalLayout.addWidget(button)
            self.otherNodeConnectionBox.addItem(node.name, userData=node)

    def on_select_node(self, active):
        if active:
            self.selected_node_button = self.sender()
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
            requirement_set = self.current_area.connections[self.current_node][self.current_connection_node]

            for i, alternative in enumerate(requirement_set.alternatives):
                self._add_box_with_labels(
                    i,
                    (individual_requirement.pretty_text
                     for individual_requirement in _sort_alternative(alternative))
                )

        else:
            self._add_box_with_labels(0, [
                "Connection to self is impossible."
            ])

    @property
    def current_world(self) -> World:
        return self.worldSelectorBox.currentData()

    @property
    def current_area(self) -> Area:
        return self.areaSelectorBox.currentData()

    @property
    def current_node(self) -> Optional[Node]:
        return self.radio_button_to_node.get(self.selected_node_button)

    @property
    def current_connection_node(self) -> Node:
        return self.otherNodeConnectionBox.currentData()
