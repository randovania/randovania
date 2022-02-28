from typing import Callable, Optional, Union
from randovania.game_description import default_database
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.game_description.world.node import DockNode, EventNode, GenericNode, Node, NodeIdentifier, PickupNode, ResourceNode, TeleporterNode
from randovania.gui.generated.area_picker_dialog_ui import Ui_AreaPickerDialog
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt

def get_node(parent: QtWidgets.QWidget, game: RandovaniaGame, filter: Optional[Callable[[Node], bool]]=None) -> Optional[NodeIdentifier]:
    dialog = AreaPickerDialog(parent, game)
    result = dialog.exec()
    if result == QtWidgets.QDialog.DialogCode.Accepted:
        return NodeIdentifier(AreaIdentifier(dialog.current_world.name, dialog.current_area.name), dialog.current_node.name)
    else:
        return None

class AreaPickerDialog(QtWidgets.QDialog, Ui_AreaPickerDialog):
    _model: QtCore.QAbstractItemModel
    _world_list: WorldList
    _empty_index: QtCore.QModelIndex
    worldList: QtWidgets.QListView
    areaList: QtWidgets.QListView
    nodeList: QtWidgets.QListView
    world_combo_box: QtWidgets.QComboBox
    area_combo_box: QtWidgets.QComboBox
    node_combo_box: QtWidgets.QComboBox
    confirm_buttons: QtWidgets.QDialogButtonBox
    current_world: Optional[World]
    current_area: Optional[Area]
    current_node: Optional[Node]

    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent)
        self.setupUi(self)
        self._world_list = default_database.game_description_for(game).world_list
        self._build_model()
        self.current_world = None
        self.current_area = None
        self.current_node = None
        self.worldList.selectionModel().currentChanged.connect(self._update_areas)
        self.areaList.selectionModel().currentChanged.connect(self._update_nodes)
        self.nodeList.selectionModel().currentChanged.connect(self._node_selected)
        self.nodeList.doubleClicked.connect(self._confirm_selection)
        self.searchLineEdit.textEdited.connect(self._update_search)
        self.searchLineEdit.returnPressed.connect(self._confirm_selection)
        self.confirmButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.searchLineEdit.setFocus()

    def _build_model(self):
        model = QtGui.QStandardItemModel()
        top_level = QtGui.QStandardItem()
        for world in self._world_list.worlds:
            world_item = QtGui.QStandardItem(world.name)
            world_item.setData(world, Qt.UserRole)
            for area in world.areas:
                area_item = QtGui.QStandardItem(area.name)
                area_item.setData(area, Qt.UserRole)
                for node in area.nodes:
                    node_item = QtGui.QStandardItem(node.name)
                    node_item.setData(node, Qt.UserRole)
                    area_item.appendRow(node_item)
                world_item.appendRow(area_item)
            top_level.appendRow(world_item)
        model.appendRow(top_level)
        model.sort(0)
        proxy_model = AreaPickerFilterProxyModel(self)
        proxy_model.setSourceModel(model)
        self._model = proxy_model
        self.worldList.setModel(proxy_model)
        self.areaList.setModel(proxy_model)
        self.nodeList.setModel(proxy_model)
        self._empty_index = self.worldList.rootIndex()
        self.worldList.setRootIndex(proxy_model.index(0, 0))
        self.areaList.setEnabled(False)
        self.nodeList.setEnabled(False)

    def validate_root_indexes(self):
        self.worldList.setRootIndex(self._model.index(0, 0))
        self._validate_selection(self.areaList, self.areaList.rootIndex())
        self._validate_selection(self.nodeList, self.nodeList.rootIndex())

    def _validate_selection(self, list: QtWidgets.QListView, root_index: QtCore.QModelIndex):
        valid = root_index.isValid()
        list.setRootIndex(root_index if valid else self._empty_index)
        list.setEnabled(valid)
        if not valid:
            self._enable_confirm(False)

    def _confirm_selection(self):
        if self.current_node is not None:
            self.accept()

    def _update_areas(self, world: QtCore.QModelIndex):
        self.current_world = world.data(Qt.UserRole)
        self._validate_selection(self.areaList, world)
        self.areaList.selectionModel().clear()

    def _update_nodes(self, area: QtCore.QModelIndex):
        self.current_area = area.data(Qt.UserRole)
        self._validate_selection(self.nodeList, area)
        self.nodeList.selectionModel().clear()

    def _node_selected(self, node: QtCore.QModelIndex):
        self._enable_confirm(node.isValid())
        self.current_node = node.data(Qt.UserRole)

    def _enable_confirm(self, enable: bool):
        self.confirmButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enable)

    def _update_search(self, text: str):
        if not text:
            return
        text = text.lower()
        root: QtCore.QModelIndex = self.worldList.rootIndex()
        i = 0
        while self._model.hasIndex(i, 0, root):
            world_index = self._model.index(i, 0, root)
            j = 0
            while self._model.hasIndex(j, 0, world_index):
                area_index = self._model.index(j, 0, world_index)
                if area_index.data(Qt.UserRole).name.lower().startswith(text):
                    self.worldList.selectionModel().setCurrentIndex(world_index, QtCore.QItemSelectionModel.SelectCurrent)
                    self.areaList.selectionModel().setCurrentIndex(area_index, QtCore.QItemSelectionModel.SelectCurrent)
                    self.nodeList.selectionModel().setCurrentIndex(self._model.index(0, 0, area_index), QtCore.QItemSelectionModel.SelectCurrent)
                    return
                j += 1
            i += 1


