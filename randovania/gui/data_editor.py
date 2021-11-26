import dataclasses
import json
import re
from pathlib import Path
from typing import Dict, Optional

from PySide2 import QtGui, QtWidgets, QtCore
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QRadioButton, QGridLayout, QDialog, QFileDialog, QInputDialog, QMessageBox
from qasync import asyncSlot

from randovania.game_description import data_reader, data_writer, pretty_print, default_database, integrity_check
from randovania.game_description.editor import Editor
from randovania.game_description.requirements import Requirement
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import Node, DockNode, TeleporterNode, GenericNode, NodeLocation
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.world import World
from randovania.games import default_data
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.connections_editor import ConnectionsEditor
from randovania.gui.dialog.node_details_popup import NodeDetailsPopup
from randovania.gui.docks.resource_database_editor import ResourceDatabaseEditor
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

        self.setCentralWidget(None)
        # self.points_of_interest_dock.hide()
        # self.node_info_dock.hide()
        self.splitDockWidget(self.points_of_interest_dock, self.area_view_dock, Qt.Horizontal)
        self.splitDockWidget(self.area_view_dock, self.node_info_dock, Qt.Horizontal)

        # self.spin_min_x = QtWidgets.QSpinBox(super().centralWidget())
        # self.spin_min_y = QtWidgets.QSpinBox(super().centralWidget())
        # self.spin_max_x = QtWidgets.QSpinBox(super().centralWidget())
        # self.spin_max_y = QtWidgets.QSpinBox(super().centralWidget())
        # for i, it in enumerate([self.spin_min_x, self.spin_min_y, self.spin_max_x, self.spin_max_y]):
        #     it.setMaximum(99999)
        #     la = QtWidgets.QLabel(super().centralWidget())
        #     la.setText(["min_x", "min_y", "max_x", "max_y"][i])
        #     self.gridLayout_2.addWidget(la)
        #     self.gridLayout_2.addWidget(it)
        #     it.valueChanged.connect(self._on_image_spin_update)

        self.world_selector_box.currentIndexChanged.connect(self.on_select_world)
        self.area_selector_box.currentIndexChanged.connect(self.on_select_area)
        self.node_details_label.linkActivated.connect(self._on_click_link_to_other_node)
        self.node_heals_check.stateChanged.connect(self.on_node_heals_check)
        self.area_spawn_check.stateChanged.connect(self.on_area_spawn_check)
        self.node_edit_button.clicked.connect(self.on_node_edit_button)
        self.other_node_connection_edit_button.clicked.connect(self._open_edit_connection)
        self.area_view_canvas.CreateNodeRequest.connect(self._create_new_node)
        self.area_view_canvas.CreateDockRequest.connect(self._create_new_dock)
        self.area_view_canvas.MoveNodeRequest.connect(self._move_node)
        self.area_view_canvas.SelectNodeRequest.connect(self.focus_on_node)
        self.area_view_canvas.SelectAreaRequest.connect(self.focus_on_area)
        self.area_view_canvas.SelectConnectionsRequest.connect(self.focus_on_connection)

        self.save_database_button.setEnabled(data_path is not None)
        if self._is_internal:
            self.save_database_button.clicked.connect(self._save_as_internal_database)
        else:
            self.save_database_button.clicked.connect(self._prompt_save_database)

        self.rename_area_button.clicked.connect(self._rename_area)
        self.new_node_button.clicked.connect(self._create_new_node_no_location)
        self.delete_node_button.clicked.connect(self._remove_node)
        self.points_of_interest_layout.setAlignment(Qt.AlignTop)
        self.nodes_scroll_layout.setAlignment(Qt.AlignTop)
        self.alternatives_grid_layout = QGridLayout(self.other_node_alternatives_contents)

        world_reader, self.game_description = data_reader.decode_data_with_world_reader(data)
        self.editor = Editor(self.game_description)
        self.generic_index = world_reader.generic_index
        self.resource_database = self.game_description.resource_database
        self.world_list = self.game_description.world_list

        self.area_view_canvas.select_game(self.game_description.game)

        self.resource_editor = ResourceDatabaseEditor(self, self.game_description.resource_database)
        self.resource_editor.setFeatures(self.resource_editor.features() & ~QtWidgets.QDockWidget.DockWidgetClosable)
        self.tabifyDockWidget(self.points_of_interest_dock, self.resource_editor)
        self.points_of_interest_dock.raise_()

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
        world = self.current_world
        for area in sorted(world.areas, key=lambda x: x.name):
            if area.name.startswith("!!"):
                continue
            self.area_selector_box.addItem(area.name, userData=area)
        self.area_selector_box.setEnabled(True)

        self.area_view_canvas.select_world(world)

        self.on_select_area()

        # for it in [self.spin_min_x, self.spin_min_y, self.spin_max_x, self.spin_max_y]:
        #     it.valueChanged.disconnect(self._on_image_spin_update)
        #
        # self.spin_min_x.setValue(world.extra["map_min_x"])
        # self.spin_min_y.setValue(world.extra["map_min_y"])
        # self.spin_max_x.setValue(world.extra["map_max_x"])
        # self.spin_max_y.setValue(world.extra["map_max_y"])
        #
        # for it in [self.spin_min_x, self.spin_min_y, self.spin_max_x, self.spin_max_y]:
        #     it.valueChanged.connect(self._on_image_spin_update)

    # def _on_image_spin_update(self):
    #     world = self.current_world
    #     world.extra["map_min_x"] = self.spin_min_x.value()
    #     world.extra["map_min_y"] = self.spin_min_y.value()
    #     world.extra["map_max_x"] = self.spin_max_x.value()
    #     world.extra["map_max_y"] = self.spin_max_y.value()
    #     self.area_view_canvas.select_world(world)

    def on_select_area(self, select_node: Optional[Node] = None):
        for node in self.radio_button_to_node.keys():
            node.deleteLater()

        self.radio_button_to_node.clear()

        current_area = self.current_area
        self.area_view_canvas.select_area(current_area)

        if not current_area:
            self.new_node_button.setEnabled(False)
            self.delete_node_button.setEnabled(False)
            return

        is_first = True
        for node in sorted(current_area.nodes, key=lambda x: x.name):
            button = QRadioButton(self.nodes_scroll_contents)
            button.setText(node.name)
            self.radio_button_to_node[button] = node
            if is_first or select_node is node:
                self.selected_node_button = button
                button.setChecked(True)
            else:
                button.setChecked(False)
            button.toggled.connect(self.on_select_node)
            is_first = False
            self.nodes_scroll_layout.addWidget(button)

        self.new_node_button.setEnabled(True)
        self.delete_node_button.setEnabled(len(current_area.nodes) > 1)

        self.update_selected_node()

    def on_select_node(self, active):
        if active:
            self.selected_node_button = self.sender()
            self.update_selected_node()

    def focus_on_world_by_name(self, world_name: str):
        world = self.world_list.world_with_name(world_name)
        self.focus_on_world(world)

    def focus_on_world(self, world: World):
        self.world_selector_box.setCurrentIndex(self.world_selector_box.findData(world))

    def focus_on_area_by_name(self, area_name: str):
        self.area_selector_box.setCurrentIndex(self.area_selector_box.findText(area_name))

    def focus_on_area(self, area: Area):
        self.area_selector_box.setCurrentIndex(self.area_selector_box.findData(area))

    def focus_on_node(self, node: Node):
        for radio, other_node in self.radio_button_to_node.items():
            if other_node == node:
                radio.setChecked(True)
        self.update_selected_node()

    def focus_on_connection(self, other: Node):
        self.other_node_connection_combo.setCurrentIndex(self.other_node_connection_combo.findData(other))

    def _on_click_link_to_other_node(self, link: str):
        world_name, area_name, node_name = None, None, None

        info = re.match(r"^node://([^/]+)/([^/]+)/(.+)$", link)
        if info:
            world_name, area_name, node_name = info.group(1, 2, 3)
        else:
            info = re.match(r"^area://([^/]+)/([^/]+)$", link)
            world_name, area_name = info.group(1, 2)

        if world_name is not None and area_name is not None:
            self.focus_on_world_by_name(world_name)
            self.focus_on_area_by_name(area_name)
            if node_name is None:
                node_name = self.current_area.default_node

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

        object.__setattr__(self.current_area, "default_node", self.current_node.name)
        self.area_spawn_check.setEnabled(False)

    def replace_node_with(self, area: Area, old_node: Node, new_node: Node):
        if old_node == new_node:
            return

        self.editor.replace_node(area, old_node, new_node)

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
        is_default_spawn = self.current_area.default_node == node.name
        self.area_spawn_check.setChecked(is_default_spawn)
        self.area_spawn_check.setEnabled(self.edit_mode and not is_default_spawn)
        self.area_view_canvas.highlight_node(node)

        try:
            msg = pretty_print.pretty_print_node_type(node, self.world_list)
        except Exception as e:
            msg = f"Unable to describe node: {e}"

        if isinstance(node, DockNode):
            try:
                other = self.world_list.node_by_identifier(node.default_connection)
                msg = "{} to <a href=\"node://{}\">{}</a>".format(
                    node.default_dock_weakness.name,
                    self.world_list.node_name(other, with_world=True),
                    self.world_list.node_name(other)
                )
            except IndexError:
                pass

        elif isinstance(node, TeleporterNode):
            try:
                other = self.world_list.area_by_area_location(node.default_connection)
                name = self.world_list.area_name(other, separator="/", distinguish_dark_aether=False)
                pretty_name = msg.replace("Teleporter to ", "")
                msg = f'Teleporter to <a href="area://{name}">{pretty_name}</a>'
            except Exception as e:
                msg = f'Teleporter to {node.default_connection} (Unknown area due to {e}).'

        self.node_name_label.setText(node.name)
        self.node_details_label.setText(msg)
        self.node_description_label.setText(node.description)
        self.update_other_node_connection()

        for button, source_node in self.radio_button_to_node.items():
            button.setStyleSheet(
                "font-weight: bold;"
                if node in self.current_area.connections[source_node]
                else ""
            )

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
            if self.other_node_connection_combo.isEnabled():
                self.other_node_connection_combo.currentIndexChanged.disconnect(self.update_connections)
            self.other_node_connection_combo.clear()

        for node in sorted(self.current_area.nodes, key=lambda x: x.name):
            if node is current_node:
                continue

            if not self.edit_mode and node not in self.current_area.connections[current_node]:
                continue

            self.other_node_connection_combo.addItem(node.name, userData=node)
            if node is selected_node:
                self.other_node_connection_combo.setCurrentIndex(self.other_node_connection_combo.count() - 1)

        if self.other_node_connection_combo.count() > 0:
            self.other_node_connection_combo.currentIndexChanged.connect(self.update_connections)
            self.other_node_connection_combo.setEnabled(True)
            self.other_node_connection_edit_button.setEnabled(True)
        else:
            self.other_node_connection_combo.setEnabled(False)
            self.other_node_connection_combo.addItem("No connections")
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
            assert len(self.current_area.nodes) == 1 or not self.edit_mode
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
            self.editor.edit_connections(self.current_area, from_node, target_node, editor.final_requirement)
            self.update_connections()

    def _prompt_save_database(self):
        open_result = QFileDialog.getSaveFileName(self, caption="Select a Randovania database path.", filter="*.json")
        if not open_result or open_result == ("", ""):
            return
        self._save_database(Path(open_result[0]))

    def _save_database(self, path: Path) -> bool:
        errors = integrity_check.find_database_errors(self.game_description)
        if errors:
            message = "Database has the following errors:\n\n" + "\n".join(errors)

            options = QMessageBox.Ok
            if self.game_description.game.data.experimental:
                options = QMessageBox.Yes | QMessageBox.No
                message += "\n\nIgnore?"

            user_response = QMessageBox.critical(
                self, "Integrity Check",
                message,
                options,
                QMessageBox.No
            )
            if user_response != QMessageBox.Yes:
                return False

        data = data_writer.write_game_description(self.game_description)
        if self._is_internal:
            path.with_suffix("").mkdir(exist_ok=True)
            data_writer.write_as_split_files(data, path.with_suffix(""))
        else:
            with path.open("w") as open_file:
                json.dump(data, open_file, indent=4)
        self._last_data = data
        return True

    def _save_as_internal_database(self):
        if self._save_database(self._data_path):
            pretty_print.write_human_readable_game(self.game_description, self._data_path.with_suffix(""))
            default_database.game_description_for.cache_clear()

    def _rename_area(self):
        new_name, did_confirm = QInputDialog.getText(self, "New Name", "Insert area name:",
                                                     text=self.current_area.name)
        if not did_confirm or new_name == "" or new_name == self.current_area.name:
            return

        self.editor.rename_area(self.current_area, new_name)
        self.on_select_world()
        self.focus_on_area_by_name(new_name)

    def _move_node(self, node: Node, location: NodeLocation):
        area = self.current_area
        assert node in area.nodes
        self.replace_node_with(
            area,
            node,
            dataclasses.replace(node, location=location)
        )

    def _create_new_node(self, location: Optional[NodeLocation]):
        node_name, did_confirm = QInputDialog.getText(self, "New Node", "Insert node name:")
        if not did_confirm or node_name == "":
            return

        if self.current_area.node_with_name(node_name) is not None:
            QMessageBox.warning(self,
                                "New Node",
                                "A node named '{}' already exists.".format(node_name))
            return

        self._do_create_node(node_name, location)

    def _create_new_node_no_location(self):
        return self._create_new_node(None)

    def _do_create_node(self, node_name: str, location: Optional[NodeLocation]):
        self.generic_index += 1
        new_node = GenericNode(node_name, False, location, "", {}, self.generic_index)
        self.editor.add_node(self.current_area, new_node)
        self.on_select_area(new_node)

    def _create_new_dock(self, location: NodeLocation, target_area: Area):
        current_area = self.current_area

        i = 1
        while current_area.node_with_name(source_name := f"Door to {target_area.name} ({i})") is not None:
            i += 1

        i = 1
        while target_area.node_with_name(target_name := f"Door to {current_area.name} ({i})") is not None:
            i += 1

        dock_weakness = self.game_description.dock_weakness_database.default_weakness

        self.generic_index += 1
        new_node_this_area = DockNode(
            source_name, False, location, "", {}, self.generic_index,
            NodeIdentifier(self.world_list.identifier_for_area(target_area), target_name),
            dock_weakness[0],
            dock_weakness[1],
        )

        self.generic_index += 1
        new_node_other_area = DockNode(
            target_name, False, location, "", {}, self.generic_index,
            NodeIdentifier(self.world_list.identifier_for_area(current_area), source_name),
            dock_weakness[0],
            dock_weakness[1],
        )

        self.editor.add_node(current_area, new_node_this_area)
        self.editor.add_node(target_area, new_node_other_area)
        self.on_select_area(new_node_this_area)

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

        self.editor.remove_node(self.current_area, current_node)
        self.on_select_area()

    def update_edit_mode(self):
        self.rename_area_button.setVisible(self.edit_mode)
        self.delete_node_button.setVisible(self.edit_mode)
        self.new_node_button.setVisible(self.edit_mode)
        self.save_database_button.setVisible(self.edit_mode)
        self.other_node_connection_edit_button.setVisible(self.edit_mode)
        self.node_heals_check.setEnabled(self.edit_mode)
        self.area_spawn_check.setEnabled(self.edit_mode and self.area_spawn_check.isEnabled())
        self.node_edit_button.setVisible(self.edit_mode)
        self.resource_editor.set_allow_edits(self.edit_mode)
        self.area_view_canvas.set_edit_mode(self.edit_mode)

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
    def current_connection_node(self) -> Optional[Node]:
        return self.other_node_connection_combo.currentData()
