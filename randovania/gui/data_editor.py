from __future__ import annotations

import dataclasses
import re
import typing
from pathlib import Path
from typing import TYPE_CHECKING, Self

import frozendict
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QMainWindow, QMessageBox, QRadioButton
from qasync import asyncSlot

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import (
    data_reader,
    data_writer,
    default_database,
    derived_nodes,
    integrity_check,
    pretty_print,
)
from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.node import GenericNode, Node, NodeContext, NodeLocation
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.editor import Editor
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games import default_data
from randovania.gui.dialog.area_details_popup import AreaDetailsPopup
from randovania.gui.dialog.connections_editor import ConnectionsEditor
from randovania.gui.dialog.node_details_popup import NodeDetailsPopup
from randovania.gui.docks.connection_filtering_widget import ConnectionFilteringWidget
from randovania.gui.docks.hint_feature_database_editor import HintFeatureDatabaseEditor
from randovania.gui.docks.resource_database_editor import ResourceDatabaseEditor
from randovania.gui.generated.data_editor_ui import Ui_DataEditorWindow
from randovania.gui.lib import async_dialog, signal_handling
from randovania.gui.lib.common_qt_lib import set_default_window_icon
from randovania.gui.lib.connections_visualizer import create_tree_items_for_requirement
from randovania.gui.lib.scroll_message_box import ScrollMessageBox
from randovania.lib import json_lib

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_info import ResourceInfo

SHOW_REGION_MIN_MAX_SPINNER = False


def _ui_patch_and_simplify(requirement: Requirement, context: NodeContext) -> Requirement:
    if isinstance(requirement, RequirementArrayBase):
        items = list(requirement.items)
        if isinstance(requirement, RequirementOr):
            remove = Requirement.impossible()
            solve = Requirement.trivial()
        else:
            remove = Requirement.trivial()
            solve = Requirement.impossible()

        items = [_ui_patch_and_simplify(it, context) for it in items]
        if solve in items:
            return solve
        items = [it for it in items if it != remove]
        return type(requirement)(items, comment=requirement.comment)

    elif isinstance(requirement, ResourceRequirement):
        return requirement.patch_requirements(1.0, context)

    elif isinstance(requirement, RequirementTemplate):
        result = requirement.template_requirement(context.database)
        patched = _ui_patch_and_simplify(result, context)
        if result != patched:
            return patched
        else:
            return requirement
    else:
        return requirement


