from PySide2 import QtWidgets

from randovania.game_description.area import Area
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.dock import DockType, DockConnection
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    TranslatorGateNode, LogbookNode, LoreType
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world import World
from randovania.gui.generated.node_details_popup_ui import Ui_NodeDetailsPopup
from randovania.gui.lib import common_qt_lib, enum_lib


def refresh_if_needed(combo: QtWidgets.QComboBox, func):
    if combo.currentIndex() == 0:
        func(0)


class NodeDetailsPopup(QtWidgets.QDialog, Ui_NodeDetailsPopup):
    def __init__(self, game: GameDescription, node: Node):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.game = game
        self.node = node
        world = game.world_list.nodes_to_world(node)

        self._type_to_tab = {
            GenericNode: self.tab_generic,
            DockNode: self.tab_dock,
            PickupNode: self.tab_pickup,
            TeleporterNode: self.tab_teleporter,
            EventNode: self.tab_event,
            TranslatorGateNode: self.tab_translator_gate,
            LogbookNode: self.tab_logbook,
        }
        tab_to_type = {tab: node_type for node_type, tab in self._type_to_tab.items()}

        # Dynamic Stuff
        for i, node_type in enumerate(self._type_to_tab.keys()):
            self.node_type_combo.setItemData(i, node_type)

        for area in world.areas:
            self.dock_connection_area_combo.addItem(area.name, area)

        for i, enum in enumerate(enum_lib.iterate_enum(DockType)):
            self.dock_type_combo.setItemData(i, enum)

        for world in sorted(game.world_list.worlds, key=lambda x: x.name):
            self.teleporter_destination_world_combo.addItem("{0.name} ({0.dark_name})".format(world), userData=world)

        for event in game.resource_database.event:
            self.event_resource_combo.addItem(event.long_name, event)

        for i, enum in enumerate(enum_lib.iterate_enum(LoreType)):
            self.lore_type_combo.setItemData(i, enum)

        # Signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.node_type_combo.currentIndexChanged.connect(self.on_node_type_combo)
        self.dock_connection_area_combo.currentIndexChanged.connect(self.on_dock_connection_area_combo)
        self.dock_connection_node_combo.currentIndexChanged.connect(self.on_dock_connection_node_combo)
        self.dock_type_combo.currentIndexChanged.connect(self.on_dock_type_combo)
        self.teleporter_destination_world_combo.currentIndexChanged.connect(self.on_teleporter_destination_world_combo)
        self.lore_type_combo.currentIndexChanged.connect(self.on_lore_type_combo)

        # Hide the tab bar
        tab_bar: QtWidgets.QTabBar = self.tab_widget.findChild(QtWidgets.QTabBar)
        tab_bar.hide()

        # Values
        self.name_edit.setText(node.name)
        self.heals_check.setChecked(node.heal)

        visible_tab = self._fill_for_type(node)
        self.node_type_combo.setCurrentIndex(self.node_type_combo.findData(tab_to_type[visible_tab]))

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

    def fill_for_dock(self, node: DockNode):
        self.dock_index_spin.setValue(node.dock_index)

        # Connection
        other_area = self.game.world_list.area_by_asset_id(node.default_connection.area_asset_id)
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
        area = world.area_by_asset_id(node.default_connection.area_asset_id)

        self.teleporter_instance_id_edit.setText(str(node.teleporter_instance_id))
        self.teleporter_destination_world_combo.setCurrentIndex(self.teleporter_destination_world_combo.findData(world))
        refresh_if_needed(self.teleporter_destination_world_combo, self.on_teleporter_destination_world_combo)
        self.teleporter_destination_area_combo.setCurrentIndex(self.teleporter_destination_area_combo.findData(area))
        self.teleporter_scan_asset_id_edit.setText(str(node.scan_asset_id) if node.scan_asset_id is not None else "")
        self.teleporter_editable_check.setChecked(node.editable)
        self.teleporter_vanilla_name_edit.setChecked(node.keep_name_when_vanilla)

    def fill_for_event(self, node: EventNode):
        self.event_resource_combo.setCurrentIndex(self.event_resource_combo.findData(node.event))

    def fill_for_translator_gate(self, node: TranslatorGateNode):
        self.translator_gate_spin.setValue(node.gate.index)

    def fill_for_logbook_node(self, node: LogbookNode):
        self.logbook_string_asset_id_edit.setText(str(node.string_asset_id))
        self.lore_type_combo.setCurrentIndex(self.lore_type_combo.findData(node.lore_type))
        refresh_if_needed(self.lore_type_combo, self.on_lore_type_combo)

        if node.lore_type == LoreType.LUMINOTH_LORE:
            self.logbook_extra_combo.setCurrentIndex(self.logbook_extra_combo.findData(node.required_translator))

        elif node.lore_type == LoreType.LUMINOTH_WARRIOR:
            self.logbook_extra_combo.setCurrentIndex(self.logbook_extra_combo.findData(node.hint_index))

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

    # Final
    def create_new_node(self) -> Node:
        node_type = self.node_type_combo.currentData()
        name = self.name_edit.text()
        heal = self.heals_check.isChecked()
        index = self.node.index

        if node_type == GenericNode:
            return GenericNode(name, heal, index)

        elif node_type == DockNode:
            return DockNode(
                name, heal, index,
                self.dock_index_spin.value(),
                DockConnection(self.dock_connection_area_combo.currentData().area_asset_id,
                               self.dock_connection_node_combo.currentData()),
                self.dock_weakness_combo.currentData(),
            )

        elif node_type == PickupNode:
            return PickupNode(
                name, heal, index,
                PickupIndex(self.pickup_index_spin.value()),
                self.major_location_check.isChecked(),
            )

        elif node_type == TeleporterNode:
            scan_asset_id = self.teleporter_scan_asset_id_edit.text()

            return TeleporterNode(
                name, heal, index,
                int(self.teleporter_instance_id_edit.text()),
                AreaLocation(self.teleporter_destination_world_combo.currentData().world_asset_id,
                             self.teleporter_destination_area_combo.currentData().area_asset_id),
                int(scan_asset_id) if scan_asset_id != "" else None,
                self.teleporter_vanilla_name_edit.isChecked(),
                self.teleporter_editable_check.isChecked(),
            )

        elif node_type == EventNode:
            return EventNode(
                name, heal, index,
                self.event_resource_combo.currentData(),
            )

        elif node_type == TranslatorGateNode:
            return TranslatorGateNode(
                name, heal, index,
                TranslatorGate(self.translator_gate_spin.value()),
                self._get_scan_visor()
            )

        elif node_type == LogbookNode:
            lore_type: LoreType = self.lore_type_combo.currentData()
            if lore_type == LoreType.LUMINOTH_LORE:
                required_translator = self.logbook_extra_combo.currentData()
            else:
                required_translator = None

            if lore_type == LoreType.LUMINOTH_WARRIOR:
                hint_index = self.logbook_extra_combo.currentData()
            else:
                hint_index = None

            return LogbookNode(
                name, heal, index,
                int(self.logbook_string_asset_id_edit.text()),
                self._get_scan_visor(),
                lore_type,
                required_translator,
                hint_index
            )

        else:
            raise RuntimeError(f"Unknown node type: {node_type}")

    def _get_scan_visor(self):
        return find_resource_info_with_long_name(
            self.game.resource_database.item,
            "Scan Visor"
        )
