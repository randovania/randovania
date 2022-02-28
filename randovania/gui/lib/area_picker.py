from typing import Callable, Iterable, Optional, Union
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

def get_node(header_text: str, parent: QtWidgets.QWidget, game: RandovaniaGame, valid_areas: list[AreaIdentifier] = None) -> Optional[NodeIdentifier]:
    """
    Opens a modal dialog for the user to pick a specific node.

    :param header_text: the instructional text at the top of the dialog
    :param parent: the parent widget that spawns the dialog
    :param game: the game whose nodes will be used
    :param valid_areas: limit the areas shown in the dialog to the areas in this list
    :return: a NodeIdentifier of the selected node, or None if the dialog was canceled
    """
    accepted, world, area, node = _get_item(header_text, parent, game, valid_areas, True, "Select Node")
    return None if not accepted else NodeIdentifier(AreaIdentifier(world.name, area.name), node.name)

def get_area(header_text: str, parent: QtWidgets.QWidget, game: RandovaniaGame, valid_areas: list[AreaIdentifier] = None) -> Optional[NodeIdentifier]:
    """
    Opens a modal dialog for the user to pick a specific area.

    :param header_text: the instructional text at the top of the dialog
    :param parent: the parent widget that spawns the dialog
    :param game: the game whose areas will be used
    :param valid_areas: limit the areas shown in the dialog to the areas in this list
    :return: an AreaIdentifier of the selected area, or None if the dialog was canceled
    """
    accepted, world, area, _ = _get_item(header_text, parent, game, valid_areas, False, "Select Area")
    return None if not accepted else AreaIdentifier(world.name, area.name)

def _get_item(header_text: str, parent: QtWidgets.QWidget, game: RandovaniaGame, valid_areas: list[AreaIdentifier] = None, pick_node = True, window_title: str = None) -> tuple[bool, Optional[World], Optional[Area], Optional[Node]]:
    dialog = AreaPickerDialog(header_text, parent, game, valid_areas, pick_node, window_title)
    result = dialog.exec()
    if result == QtWidgets.QDialog.DialogCode.Accepted:
        return (True, dialog.current_world, dialog.current_area, dialog.current_node)
    else:
        return (False, None, None, None)


class AreaPickerModel(QtCore.QSortFilterProxyModel):
    _world_list: WorldList
    _show_locations: bool = True
    _show_pickups: bool = True
    _show_events: bool = True
    _valid_areas: list[AreaIdentifier]
    _LOCATION_NODES: list[type] = [DockNode, GenericNode, TeleporterNode]
    _PICKUP_NODES: list[type] = [PickupNode]
    _EVENT_NODES: list[type] = [EventNode]

    def __init__(self, parent: Optional[QtCore.QObject], world_list: WorldList, valid_areas: list[AreaIdentifier] = None):
        super().__init__(parent)
        self.setSourceModel(self._build_model(world_list))
        self._world_list = world_list
        self._valid_areas = valid_areas
        # Lets us filter nodes only; worlds/areas with visible nodes will appear
        self.setRecursiveFilteringEnabled(True)
        self._default_filters = [
            self._filter_location,
            self._filter_pickup,
            self._filter_event,
            self._none_of_above
        ]

    @staticmethod
    def _build_model(world_list: WorldList) -> QtGui.QStandardItemModel:
        model = QtGui.QStandardItemModel()
        top_level = QtGui.QStandardItem()
        for world in world_list.worlds:
            world_item = QtGui.QStandardItem(world.name)
            world_item.setData(world, Qt.UserRole)
            world_item.setEditable(False)
            for area in world.areas:
                area_item = QtGui.QStandardItem(area.name)
                area_item.setData(area, Qt.UserRole)
                area_item.setEditable(False)
                for node in area.nodes:
                    node_item = QtGui.QStandardItem(node.name)
                    node_item.setData(node, Qt.UserRole)
                    node_item.setEditable(False)
                    area_item.appendRow(node_item)
                world_item.appendRow(area_item)
            top_level.appendRow(world_item)
        model.appendRow(top_level)
        model.sort(0)
        return model

    def set_show_locations(self, state):
        self._show_locations = state == Qt.Checked
        self.invalidateFilter()
    def set_show_pickups(self, state):
        self._show_pickups = state == Qt.Checked
        self.invalidateFilter()
    def set_show_events(self, state):
        self._show_events = state == Qt.Checked
        self.invalidateFilter()

    def _is_in_valid_area(self, node: Node):
        area_id = self._world_list.node_to_area_location(node)
        return not self._valid_areas or area_id in self._valid_areas

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
        """
        Determines if the current item should or should not be accepted into the model,
        called automatically for each item.
        """
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        data = source_index.data(Qt.UserRole)
        return any([filter(data) for filter in self._default_filters]) and \
            self._is_in_valid_area(data)

    def all_areas(self) -> Iterable[tuple[QtCore.QModelIndex, QtCore.QModelIndex]]:
        root = self.index(0, 0)
        i = 0
        while self.hasIndex(i, 0, root):
            world_index = self.index(i, 0, root)
            j = 0
            while self.hasIndex(j, 0, world_index):
                area_index = self.index(j, 0, world_index)
                yield world_index, area_index
                j += 1
            i += 1

    def invalidateFilter(self):
        """Invalidates the filter and updates it according to the current filter parameters."""
        super().invalidateFilter()
        self.parent().validate_root_indexes()

    @staticmethod
    def _isany(obj: object, types: list[type]):
        """Checks if the object is any type in a list of types."""
        return any ([isinstance(obj, t) for t in types])


