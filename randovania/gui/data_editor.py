import json
from pathlib import Path
from typing import Dict, Optional

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QRadioButton, QGridLayout, QDialog, QFileDialog

from randovania.game_description import data_reader, data_writer
from randovania.game_description.area import Area
from randovania.game_description.node import Node, DockNode, TeleporterNode
from randovania.game_description.world import World
from randovania.gui.common_qt_lib import set_default_window_icon
from randovania.gui.connections_editor import ConnectionsEditor
from randovania.gui.connections_visualizer import ConnectionsVisualizer
from randovania.gui.data_editor_ui import Ui_DataEditorWindow


class DataEditorWindow(QMainWindow, Ui_DataEditorWindow):
    edit_mode: bool
    selected_node_button: QRadioButton = None
    radio_button_to_node: Dict[QRadioButton, Node] = {}
    _area_with_displayed_connections: Optional[Area] = None
    _previous_selected_node: Optional[Node] = None
    _connections_visualizer: Optional[ConnectionsVisualizer] = None

    def __init__(self, data: dict, edit_mode: bool):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)
        self.edit_mode = edit_mode

        self.world_selector_box.currentIndexChanged.connect(self.on_select_world)
        self.area_selector_box.currentIndexChanged.connect(self.on_select_area)
        self.other_node_connection_edit_button.clicked.connect(self._open_edit_connection)
        self.save_database_button.clicked.connect(self._save_database)
        self.verticalLayout.setAlignment(Qt.AlignTop)
        self.alternatives_grid_layout = QGridLayout(self.other_node_alternatives_contents)

        self.game_description = data_reader.decode_data(data, False)

        self.resource_database = self.game_description.resource_database
        self.world_list = self.game_description.world_list

        for world in sorted(self.world_list.worlds, key=lambda x: x.name):
            self.world_selector_box.addItem(world.name, userData=world)

        self.update_edit_mode()

    def on_select_world(self):
        self.area_selector_box.clear()
        for area in sorted(self.current_world.areas, key=lambda x: x.name):
            self.area_selector_box.addItem(area.name, userData=area)
        self.area_selector_box.setEnabled(True)

    def on_select_area(self):
        for node in self.radio_button_to_node.keys():
            node.deleteLater()

        self.radio_button_to_node.clear()

        current_area = self.current_area
        if not current_area:
            return

        is_first = True
        for node in sorted(current_area.nodes, key=lambda x: x.name):
            button = QRadioButton(self.points_of_interest_group)
            button.setText(node.name)
            self.radio_button_to_node[button] = node
            if is_first:
                self.selected_node_button = button

            button.setChecked(is_first)
            button.toggled.connect(self.on_select_node)
            is_first = False
            self.verticalLayout.addWidget(button)

        self.update_selected_node()

    def on_select_node(self, active):
        if active:
            self.selected_node_button = self.sender()
            self.update_selected_node()

    def update_selected_node(self):
        node = self.current_node
        assert node is not None

        self.node_heals_check.setChecked(node.heal)

        if isinstance(node, DockNode):
            other = self.world_list.resolve_dock_connection(self.current_world, node.default_connection)
            msg = "{} to {}".format(node.default_dock_weakness.name, self.world_list.node_name(other))

        elif node.is_resource_node:
            msg = "Provides {}".format(node.resource())

        elif isinstance(node, TeleporterNode):
            other = self.world_list.resolve_teleporter_connection(node.default_connection)
            msg = "Connects to {}".format(self.world_list.node_name(other, with_world=True))
        else:
            msg = ""

        self.node_name_label.setText(node.name)
        self.node_details_label.setText(msg)
        self.update_other_node_connection()

        self._previous_selected_node = node

    def update_other_node_connection(self):
        """
        Fills self.other_node_connection_combo for the current area, excluding the currently selected node.
        :return:
        """
        current_node = self.current_node
        assert current_node is not None

        # Calculates which node should be selected
        selected_node = None
        if self._area_with_displayed_connections == self.current_area:
            selected_node = self.current_connection_node
        if selected_node is current_node:
            selected_node = self._previous_selected_node

        #
        self._area_with_displayed_connections = self.current_area

        if self.other_node_connection_combo.count() > 0:
            self.other_node_connection_combo.currentIndexChanged.disconnect(self.update_connections)
            self.other_node_connection_combo.clear()

        for node in sorted(self.current_area.nodes, key=lambda x: x.name):
            if node is not current_node:
                self.other_node_connection_combo.addItem(node.name, userData=node)
                if node is selected_node:
                    self.other_node_connection_combo.setCurrentIndex(self.other_node_connection_combo.count() - 1)

        if self.other_node_connection_combo.count() > 0:
            self.other_node_connection_combo.currentIndexChanged.connect(self.update_connections)
            self.other_node_connection_combo.setEnabled(True)
            self.other_node_connection_edit_button.setEnabled(True)
        else:
            self.other_node_connection_combo.setEnabled(False)
            self.other_node_connection_edit_button.setEnabled(False)

        self.update_connections()

    def update_connections(self):
        current_node = self.current_node
        current_connection_node = self.current_connection_node

        assert current_node is not None
        assert current_node != current_connection_node

        if self._connections_visualizer is not None:
            self._connections_visualizer.deleteLater()
            self._connections_visualizer = None

        if current_connection_node is None:
            assert len(self.current_area.nodes) == 1
            return

        requirement_set = self.current_area.connections[self.current_node].get(self.current_connection_node)
        self._connections_visualizer = ConnectionsVisualizer(
            self.other_node_alternatives_contents,
            self.alternatives_grid_layout,
            self.resource_database,
            requirement_set,
            False
        )

    def _open_edit_connection(self):
        from_node = self.current_node
        target_node = self.current_connection_node

        assert from_node is not None
        assert target_node is not None

        requirement_set = self.current_area.connections[from_node].get(target_node)
        editor = ConnectionsEditor(self, self.resource_database, requirement_set)
        result = editor.exec_()
        if result == QDialog.Accepted:
            self.current_area.connections[from_node][target_node] = editor.final_requirement_set
            if self.current_area.connections[from_node][target_node] is None:
                del self.current_area.connections[from_node][target_node]
            self.update_connections()

    def _save_database(self):
        open_result = QFileDialog.getSaveFileName(self, caption="Select a Randovania database path.", filter="*.json")
        if not open_result or open_result == ("", ""):
            return None

        data = data_writer.write_game_description(self.game_description)
        with Path(open_result[0]).open("w") as open_file:
            json.dump(data, open_file, indent=4)

    def update_edit_mode(self):
        self.delete_node_button.setVisible(self.edit_mode)
        self.new_node_button.setVisible(self.edit_mode)
        self.save_database_button.setVisible(self.edit_mode)
        self.other_node_connection_edit_button.setVisible(self.edit_mode)
        self.node_heals_check.setEnabled(self.edit_mode and False)
        self.delete_node_button.setEnabled(False)
        self.new_node_button.setEnabled(False)


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