class DataEditorWindow(QMainWindow, Ui_DataEditorWindow):
    game_description: GameDescription
    editor: Editor
    region_list: RegionList

    edit_mode: bool
    selected_node_button: QRadioButton | None = None
    radio_button_to_node: dict[QRadioButton, Node]
    _area_with_displayed_connections: Area | None = None
    _previous_selected_node: Node | None = None
    _edit_popup: QDialog | None = None
    _warning_dialogs_disabled = False
    _collection_for_filtering: ResourceCollection | None = None

    def __init__(self, data: dict, data_path: Path | None, is_internal: bool, edit_mode: bool):
        super().__init__()
        self.setupUi(self)
        set_default_window_icon(self)

        self._is_internal = is_internal
        self._data_path = data_path
        self._last_data = data
        self.edit_mode = edit_mode
        self.radio_button_to_node = {}

        self.setCentralWidget(None)  # type: ignore[arg-type]
        # self.points_of_interest_dock.hide()
        # self.node_info_dock.hide()
        self.splitDockWidget(self.points_of_interest_dock, self.area_view_dock, Qt.Orientation.Horizontal)
        self.splitDockWidget(self.area_view_dock, self.node_info_dock, Qt.Orientation.Horizontal)

        self.use_trick_filters_check = QtWidgets.QCheckBox("Apply trick filters", self.connections_group)
        self.use_trick_filters_check.setChecked(True)
        self.connections_group_layout.addWidget(self.use_trick_filters_check, 0, 2, 1, 1)
        self.use_trick_filters_check.setToolTip(
            "Hides connections based on trick level settings defined on the `Connection Filtering` tab, on the left."
        )

        if SHOW_REGION_MIN_MAX_SPINNER:
            area_border_body = QtWidgets.QWidget()

            area_border_dock = QtWidgets.QDockWidget(self)
            area_border_dock.setWidget(area_border_body)
            area_border_dock.setWindowTitle("Region min/max for image")

            layout = QtWidgets.QVBoxLayout(area_border_body)
            self.spin_min_x = QtWidgets.QSpinBox(area_border_body)
            self.spin_min_y = QtWidgets.QSpinBox(area_border_body)
            self.spin_max_x = QtWidgets.QSpinBox(area_border_body)
            self.spin_max_y = QtWidgets.QSpinBox(area_border_body)

            for i, it in enumerate([self.spin_min_x, self.spin_min_y, self.spin_max_x, self.spin_max_y]):
                it.setMaximum(99999)
                la = QtWidgets.QLabel(area_border_body)
                la.setText(["min_x", "min_y", "max_x", "max_y"][i])
                layout.addWidget(la)
                layout.addWidget(it)
                it.valueChanged.connect(self._on_image_spin_update)

            self.tabifyDockWidget(self.points_of_interest_dock, area_border_dock)

        self.region_selector_box.currentIndexChanged.connect(self.on_select_region)
        self.area_selector_box.currentIndexChanged.connect(self.on_select_area)
        self.node_details_label.linkActivated.connect(self._on_click_link_to_other_node)
        self.node_heals_check.stateChanged.connect(self.on_node_heals_check)
        self.area_spawn_check.stateChanged.connect(self.on_area_spawn_check)
        self.node_edit_button.clicked.connect(self.on_node_edit_button)
        self.other_node_connection_swap_button.clicked.connect(self._swap_selected_connection)
        self.other_node_connection_edit_button.clicked.connect(self._open_edit_connection)
        self.area_view_canvas.CreateNodeRequest.connect(self._create_new_node)
        self.area_view_canvas.CreateDockRequest.connect(self._create_new_dock)
        self.area_view_canvas.MoveNodeToAreaRequest.connect(self._move_dock_to_area)
        self.area_view_canvas.MoveNodeRequest.connect(self._move_node)
        self.area_view_canvas.SelectNodeRequest.connect(self.focus_on_node)
        self.area_view_canvas.SelectAreaRequest.connect(self.focus_on_area)
        self.area_view_canvas.SelectConnectionsRequest.connect(self.focus_on_connection)
        self.area_view_canvas.ReplaceConnectionsRequest.connect(self.replace_connection_with)
        self.area_view_canvas.UpdateSlider.connect(self.update_slider)

        self.save_database_button.setEnabled(data_path is not None)
        if self._is_internal:
            self.save_database_button.clicked.connect(self._save_as_internal_database)
        else:
            self.save_database_button.clicked.connect(self._prompt_save_database)

        self.edit_area_button.clicked.connect(self.on_area_edit_button)
        self.new_node_button.clicked.connect(self._create_new_node_no_location)
        self.delete_node_button.clicked.connect(self._remove_node)
        self.zoom_slider.valueChanged.connect(self._on_slider_changed)
        self.points_of_interest_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nodes_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.use_trick_filters_check.toggled.connect(self._on_filters_changed)

        _, self.original_game_description = data_reader.decode_data_with_region_reader(data)
        self.resource_database = self.original_game_description.resource_database
        self.hint_features = self.original_game_description.hint_feature_database

        self.update_game(self.original_game_description)

        self.resource_editor = ResourceDatabaseEditor(self, self.resource_database, self.region_list)
        self.resource_editor.setFeatures(
            self.resource_editor.features() & ~QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.tabifyDockWidget(self.points_of_interest_dock, self.resource_editor)

        self.hint_feature_editor = HintFeatureDatabaseEditor(self, self.hint_features)
        self.hint_feature_editor.setFeatures(
            self.hint_feature_editor.features() & ~QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.tabifyDockWidget(self.points_of_interest_dock, self.hint_feature_editor)

        self.connection_filters = ConnectionFilteringWidget(self, self.original_game_description)
        self.connection_filters.setFeatures(
            self.connection_filters.features() & ~QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.tabifyDockWidget(self.points_of_interest_dock, self.connection_filters)

        self.points_of_interest_dock.raise_()

        self.resource_editor.ResourceChanged.connect(self._on_resource_changed)
        self.connection_filters.FiltersUpdated.connect(self._on_filters_changed)

        if self.game_description.game in {
            RandovaniaGame.METROID_PRIME_ECHOES,
            RandovaniaGame.FACTORIO,
        }:
            self.area_view_dock.hide()

        self.zoom_slider.setTickInterval(1)

        self.update_edit_mode()
        self._on_filters_changed()

    def set_warning_dialogs_disabled(self, value: bool) -> None:
        self._warning_dialogs_disabled = value

    def update_game(self, game: GameDescription) -> None:
        current_region = self.current_region
        current_area = self.current_area
        current_node = self.current_node
        current_connection = self.current_connection_node

        self.game_description = game
        self.editor = Editor(self.game_description)
        self.region_list = self.game_description.region_list
        self.area_view_canvas.select_game(self.game_description.game)

        self.region_selector_box.clear()
        for region in sorted(self.region_list.regions, key=lambda x: x.name):
            name = f"{region.name} ({region.dark_name})" if region.dark_name else region.name
            self.region_selector_box.addItem(name, userData=region)

        if current_region:
            self.focus_on_region_by_name(current_region.name)
        if current_area:
            self.focus_on_area_by_name(current_area.name)
        if current_node:
            self.focus_on_node(current_node)
        if current_connection:
            self.focus_on_connection(current_connection)

    @classmethod
    def open_internal_data(cls, game: RandovaniaGame, edit_mode: bool) -> Self:
        default_data.read_json_then_binary.cache_clear()
        path: Path | None = None
        path, data = default_data.read_json_then_binary(game)
        if path.suffix == ".bin":
            path = None
        return cls(data, path, True, edit_mode)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._check_for_edit_dialog():
            event.ignore()
        else:
            if self.edit_mode:
                data = data_writer.write_game_description(self.game_description)
                if data != self._last_data:
                    if not self.prompt_unsaved_changes_warning():
                        return event.ignore()
            super().closeEvent(event)

    def prompt_unsaved_changes_warning(self) -> bool:
        """Return value: True, if user decided to discard"""
        if self._warning_dialogs_disabled:
            return True

        user_response = QMessageBox.warning(
            self,
            "Unsaved changes",
            "You have unsaved changes. Do you want to close and discard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return user_response == QMessageBox.StandardButton.Yes

    def on_select_region(self) -> None:
        self.area_selector_box.clear()
        region = self.current_region
        if region is None:
            return

        for area in sorted(region.areas, key=lambda x: x.name):
            if area.name.startswith("!!"):
                continue
            self.area_selector_box.addItem(area.name, userData=area)
        self.area_selector_box.setEnabled(True)

        self.area_view_canvas.select_region(region)

        self.on_select_area()

        if SHOW_REGION_MIN_MAX_SPINNER:
            for it in [self.spin_min_x, self.spin_min_y, self.spin_max_x, self.spin_max_y]:
                it.valueChanged.disconnect(self._on_image_spin_update)

            self.spin_min_x.setValue(region.extra["map_min_x"])
            self.spin_min_y.setValue(region.extra["map_min_y"])
            self.spin_max_x.setValue(region.extra["map_max_x"])
            self.spin_max_y.setValue(region.extra["map_max_y"])

            for it in [self.spin_min_x, self.spin_min_y, self.spin_max_x, self.spin_max_y]:
                it.valueChanged.connect(self._on_image_spin_update)

    def _on_image_spin_update(self) -> None:
        w = self.current_region
        if not isinstance(w.extra, dict) or isinstance(w.extra, frozendict.frozendict):
            object.__setattr__(w, "extra", dict(w.extra))
        w.extra["map_min_x"] = self.spin_min_x.value()
        w.extra["map_min_y"] = self.spin_min_y.value()
        w.extra["map_max_x"] = self.spin_max_x.value()
        w.extra["map_max_y"] = self.spin_max_y.value()
        self.area_view_canvas.select_region(w)

    def on_select_area(self, select_node: Node | None = None) -> None:
        for radio_node in self.radio_button_to_node.keys():
            radio_node.deleteLater()

        self.radio_button_to_node.clear()

        current_area = self.current_area
        self.area_view_canvas.select_area(current_area)

        if not current_area:
            self.new_node_button.setEnabled(False)
            self.delete_node_button.setEnabled(False)
            return

        is_first = True
        for node in sorted(current_area.actual_nodes, key=lambda x: x.name):
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

    def on_select_node(self, active: bool) -> None:
        if active:
            self.selected_node_button = typing.cast("QRadioButton", self.sender())
            self.update_selected_node()

    def focus_on_region_by_name(self, name: str) -> None:
        region = self.region_list.region_with_name(name)
        self.focus_on_region(region)

    def focus_on_region(self, region: Region) -> None:
        signal_handling.set_combo_with_value(self.region_selector_box, region)

    def focus_on_area_by_name(self, area_name: str) -> None:
        self.area_selector_box.setCurrentIndex(self.area_selector_box.findText(area_name))

    def focus_on_area(self, area: Area) -> None:
        signal_handling.set_combo_with_value(self.area_selector_box, area)

    def focus_on_node(self, node: Node) -> None:
        for radio, other_node in self.radio_button_to_node.items():
            if other_node == node:
                radio.setChecked(True)
        self.update_selected_node()

    def focus_on_connection(self, other: Node) -> None:
        signal_handling.set_combo_with_value(self.other_node_connection_combo, other)

    def _on_click_link_to_other_node(self, link: str) -> None:
        region_name, area_name, node_name = None, None, None

        info = re.match(r"^node://([^/]+)/([^/]+)/(.+)$", link)
        if info:
            region_name, area_name, node_name = info.group(1, 2, 3)
        else:
            info = re.match(r"^area://([^/]+)/([^/]+)$", link)
            if info:
                region_name, area_name = info.group(1, 2)

        if region_name is not None and area_name is not None:
            self.focus_on_region_by_name(region_name)
            self.focus_on_area_by_name(area_name)

            for radio_button in self.radio_button_to_node.keys():
                if radio_button.text() == node_name:
                    radio_button.setChecked(True)

    def on_node_heals_check(self, state: int) -> None:
        old_node = self.current_node
        assert old_node is not None

        new_node = dataclasses.replace(old_node, heal=bool(state))
        self.replace_node_with(self.current_area, old_node, new_node)

    def on_area_spawn_check(self, state: int) -> None:
        old_node = self.current_node
        assert old_node is not None
        new_node = dataclasses.replace(old_node, valid_starting_location=bool(state))
        self.replace_node_with(self.current_area, old_node, new_node)

    def replace_node_with(self, area: Area, old_node: Node, new_node: Node) -> None:
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

    async def _execute_edit_dialog(self, dialog: QDialog) -> bool:
        self._edit_popup = dialog
        try:
            result = await async_dialog.execute_dialog(self._edit_popup)
            return result == QDialog.DialogCode.Accepted
        finally:
            self._edit_popup = None

    @asyncSlot()
    async def on_node_edit_button(self) -> None:
        if self._check_for_edit_dialog():
            return

        area = self.current_area
        old_node = self.current_node
        if old_node not in area.nodes:
            raise ValueError("Current node is not part of the current area")

        node_edit_popup = NodeDetailsPopup(self.game_description, old_node)
        if await self._execute_edit_dialog(node_edit_popup):
            try:
                new_node = node_edit_popup.create_new_node()
            except ValueError as e:
                if not self._warning_dialogs_disabled:
                    await async_dialog.warning(self, "Error in new node", str(e))
                return
            self.replace_node_with(area, node_edit_popup.node, new_node)

            if isinstance(new_node, DockNode) and not hasattr(new_node, "lock_node"):
                lock_node = DockLockNode.create_from_dock(
                    new_node, self.editor.new_node_index(), self.resource_database
                )
                self.editor.add_node(area, lock_node)

    def update_selected_node(self) -> None:
        node = self.current_node
        self.node_info_group.setEnabled(node is not None)
        if node is None:
            self.node_name_label.setText("<missing node>")
            self.node_details_label.setText("")
            self.node_description_label.setText("")
            self.update_other_node_connection()
            return

        self.node_heals_check.setChecked(node.heal)

        is_area_spawn = node.valid_starting_location
        self.area_spawn_check.setChecked(is_area_spawn)

        self.area_view_canvas.highlight_node(node)

        try:
            msg = pretty_print.pretty_print_node_type(node, self.region_list, self.resource_database)
        except Exception as e:
            msg = f"Unable to describe node: {e}"

        if isinstance(node, DockNode):
            msg = f'{node.default_dock_weakness.name} to <a href="node://{node.default_connection.as_string}">{node.default_connection.node}</a>'
            if node.override_default_open_requirement is not None:
                msg += f"\n<br />Open Override: {node.override_default_open_requirement}"
            if node.override_default_lock_requirement is not None:
                msg += f"\n<br />Lock Override: {node.override_default_lock_requirement}"

        self.node_name_label.setText(node.name)
        self.node_details_label.setText(msg)
        self.node_description_label.setText(node.description)
        self.update_other_node_connection()

        for button, source_node in self.radio_button_to_node.items():
            button.setStyleSheet("font-weight: bold;" if node in self.current_area.connections[source_node] else "")

        self._previous_selected_node = node

    def update_other_node_connection(self) -> None:
        """
        Fills self.other_node_connection_combo for the current area, excluding the currently selected node.
        :return:
        """
        current_node = self.current_node
        if current_node is None:
            assert not self.current_area.nodes

        # Calculates which node should be selected
        selected_node = None
        if self._area_with_displayed_connections == self.current_area:
            selected_node = self.current_connection_node
        if selected_node is current_node:
            selected_node = self._previous_selected_node

        self._area_with_displayed_connections = self.current_area

        if self.other_node_connection_combo.count() > 0:
            if self.other_node_connection_combo.isEnabled():
                self.other_node_connection_combo.currentIndexChanged.disconnect(self.update_connections)
            self.other_node_connection_combo.clear()

        for node in sorted(self.current_area.actual_nodes, key=lambda x: x.name):
            if node is current_node:
                continue

            if not self.edit_mode and current_node and node not in self.current_area.connections[current_node]:
                continue

            self.other_node_connection_combo.addItem(node.name, userData=node)
            if node is selected_node:
                self.other_node_connection_combo.setCurrentIndex(self.other_node_connection_combo.count() - 1)

        if self.other_node_connection_combo.count() > 0:
            self.other_node_connection_combo.currentIndexChanged.connect(self.update_connections)
            self.other_node_connection_combo.setEnabled(True)
            self.other_node_connection_swap_button.setEnabled(True)
            self.other_node_connection_edit_button.setEnabled(True)
        else:
            self.other_node_connection_combo.setEnabled(False)
            self.other_node_connection_combo.addItem("No connections")
            self.other_node_connection_swap_button.setEnabled(False)
            self.other_node_connection_edit_button.setEnabled(False)

        self.update_connections()

    def update_connections(self) -> None:
        current_node = self.current_node
        current_connection_node = self.current_connection_node

        assert current_node != current_connection_node or current_node is None
        self.area_view_canvas.set_connected_node(current_connection_node)

        if current_connection_node is None or current_node is None:
            assert len(list(self.current_area.actual_nodes)) <= 1 or not self.edit_mode
            return

        self.other_node_alternatives_contents.clear()
        requirement = self.current_area.connections[current_node].get(current_connection_node, Requirement.impossible())
        if self._collection_for_filtering is not None:
            db = self.game_description.resource_database
            context = NodeContext(None, self._collection_for_filtering, db, self.game_description.region_list)
            before_count = sum(1 for _ in requirement.iterate_resource_requirements(context))
            requirement = _ui_patch_and_simplify(requirement, context)
            after_count = sum(1 for _ in requirement.iterate_resource_requirements(context))

            filtered_count_item = QtWidgets.QTreeWidgetItem(self.other_node_alternatives_contents)
            filtered_count_item.setText(
                0, f"A total of {before_count - after_count} requirements were hidden due to filters."
            )

        create_tree_items_for_requirement(
            self.other_node_alternatives_contents,
            self.other_node_alternatives_contents,
            requirement,
            self.resource_database,
        )

    def _swap_selected_connection(self) -> None:
        current_connection_node = self.current_connection_node
        if current_connection_node:
            self.focus_on_node(current_connection_node)

    def replace_connection_with(self, target_node: Node, requirement: Requirement | None) -> None:
        current_node = self.current_node
        assert current_node

        if requirement == Requirement.impossible():
            requirement = None

        self.editor.edit_connections(self.current_area, current_node, target_node, requirement)
        self.update_connections()
        self.area_view_canvas.update()

    @asyncSlot()
    async def _open_edit_connection(self) -> None:
        if self._check_for_edit_dialog():
            return

        from_node = self.current_node
        target_node = self.current_connection_node
        assert from_node is not None
        assert target_node is not None

        requirement = self.current_area.connections[from_node].get(target_node, Requirement.impossible())
        editor = ConnectionsEditor(self, self.resource_database, self.region_list, requirement)
        if await self._execute_edit_dialog(editor):
            self.editor.edit_connections(self.current_area, from_node, target_node, editor.final_requirement)
            self.update_connections()
            self.area_view_canvas.update()

    def _prompt_save_database(self) -> None:
        open_result = QFileDialog.getSaveFileName(self, caption="Select a Randovania database path.", filter="*.json")
        if not open_result or open_result == ("", ""):
            return
        self._save_database(Path(open_result[0]))

    def display_integrity_errors_warning(self, errors: list[str]) -> bool:
        """Return value: true if ignoring"""
        if self._warning_dialogs_disabled:
            return True

        options = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        message = "Database has the following errors:\n\n" + "\n\n".join(errors)
        message += "\n\nIgnore?"

        box = ScrollMessageBox.create_new(
            self,
            QtWidgets.QMessageBox.Icon.Critical,
            "Integrity Check",
            message,
            options,
            QMessageBox.StandardButton.No,
        )
        user_response = box.exec_()

        return user_response == QMessageBox.StandardButton.Yes

    def _save_database(self, path: Path) -> bool:
        errors = integrity_check.find_database_errors(self.game_description)
        if errors:
            if not self.display_integrity_errors_warning(errors):
                return False

        data = data_writer.write_game_description(self.game_description)
        if self._is_internal:
            path.with_suffix("").mkdir(exist_ok=True)
            data_writer.write_as_split_files(data, path.with_suffix(""))
        else:
            json_lib.write_path(path, data)
        self._last_data = data
        return True

    def _save_as_internal_database(self) -> None:
        if self._data_path and self._save_database(self._data_path):
            pretty_print.write_human_readable_game(self.game_description, self._data_path.with_suffix(""))
            default_database.game_description_for.cache_clear()

    @asyncSlot()
    async def on_area_edit_button(self) -> None:
        """Open the AreaDetailsPopup"""

        if self._check_for_edit_dialog():
            return

        area = self.current_area

        if self.current_node is not None:
            node_index = area.nodes.index(self.current_node)
        else:
            node_index = None

        area_edit_popup = AreaDetailsPopup(self.game_description, area)
        if await self._execute_edit_dialog(area_edit_popup):
            try:
                new_area = area_edit_popup.create_new_area()
            except ValueError as e:
                if not self._warning_dialogs_disabled:
                    await async_dialog.warning(self, "Error in new area", str(e))
                return

            self.editor.replace_area(area, new_area)

            self.on_select_region()
            self.focus_on_area_by_name(new_area.name)
            if node_index is not None:
                self.focus_on_node(self.current_area.nodes[node_index])
            else:
                self.update_selected_node()

    def _move_node(self, node: Node, location: NodeLocation) -> None:
        area = self.current_area
        assert node in area.nodes
        self.replace_node_with(area, node, dataclasses.replace(node, location=location))

    def _create_new_node(self, location: NodeLocation | None) -> None:
        node_name, did_confirm = QInputDialog.getText(self, "New Node", "Insert node name:")
        if not did_confirm or node_name == "":
            return

        if self.current_area.node_with_name(node_name) is not None:
            if not self._warning_dialogs_disabled:
                QMessageBox.warning(self, "New Node", f"A node named '{node_name}' already exists.")
            return

        self._do_create_node(node_name, location)

    def _create_new_node_no_location(self) -> None:
        return self._create_new_node(None)

    def _create_identifier(self, node_name: str) -> NodeIdentifier:
        return NodeIdentifier.create(self.current_region.name, self.current_area.name, node_name)

    def _do_create_node(self, node_name: str, location: NodeLocation | None) -> None:
        new_node = GenericNode(
            self._create_identifier(node_name),
            self.editor.new_node_index(),
            False,
            location,
            "",
            ("default",),
            {},
            False,
        )
        self.editor.add_node(self.current_area, new_node)
        self.on_select_area(new_node)

    def _create_new_dock(self, location: NodeLocation, target_area: Area) -> None:
        current_area = self.current_area
        target_identifier = self.region_list.identifier_for_area(target_area)
        source_identifier = self.region_list.identifier_for_area(current_area)

        dock_type, dock_weakness = self.game_description.dock_weakness_database.default_weakness
        source_name_base = next(
            integrity_check.raw_expected_dock_names(
                dock_type, dock_weakness, target_identifier, source_identifier.region
            )
        )
        target_name_base = next(
            integrity_check.raw_expected_dock_names(
                dock_type, dock_weakness, source_identifier, target_identifier.region
            )
        )

        source_count = len(integrity_check.docks_with_same_base_name(current_area, source_name_base))
        if source_count != len(integrity_check.docks_with_same_base_name(target_area, target_name_base)):
            raise ValueError(
                f"Expected {target_area.name} to also have {source_count} docks with name {target_name_base}"
            )

        if source_count > 0:
            source_name = f"{source_name_base} ({source_count + 1})"
            target_name = f"{target_name_base} ({source_count + 1})"
        else:
            source_name = source_name_base
            target_name = target_name_base

        new_node_this_area_identifier = NodeIdentifier.with_area(
            self.region_list.identifier_for_area(current_area), source_name
        )
        new_node_other_area_identifier = NodeIdentifier.with_area(
            self.region_list.identifier_for_area(target_area), target_name
        )

        new_node_this_area = DockNode(
            identifier=new_node_this_area_identifier,
            node_index=self.editor.new_node_index(),
            heal=False,
            location=location,
            description="",
            layers=("default",),
            extra={},
            valid_starting_location=False,
            dock_type=dock_type,
            default_connection=new_node_other_area_identifier,
            default_dock_weakness=dock_weakness,
            exclude_from_dock_rando=False,
            override_default_open_requirement=None,
            override_default_lock_requirement=None,
            incompatible_dock_weaknesses=(),
            ui_custom_name=None,
        )

        new_node_other_area = DockNode(
            identifier=new_node_other_area_identifier,
            node_index=self.editor.new_node_index(),
            heal=False,
            location=location,
            description="",
            layers=("default",),
            extra={},
            valid_starting_location=False,
            dock_type=dock_type,
            default_connection=new_node_this_area_identifier,
            default_dock_weakness=dock_weakness,
            exclude_from_dock_rando=False,
            override_default_open_requirement=None,
            override_default_lock_requirement=None,
            incompatible_dock_weaknesses=(),
            ui_custom_name=None,
        )

        self.editor.add_node(current_area, new_node_this_area)
        self.editor.add_node(target_area, new_node_other_area)

        new_node_this_lock = DockLockNode.create_from_dock(
            new_node_this_area,
            self.editor.new_node_index(),
            self.resource_database,
        )
        new_node_other_lock = DockLockNode.create_from_dock(
            new_node_other_area,
            self.editor.new_node_index(),
            self.resource_database,
        )
        self.editor.add_node(current_area, new_node_this_lock)
        self.editor.add_node(target_area, new_node_other_lock)

        if source_count == 1:
            source_node = current_area.node_with_name(source_name_base)
            target_node = target_area.node_with_name(target_name_base)
            assert source_node
            assert target_node
            self.editor.rename_node(
                current_area,
                source_node,
                f"{source_name_base} (1)",
            )
            self.editor.rename_node(
                target_area,
                target_node,
                f"{target_name_base} (1)",
            )
        self.on_select_area(new_node_this_area)

    def _move_dock_to_area(self, node: Node, new_area: Area) -> None:
        self.editor.move_node_from_area_to_area(self.current_area, new_area, node)
        self.on_select_area()

    def _remove_node(self) -> None:
        if self._check_for_edit_dialog():
            return

        current_node = self.current_node

        if not isinstance(current_node, GenericNode):
            if not self._warning_dialogs_disabled:
                QMessageBox.warning(self, "Delete Node", "Can only remove Generic Nodes")
            return

        user_response = QMessageBox.warning(
            self,
            "Delete Node",
            f"Are you sure you want to delete the node '{current_node.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if user_response != QMessageBox.StandardButton.Yes:
            return

        self.editor.remove_node(self.current_area, current_node)
        self.on_select_area()

    def _on_resource_changed(self, resource: ResourceInfo) -> None:
        if resource.resource_type == ResourceType.EVENT:
            for area in self.game_description.region_list.all_areas:
                for i in range(len(area.nodes)):
                    node = area.nodes[i]
                    if not isinstance(node, EventNode):
                        continue

                    if node.event.short_name == resource.short_name:
                        self.replace_node_with(area, node, dataclasses.replace(node, event=resource))

    def _on_filters_changed(self) -> None:
        if self.edit_mode:
            game = self.original_game_description
        else:
            game = derived_nodes.remove_inactive_layers(
                self.original_game_description,
                self.connection_filters.selected_layers(),
            )

            resources = self.connection_filters.selected_tricks()
            if resources and self.use_trick_filters_check.isChecked():
                self._collection_for_filtering = ResourceCollection.from_resource_gain(
                    game.resource_database, resources.items()
                )
            else:
                self._collection_for_filtering = None

            self.use_trick_filters_check.setEnabled(bool(resources))

        self.update_game(game)

    def _on_slider_changed(self) -> None:
        self.area_view_canvas.set_zoom_value(self.zoom_slider.value())

    def update_slider(self, zoom_in: bool) -> None:
        # update slider on wheel event
        current_val = self.zoom_slider.value()
        if zoom_in:
            self.zoom_slider.setValue(current_val + self.zoom_slider.tickInterval())
        else:
            self.zoom_slider.setValue(current_val - self.zoom_slider.tickInterval())
        # set zoom valuein canvas to the slider value
        self.area_view_canvas.set_zoom_value(self.zoom_slider.value())

    def update_edit_mode(self) -> None:
        self.edit_area_button.setVisible(self.edit_mode)
        self.delete_node_button.setVisible(self.edit_mode)
        self.new_node_button.setVisible(self.edit_mode)
        self.save_database_button.setVisible(self.edit_mode)
        self.other_node_connection_edit_button.setVisible(self.edit_mode)
        self.use_trick_filters_check.setVisible(not self.edit_mode)
        self.node_heals_check.setEnabled(self.edit_mode)
        self.area_spawn_check.setEnabled(self.edit_mode)
        self.node_edit_button.setVisible(self.edit_mode)
        self.resource_editor.set_allow_edits(self.edit_mode)
        self.area_view_canvas.set_edit_mode(self.edit_mode)
        self.connection_filters.set_edit_mode(self.edit_mode)
        self.setWindowTitle("Data Editor" if self.edit_mode else "Data Visualizer")

    @property
    def current_region(self) -> Region:
        return self.region_selector_box.currentData()

    @property
    def current_area(self) -> Area:
        return self.area_selector_box.currentData()

    @property
    def current_node(self) -> Node | None:
        if self.selected_node_button:
            return self.radio_button_to_node.get(self.selected_node_button)
        else:
            return None

    @property
    def current_connection_node(self) -> Node | None:
        return self.other_node_connection_combo.currentData()