class AreaPickerDialog(QtWidgets.QDialog, Ui_AreaPickerDialog):
    _model: AreaPickerModel
    _world_list: WorldList
    _empty_index: QtCore.QModelIndex
    _pick_node: bool
    worldList: QtWidgets.QListView
    areaList: QtWidgets.QListView
    nodeList: QtWidgets.QListView
    world_combo_box: QtWidgets.QComboBox
    area_combo_box: QtWidgets.QComboBox
    node_combo_box: QtWidgets.QComboBox
    confirm_buttons: QtWidgets.QDialogButtonBox
    current_world: Optional[World] = None
    current_area: Optional[Area] = None
    current_node: Optional[Node] = None

    def __init__(self, header_text: str, parent: QtWidgets.QWidget, game: RandovaniaGame, valid_areas: list[AreaIdentifier] = None, pick_node: bool = True, window_title: str = None):
        super().__init__(parent)
        self.setupUi(self)
        world_list = default_database.game_description_for(game).world_list
        self._pick_node = pick_node
        self._model = AreaPickerModel(self, world_list, valid_areas)
        self._setup_lists()
        self.worldList.selectionModel().currentChanged.connect(self._update_areas)
        self.searchLineEdit.textEdited.connect(self._update_search)
        self.searchLineEdit.returnPressed.connect(self._confirm_selection)
        self.confirmButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.searchLineEdit.setFocus()
        if window_title:
            self.setWindowTitle(window_title)
        if header_text:
            self.headerLabel.setText(header_text)
        else:
            self.headerLabel.hide()
            self.headerLine.hide()
        # Cheap way of setting up the window to pick nodes or just areas
        if self._pick_node:
            self.areaList.selectionModel().currentChanged.connect(self._update_nodes)
            self.nodeList.selectionModel().currentChanged.connect(self._node_selected)
            self.locationsCheckBox.stateChanged.connect(self._model.set_show_locations)
            self.pickupsCheckBox.stateChanged.connect(self._model.set_show_pickups)
            self.eventsCheckBox.stateChanged.connect(self._model.set_show_events)
            self.nodeList.doubleClicked.connect(self._confirm_selection)
        else:
            self.areaList.selectionModel().currentChanged.connect(self._area_selected)
            self.areaList.doubleClicked.connect(self._confirm_selection)
            self.nodeLabel.hide()
            self.nodeList.hide()
            self.filterLabel.hide()
            self.locationsCheckBox.hide()
            self.pickupsCheckBox.hide()
            self.eventsCheckBox.hide()
            self.resize(534, self.height())

    def _setup_lists(self):
        self.worldList.setModel(self._model)
        self.areaList.setModel(self._model)
        self.nodeList.setModel(self._model)
        self._empty_index = self.worldList.rootIndex()
        self.worldList.setRootIndex(self._model.index(0, 0))
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
        if self.current_node or not self._pick_node and self.current_area:
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
        self.current_node = node.data(Qt.UserRole)
        self._enable_confirm(node.isValid())

    def _area_selected(self, area: QtCore.QModelIndex):
        self.current_area = area.data(Qt.UserRole)
        self._enable_confirm(area.isValid())

    def _enable_confirm(self, enable: bool):
        self.confirmButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enable)

    def _update_search(self, text: str):
        if not text:
            return
        text = text.lower()
        for world_index, area_index in self._model.all_areas():
            if area_index.data(Qt.UserRole).name.lower().startswith(text):
                self.worldList.selectionModel().setCurrentIndex(world_index, QtCore.QItemSelectionModel.SelectCurrent)
                self.areaList.selectionModel().setCurrentIndex(area_index, QtCore.QItemSelectionModel.SelectCurrent)
                self.nodeList.selectionModel().setCurrentIndex(self._model.index(0, 0, area_index), QtCore.QItemSelectionModel.SelectCurrent)
                return
