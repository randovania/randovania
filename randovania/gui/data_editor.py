import dataclasses
import json
import re
from pathlib import Path
from typing import Dict, Optional

from PySide2 import QtGui
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QRadioButton, QGridLayout, QDialog, QFileDialog, QInputDialog, QMessageBox
from qasync import asyncSlot

from randovania.game_description import data_reader, data_writer, pretty_print, default_database
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import Node, DockNode, TeleporterNode, GenericNode
from randovania.game_description.requirements import Requirement
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.games import default_data
from randovania.gui.dialog.connections_editor import ConnectionsEditor
from randovania.gui.dialog.node_details_popup import NodeDetailsPopup
from randovania.gui.generated.data_editor_ui import Ui_DataEditorWindow
from randovania.gui.lib import async_dialog
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.connections_visualizer import ConnectionsVisualizer


class DataEditorWindow(QMainWindow, Ui_DataEditorWindow):
    edit_mode: bool
    selected_node_button: QRadioButton = None
    radio_button_to_node: Dict[QRadioButton, Node]
    _area_with_displayed_connections: Optional[Area] = None
    _previous_selected_node: Optional[Node] = None
    _connections_visualizer: Optional[ConnectionsVisualizer] = None
    _edit_popup: Optional[QDialog] = None

    def __init__(self, data: dict, data_path: Optional[Path], is_internal: bool, edit_mode: bool):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._is_internal = is_internal
        self._data_path = data_path
        self._last_data = data
        self.edit_mode = edit_mode
        self.radio_button_to_node = {}

        self.world_selector_box.currentIndexChanged.connect(self.on_select_world)
        self.area_selector_box.currentIndexChanged.connect(self.on_select_area)
        self.node_details_label.linkActivated.connect(self._on_click_link_to_other_node)
        self.node_heals_check.stateChanged.connect(self.on_node_heals_check)
        self.area_spawn_check.stateChanged.connect(self.on_area_spawn_check)
        self.node_edit_button.clicked.connect(self.on_node_edit_button)
        self.other_node_connection_edit_button.clicked.connect(self._open_edit_connection)

        self.save_database_button.setEnabled(data_path is not None)
        if self._is_internal:
            self.save_database_button.clicked.connect(self._save_as_internal_database)
        else:
            self.save_database_button.clicked.connect(self._prompt_save_database)

        self.new_node_button.clicked.connect(self._create_new_node)
        self.delete_node_button.clicked.connect(self._remove_node)
        self.verticalLayout.setAlignment(Qt.AlignTop)
        self.alternatives_grid_layout = QGridLayout(self.other_node_alternatives_contents)

        world_reader, self.game_description = data_reader.decode_data_with_world_reader(data)
        self.generic_index = world_reader.generic_index

        self.resource_database = self.game_description.resource_database
        self.world_list = self.game_description.world_list

        for world in sorted(self.world_list.worlds, key=lambda x: x.name):
            name = "{0.name} ({0.dark_name})".format(world) if world.dark_name else world.name
            self.world_selector_box.addItem(name, userData=world)

        self.update_edit_mode()

    @classmethod
    def open_internal_data(cls, game: RandovaniaGame, edit_mode: bool) -> "DataEditorWindow":
        default_data.read_json_then_binary.cache_clear()
        path, data = default_data.read_json_then_binary(game)
        if path.suffix == ".bin":
            path = None
        return DataEditorWindow(data, path, True, edit_mode)

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self._check_for_edit_dialog():
            event.ignore()
        else:
            data = data_writer.write_game_description(self.game_description)
            if data != self._last_data:
                user_response = QMessageBox.warning(self, "Unsaved changes",
                                                    "You have unsaved changes. Do you want to close and discard?",
                                                    QMessageBox.Yes | QMessageBox.No,
                                                    QMessageBox.No)
                if user_response == QMessageBox.No:
                    return event.ignore()
            super().closeEvent(event)

    def on_select_world(self):
        self.area_selector_box.clear()
        for area in sorted(self.current_world.areas, key=lambda x: x.name):
            if area.name.startswith("!!"):
                continue
            self.area_selector_box.addItem(area.name, userData=area)
        self.area_selector_box.setEnabled(True)

    def on_select_area(self):
        for node in self.radio_button_to_node.keys():
            node.deleteLater()

        self.radio_button_to_node.clear()

        current_area = self.current_area
        if not current_area:
            self.new_node_button.setEnabled(False)
            self.delete_node_button.setEnabled(False)
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

        self.new_node_button.setEnabled(True)
        self.delete_node_button.setEnabled(len(current_area.nodes) > 1)

        self.update_selected_node()

    def on_select_node(self, active):
        if active:
            self.selected_node_button = self.sender()
            self.update_selected_node()

    def focus_on_world(self, world_name: str):
        world = self.world_list.world_with_name(world_name)
        self.world_selector_box.setCurrentIndex(self.world_selector_box.findData(world))

    def focus_on_area(self, area_name: str):
        self.area_selector_box.setCurrentIndex(self.area_selector_box.findText(area_name))

    def _on_click_link_to_other_node(self, link: str):
        world_name, area_name, node_name = None, None, None

        info = re.match(r"^node://([^/]+)/([^/]+)/(.+)$", link)
        if info:
            world_name, area_name, node_name = info.group(1, 2, 3)
        else:
            info = re.match(r"^area://([^/]+)/([^/]+)$", link)
            world_name, area_name = info.group(1, 2)

        if world_name is not None and area_name is not None:
            self.focus_on_world(world_name)
            self.focus_on_area(area_name)
            if node_name is None and self.current_area.default_node_index is not None:
                node_name = self.current_area.nodes[self.current_area.default_node_index].name
            
            for radio_button in self.radio_button_to_node.keys():
                if radio_button.text() == node_name:
                    radio_button.setChecked(True)

    def on_node_heals_check(self, state: int):
        old_node = self.current_node
        assert old_node is not None

        new_node = dataclasses.replace(old_node, heal=bool(state))
        self.replace_node_with(self.current_area, old_node, new_node)

    def on_area_spawn_check(self, state: int):
        state = bool(state)
        if not state:
            return

        object.__setattr__(self.current_area, "default_node_index", self.current_area.nodes.index(self.current_node))
        self.area_spawn_check.setEnabled(False)

    def replace_node_with(self, area: Area, old_node: Node, new_node: Node):
        if old_node == new_node:
            return

        def sub(n: Node):
            return new_node if n == old_node else n

        area_node_list = area.nodes
        for i, node in enumerate(area_node_list):
            if node == old_node:
                area_node_list[i] = new_node

        new_connections = {
            sub(source_node): {
                sub(target_node): requirements
                for target_node, requirements in connection.items()
            }
            for source_node, connection in area.connections.items()
        }
        area.connections.clear()
        area.connections.update(new_connections)
        self.game_description.world_list.refresh_node_cache()

        if area == self.current_area:
            radio = next(key for key, value in self.radio_button_to_node.items() if value == old_node)
            radio.setText(new_node.name)
            self.radio_button_to_node[radio] = new_node
            self.update_selected_node()

    def _check_for_edit_dialog(self) -> bool:
        """
        If an edit popup exists, raises it and returns True.
        Otherwise, just return False.
        :return:
        """
        if self._edit_popup is not None:
            self._edit_popup.raise_()
            return True
        else:
            return False

    async def _execute_edit_dialog(self, dialog: QDialog):
        self._edit_popup = dialog
        try:
            result = await async_dialog.execute_dialog(self._edit_popup)
            return result == QDialog.Accepted
        finally:
            self._edit_popup = None

    @asyncSlot()
    async def on_node_edit_button(self):
        if self._check_for_edit_dialog():
            return

        area = self.current_area
        node_edit_popup = NodeDetailsPopup(self.game_description, self.current_node)
        if await self._execute_edit_dialog(node_edit_popup):
            try:
                new_node = node_edit_popup.create_new_node()
            except ValueError as e:
                await async_dialog.warning(self, "Error in new node", str(e))
                return
            self.replace_node_with(area, node_edit_popup.node, new_node)

    def update_selected_node(self):
        node = self.current_node
        assert node is not None

        self.node_heals_check.setChecked(node.heal)
        is_default_spawn = self.current_area.default_node_index == self.current_area.nodes.index(node)
        self.area_spawn_check.setChecked(is_default_spawn)
        self.area_spawn_check.setEnabled(self.edit_mode and not is_default_spawn)

        msg = pretty_print.pretty_print_node_type(node, self.world_list)
        if isinstance(node, DockNode):
            try:
                other = self.world_list.resolve_dock_connection(self.current_world, node.default_connection)
                msg = "{} to <a href=\"node://{}\">{}</a>".format(
                    node.default_dock_weakness.name,
                    self.world_list.node_name(other, with_world=True),
                    self.world_list.node_name(other)
                )
            except IndexError:
                pass

        elif isinstance(node, TeleporterNode):
            other = self.world_list.area_by_area_location(node.default_connection)
            name = self.world_list.area_name(other, separator="/", distinguish_dark_aether=False)
            pretty_name = msg.replace("Teleporter to ", "")
            msg = f'Teleporter to <a href="area://{name}">{pretty_name}</a>'

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

        requirement = self.current_area.connections[self.current_node].get(self.current_connection_node,
                                                                           Requirement.impossible())
        self._connections_visualizer = ConnectionsVisualizer(
            self.other_node_alternatives_contents,
            self.alternatives_grid_layout,
            self.resource_database,
            requirement,
            False
        )

    @asyncSlot()
    async def _open_edit_connection(self):
        if self._check_for_edit_dialog():
            return

        from_node = self.current_node
        target_node = self.current_connection_node
        assert from_node is not None
        assert target_node is not None

        requirement = self.current_area.connections[from_node].get(target_node, Requirement.impossible())
        editor = ConnectionsEditor(self, self.resource_database, requirement)
        if await self._execute_edit_dialog(editor):
            self._apply_edit_connections(from_node, target_node, editor.final_requirement)

    def _apply_edit_connections(self, from_node: Node, target_node: Node,
                                requirement: Optional[Requirement]):

        current_connections = self.current_area.connections[from_node]
        self.current_area.connections[from_node][target_node] = requirement
        if self.current_area.connections[from_node][target_node] is None:
            del self.current_area.connections[from_node][target_node]

        self.current_area.connections[from_node] = {
            node: current_connections[node]
            for node in self.current_area.nodes
            if node in current_connections
        }
        self.update_connections()

    def _prompt_save_database(self):
        open_result = QFileDialog.getSaveFileName(self, caption="Select a Randovania database path.", filter="*.json")
        if not open_result or open_result == ("", ""):
            return
        self._save_database(Path(open_result[0]))

    def _save_database(self, path: Path):
        data = data_writer.write_game_description(self.game_description)
        if self._is_internal:
            path.with_suffix("").mkdir(exist_ok=True)
            data_writer.write_as_split_files(data, path.with_suffix(""))
        else:
            with path.open("w") as open_file:
                json.dump(data, open_file, indent=4)
        self._last_data = data

    def _save_as_internal_database(self):
        self._save_database(self._data_path)
        pretty_print.write_human_readable_game(self.game_description, self._data_path.with_suffix(""))
        default_database.game_description_for.cache_clear()

    def _create_new_node(self):
        node_name, did_confirm = QInputDialog.getText(self, "New Node", "Insert node name:")
        if not did_confirm or node_name == "":
            return

        if self.current_area.node_with_name(node_name) is not None:
            QMessageBox.warning(self,
                                "New Node",
                                "A node named '{}' already exists.".format(node_name))
            return

        self._do_create_node(node_name)

    def _do_create_node(self, node_name: str):
        self.generic_index += 1
        new_node = GenericNode(node_name, False, None, self.generic_index)
        self.current_area.nodes.append(new_node)
        self.current_area.connections[new_node] = {}
        self.game_description.world_list.refresh_node_cache()

        self.on_select_area()

    def _remove_node(self):
        if self._check_for_edit_dialog():
            return

        current_node = self.current_node

        if not isinstance(current_node, GenericNode):
            QMessageBox.warning(self, "Delete Node", "Can only remove Generic Nodes")
            return

        user_response = QMessageBox.warning(
            self,
            "Delete Node",
            "Are you sure you want to delete the node '{}'?".format(current_node.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if user_response != QMessageBox.Yes:
            return

        for other_nodes in self.current_area.connections.values():
            other_nodes.pop(current_node, None)

        self.current_area.remove_node(current_node)
        self.game_description.world_list.refresh_node_cache()
        self.on_select_area()

    def update_edit_mode(self):
        self.delete_node_button.setVisible(self.edit_mode)
        self.new_node_button.setVisible(self.edit_mode)
        self.save_database_button.setVisible(self.edit_mode)
        self.other_node_connection_edit_button.setVisible(self.edit_mode)
        self.node_heals_check.setEnabled(self.edit_mode)
        self.area_spawn_check.setEnabled(self.edit_mode and self.area_spawn_check.isEnabled())
        self.node_edit_button.setVisible(self.edit_mode)

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
