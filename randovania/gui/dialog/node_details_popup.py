import dataclasses

from PySide2 import QtWidgets
from qasync import asyncSlot

from randovania.game_description.world.area import Area
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.dock import DockType, DockConnection
from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.node import Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    TranslatorGateNode, LogbookNode, LoreType, NodeLocation, PlayerShipNode
from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world.teleporter import Teleporter
from randovania.game_description.world.world import World
from randovania.gui.dialog.connections_editor import ConnectionsEditor
from randovania.gui.generated.node_details_popup_ui import Ui_NodeDetailsPopup
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.connections_visualizer import ConnectionsVisualizer
from randovania.lib import enum_lib


def refresh_if_needed(combo: QtWidgets.QComboBox, func):
    if combo.currentIndex() == 0:
        func(0)


class NodeDetailsPopup(QtWidgets.QDialog, Ui_NodeDetailsPopup):
    _unlocked_by_requirement = Requirement.trivial()
    _connections_visualizer = None

    def __init__(self, game: GameDescription, node: Node):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game = game
        self.node = node
        self.world = game.world_list.nodes_to_world(node)
        world = self.world

        self._type_to_tab = {
            GenericNode: self.tab_generic,
            DockNode: self.tab_dock,
            PickupNode: self.tab_pickup,
            TeleporterNode: self.tab_teleporter,
            EventNode: self.tab_event,
            TranslatorGateNode: self.tab_translator_gate,
            LogbookNode: self.tab_logbook,
            PlayerShipNode: self.tab_player_ship,
        }
        tab_to_type = {tab: node_type for node_type, tab in self._type_to_tab.items()}

        # Dynamic Stuff
        for i, node_type in enumerate(self._type_to_tab.keys()):
            self.node_type_combo.setItemData(i, node_type)

        for area in world.areas:
            self.dock_connection_area_combo.addItem(area.name, area)
        refresh_if_needed(self.dock_connection_area_combo, self.on_dock_connection_area_combo)

        for i, enum in enumerate(enum_lib.iterate_enum(DockType)):
            self.dock_type_combo.setItemData(i, enum)

        for world in sorted(game.world_list.worlds, key=lambda x: x.name):
            self.teleporter_destination_world_combo.addItem("{0.name} ({0.dark_name})".format(world), userData=world)
        refresh_if_needed(self.teleporter_destination_world_combo, self.on_teleporter_destination_world_combo)

        for event in sorted(game.resource_database.event, key=lambda it: it.long_name):
            self.event_resource_combo.addItem(event.long_name, event)
        if self.event_resource_combo.count() == 0:
            self.event_resource_combo.addItem("No events in database", None)
            self.event_resource_combo.setEnabled(False)

        for i, enum in enumerate(enum_lib.iterate_enum(LoreType)):
            self.lore_type_combo.setItemData(i, enum)
        refresh_if_needed(self.lore_type_combo, self.on_lore_type_combo)

        self.set_unlocked_by(Requirement.trivial())

        # Signals
        self.button_box.accepted.connect(self.try_accept)
        self.button_box.rejected.connect(self.reject)
        self.node_type_combo.currentIndexChanged.connect(self.on_node_type_combo)
        self.dock_connection_area_combo.currentIndexChanged.connect(self.on_dock_connection_area_combo)
        self.dock_connection_node_combo.currentIndexChanged.connect(self.on_dock_connection_node_combo)
        self.dock_type_combo.currentIndexChanged.connect(self.on_dock_type_combo)
        self.teleporter_destination_world_combo.currentIndexChanged.connect(self.on_teleporter_destination_world_combo)
        self.lore_type_combo.currentIndexChanged.connect(self.on_lore_type_combo)
        self.player_ship_unlocked_button.clicked.connect(self.on_player_ship_unlocked_button)

        # Hide the tab bar
        tab_bar: QtWidgets.QTabBar = self.tab_widget.findChild(QtWidgets.QTabBar)
        tab_bar.hide()

        # Values
        self.name_edit.setText(node.name)
        self.heals_check.setChecked(node.heal)
        self.location_group.setChecked(node.location is not None)
        if node.location is not None:
            self.location_x_spin.setValue(node.location.x)
            self.location_y_spin.setValue(node.location.y)
            self.location_z_spin.setValue(node.location.z)

        visible_tab = self._fill_for_type(node)
        self.node_type_combo.setCurrentIndex(self.node_type_combo.findData(tab_to_type[visible_tab]))
        refresh_if_needed(self.node_type_combo, self.on_node_type_combo)

    def _fill_for_type(self, node: Node) -> QtWidgets.QWidget:
        if isinstance(node, GenericNode):
            return self.tab_generic

        elif isinstance(node, DockNode):
            self.fill_for_dock(node)
            return self.tab_dock

        elif isinstance(node, PickupNode):
            self.fill_for_pickup(node)
            return self.tab_pickup

        elif isinstance(node, TeleporterNode):
            self.fill_for_teleporter(node)
            return self.tab_teleporter

        elif isinstance(node, EventNode):
            self.fill_for_event(node)
            return self.tab_event

        elif isinstance(node, TranslatorGateNode):
            self.fill_for_translator_gate(node)
            return self.tab_translator_gate

        elif isinstance(node, LogbookNode):
            self.fill_for_logbook_node(node)
            return self.tab_logbook

        elif isinstance(node, PlayerShipNode):
            self.fill_for_player_ship_node(node)
            return self.tab_player_ship

        else:
            raise ValueError(f"Unknown node type: {node}")

    def fill_for_dock(self, node: DockNode):
        self.dock_index_spin.setValue(node.dock_index)

        # Connection
        other_area = self.game.world_list.area_by_area_location(AreaLocation(self.world.world_asset_id,
                                                                             node.default_connection.area_asset_id))
        self.dock_connection_area_combo.setCurrentIndex(self.dock_connection_area_combo.findData(other_area))
        refresh_if_needed(self.dock_connection_area_combo, self.on_dock_connection_area_combo)
        self.dock_connection_node_combo.setCurrentIndex(
            self.dock_connection_node_combo.findData(node.default_connection.dock_index))
        self.dock_connection_index_raw_spin.setValue(node.default_connection.dock_index)

        # Dock Weakness
        self.dock_type_combo.setCurrentIndex(self.dock_type_combo.findData(node.default_dock_weakness.dock_type))
        refresh_if_needed(self.dock_type_combo, self.on_dock_type_combo)
        self.dock_weakness_combo.setCurrentIndex(self.dock_weakness_combo.findData(node.default_dock_weakness))

    def fill_for_pickup(self, node: PickupNode):
        self.pickup_index_spin.setValue(node.pickup_index.index)
        self.major_location_check.setChecked(node.major_location)

    def fill_for_teleporter(self, node: TeleporterNode):
        world = self.game.world_list.world_by_asset_id(node.default_connection.world_asset_id)
        area = self.game.world_list.area_by_area_location(node.default_connection)

        self.teleporter_instance_id_edit.setText(hex(node.teleporter_instance_id)
                                                 if node.teleporter_instance_id is not None else "")
        self.teleporter_destination_world_combo.setCurrentIndex(self.teleporter_destination_world_combo.findData(world))
        refresh_if_needed(self.teleporter_destination_world_combo, self.on_teleporter_destination_world_combo)
        self.teleporter_destination_area_combo.setCurrentIndex(self.teleporter_destination_area_combo.findData(area))
        self.teleporter_scan_asset_id_edit.setText(hex(node.scan_asset_id) if node.scan_asset_id is not None else "")
        self.teleporter_editable_check.setChecked(node.editable)
        self.teleporter_vanilla_name_edit.setChecked(node.keep_name_when_vanilla)

    def fill_for_event(self, node: EventNode):
        self.event_resource_combo.setCurrentIndex(self.event_resource_combo.findData(node.event))

    def fill_for_translator_gate(self, node: TranslatorGateNode):
        self.translator_gate_spin.setValue(node.gate.index)

    def fill_for_logbook_node(self, node: LogbookNode):
        self.logbook_string_asset_id_edit.setText(hex(node.string_asset_id).upper())
        self.lore_type_combo.setCurrentIndex(self.lore_type_combo.findData(node.lore_type))
        refresh_if_needed(self.lore_type_combo, self.on_lore_type_combo)

        if node.lore_type == LoreType.LUMINOTH_LORE:
            self.logbook_extra_combo.setCurrentIndex(self.logbook_extra_combo.findData(node.required_translator))

        elif node.lore_type == LoreType.LUMINOTH_WARRIOR:
            self.logbook_extra_combo.setCurrentIndex(self.logbook_extra_combo.findData(node.hint_index))

    def fill_for_player_ship_node(self, node: PlayerShipNode):
        self.set_unlocked_by(node.is_unlocked)

    def set_unlocked_by(self, requirement: Requirement):
        if self._connections_visualizer is not None:
            self._connections_visualizer.deleteLater()
            self._connections_visualizer = None

        self._unlocked_by_requirement = requirement
        self._connections_visualizer = ConnectionsVisualizer(
            self.player_ship_unlocked_group,
            self.player_ship_unlocked_layout,
            self.game.resource_database,
            requirement,
            False
        )

    # Signals
    def on_node_type_combo(self, _):
        self.tab_widget.setCurrentWidget(self._type_to_tab[self.node_type_combo.currentData()])

    def on_dock_connection_area_combo(self, _):
        area: Area = self.dock_connection_area_combo.currentData()

        self.dock_connection_node_combo.clear()
        for node in area.nodes:
            if isinstance(node, DockNode):
                self.dock_connection_node_combo.addItem(f"{node.name} - Dock {node.dock_index}", node.dock_index)
        self.dock_connection_node_combo.addItem("Other", None)

    def on_dock_connection_node_combo(self, _):
        self.dock_connection_index_raw_spin.setEnabled(self.dock_connection_node_combo.currentData() is None)

    def on_dock_type_combo(self, _):
        self.dock_weakness_combo.clear()

        for weakness in self.game.dock_weakness_database.get_by_type(self.dock_type_combo.currentData()):
            self.dock_weakness_combo.addItem(weakness.name, weakness)

    def on_teleporter_destination_world_combo(self, _):
        world: World = self.teleporter_destination_world_combo.currentData()

        self.teleporter_destination_area_combo.clear()
        for area in sorted(world.areas, key=lambda x: x.name):
            self.teleporter_destination_area_combo.addItem(area.name, userData=area)

    def on_lore_type_combo(self, _):
        lore_type: LoreType = self.lore_type_combo.currentData()

        self.logbook_extra_combo.clear()

        if lore_type == LoreType.LUMINOTH_LORE:
            self.logbook_extra_label.setText("Translator needed:")
            for item in self.game.resource_database.item:
                self.logbook_extra_combo.addItem(item.long_name, item)

        elif lore_type == LoreType.LUMINOTH_WARRIOR:
            self.logbook_extra_label.setText("Pickup index hinted:")
            for node in self.game.world_list.all_nodes:
                if isinstance(node, PickupNode):
                    self.logbook_extra_combo.addItem("{} - {}".format(
                        self.game.world_list.node_name(node, True, True),
                        node.pickup_index.index,
                    ), node.pickup_index.index)

        else:
            self.logbook_extra_label.setText("Nothing:")
            self.logbook_extra_combo.addItem("Nothing", None)

    @asyncSlot()
    async def on_player_ship_unlocked_button(self):
        self._edit_popup = ConnectionsEditor(self, self.game.resource_database, self._unlocked_by_requirement)
        self._edit_popup.setModal(True)
        try:
            result = await async_dialog.execute_dialog(self._edit_popup)
            if result == QtWidgets.QDialog.Accepted:
                self.set_unlocked_by(self._edit_popup.final_requirement)
        finally:
            self._edit_popup = None

    # Final
    def create_new_node(self) -> Node:
        node_type = self.node_type_combo.currentData()
        name = self.name_edit.text()
        heal = self.heals_check.isChecked()
        location = None
        if self.location_group.isChecked():
            location = NodeLocation(self.location_x_spin.value(),
                                    self.location_y_spin.value(),
                                    self.location_z_spin.value())
        index = self.node.index

        if node_type == GenericNode:
            return GenericNode(name, heal, location, index)

        elif node_type == DockNode:
            return DockNode(
                name, heal, location, index,
                self.dock_index_spin.value(),
                DockConnection(self.dock_connection_area_combo.currentData().area_asset_id,
                               self.dock_connection_node_combo.currentData()),
                self.dock_weakness_combo.currentData(),
            )

        elif node_type == PickupNode:
            return PickupNode(
                name, heal, location, index,
                PickupIndex(self.pickup_index_spin.value()),
                self.major_location_check.isChecked(),
            )

        elif node_type == TeleporterNode:
            instance_id = self.teleporter_instance_id_edit.text()
            scan_asset_id = self.teleporter_scan_asset_id_edit.text()

            if instance_id != "":
                instance_id_value = int(instance_id, 0)
                if isinstance(self.node, TeleporterNode):
                    teleporter = dataclasses.replace(self.node.teleporter, instance_id=instance_id_value)
                else:
                    teleporter = Teleporter(0, 0, instance_id_value)
            else:
                teleporter = None

            return TeleporterNode(
                name, heal, location, index, teleporter,
                AreaLocation(self.teleporter_destination_world_combo.currentData().world_asset_id,
                             self.teleporter_destination_area_combo.currentData().area_asset_id),
                int(scan_asset_id, 0) if scan_asset_id != "" else None,
                self.teleporter_vanilla_name_edit.isChecked(),
                self.teleporter_editable_check.isChecked(),
            )

        elif node_type == EventNode:
            event = self.event_resource_combo.currentData()
            if event is None:
                raise ValueError("There are no events in the database, unable to create EventNode.")
            return EventNode(
                name, heal, location, index,
                event,
            )

        elif node_type == TranslatorGateNode:
            return TranslatorGateNode(
                name, heal, location, index,
                TranslatorGate(self.translator_gate_spin.value()),
                self._get_scan_visor()
            )

        elif node_type == LogbookNode:
            lore_type: LoreType = self.lore_type_combo.currentData()
            if lore_type == LoreType.LUMINOTH_LORE:
                required_translator = self.logbook_extra_combo.currentData()
                if required_translator is None:
                    raise ValueError("Missing required translator.")
            else:
                required_translator = None

            if lore_type == LoreType.LUMINOTH_WARRIOR:
                hint_index = self.logbook_extra_combo.currentData()
            else:
                hint_index = None

            return LogbookNode(
                name, heal, location, index,
                int(self.logbook_string_asset_id_edit.text(), 0),
                self._get_scan_visor(),
                lore_type,
                required_translator,
                hint_index
            )

        elif node_type == PlayerShipNode:
            return PlayerShipNode(
                name, heal, location, index,
                self._unlocked_by_requirement,
                self._get_command_visor()
            )

        else:
            raise RuntimeError(f"Unknown node type: {node_type}")

    def _get_scan_visor(self):
        return find_resource_info_with_long_name(
            self.game.resource_database.item,
            "Scan Visor"
        )

    def _get_command_visor(self):
        return find_resource_info_with_long_name(
            self.game.resource_database.item,
            "Command Visor"
        )

    def try_accept(self):
        try:
            self.create_new_node()
            self.accept()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Invalid configuration",
                                          f"Unable to save node: {e}")