class AreaPickerFilterProxyModel(QtCore.QSortFilterProxyModel):
    _show_locations: bool
    _show_pickups: bool
    _show_events: bool
    _LOCATION_NODES: list[type] = [DockNode, GenericNode, TeleporterNode]
    _PICKUP_NODES: list[type] = [PickupNode]
    _EVENT_NODES: list[type] = [EventNode]

    def __init__(self, parent: AreaPickerDialog):
        super().__init__(parent)
        self._show_locations = parent.locationsCheckBox.isChecked()
        self._show_pickups = parent.pickupsCheckBox.isChecked()
        self._show_events = parent.eventsCheckBox.isChecked()
        parent.locationsCheckBox.stateChanged.connect(self._set_show_locations)
        parent.pickupsCheckBox.stateChanged.connect(self._set_show_pickups)
        parent.eventsCheckBox.stateChanged.connect(self._set_show_events)
        # Lets us filter nodes only; worlds/areas with visible nodes will appear
        self.setRecursiveFilteringEnabled(True)
        self._default_filters = [
            self._filter_location,
            self._filter_pickup,
            self._filter_event,
            self._none_of_above
        ]
    
    def _set_show_locations(self, state):
        self._show_locations = state == Qt.Checked
        self.invalidateFilter()
    def _set_show_pickups(self, state):
        self._show_pickups = state == Qt.Checked
        self.invalidateFilter()
    def _set_show_events(self, state):
        self._show_events = state == Qt.Checked
        self.invalidateFilter()

    def _filter_location(self, node: Node) -> bool:
        return self._show_locations and self._isany(node, self._LOCATION_NODES)
    def _filter_pickup(self, node: Node) -> bool:
        return self._show_pickups and self._isany(node, self._PICKUP_NODES)
    def _filter_event(self, node: Node) -> bool:
        return self._show_events and self._isany(node, self._EVENT_NODES)
    # Shows nodes that don't fall under any of the above criteria
    def _none_of_above(self, node: Node) -> bool:
        return isinstance(node, Node) and \
            not self._isany(node, self._LOCATION_NODES + self._PICKUP_NODES + self._EVENT_NODES)

    def filterAcceptsRow(self, source_row: int, source_parent: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]) -> bool:
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        data = source_index.data(Qt.UserRole)
        return any([filter(data) for filter in self._default_filters])

    def invalidateFilter(self):
        super().invalidateFilter()
        self.parent().validate_root_indexes()

    @staticmethod
    def _isany(obj: object, types: list[type]):
        return any ([isinstance(obj, t) for t in types])