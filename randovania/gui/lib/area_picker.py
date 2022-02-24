from typing import Callable, Optional
from randovania.game_description import default_database
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.game_description.world.node import Node, NodeIdentifier
from randovania.gui.generated.area_picker_dialog_ui import Ui_AreaPickerDialog
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

def get_node(parent: QtWidgets.QWidget, game: RandovaniaGame, filter: Optional[Callable[[Node], bool]]=None) -> Optional[NodeIdentifier]:
    dialog = AreaPickerDialog(parent, game, filter)
    result = dialog.exec()
    if result == QtWidgets.QDialog.DialogCode.Accepted:
        return NodeIdentifier(AreaIdentifier(dialog.current_world.name, dialog.current_area.name), dialog.current_node.name)
    else:
        return None

class AreaPickerDialog(QtWidgets.QDialog, Ui_AreaPickerDialog):
    _world_list: list[World]
    _form: QtWidgets.QFormLayout
    world_combo_box: QtWidgets.QComboBox
    area_combo_box: QtWidgets.QComboBox
    node_combo_box: QtWidgets.QComboBox
    confirm_buttons: QtWidgets.QDialogButtonBox
    current_world: World
    current_area: Area
    current_node: Node
    filter: Optional[Callable[[Node], bool]]

    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame, filter: Optional[Callable[[Node], bool]]=None):
        super().__init__(parent)
        self.setupUi(self)
        self._world_list = default_database.game_description_for(game).world_list.worlds
        for world in self._world_list:
            item = QtWidgets.QListWidgetItem(world.name)
            item.setData(Qt.UserRole, world)
            self.worldList.addItem(item)
        self.worldList.currentItemChanged.connect(self._update_areas)
        self.areaList.currentItemChanged.connect(self._update_nodes)
        self.nodeList.currentItemChanged.connect(self._node_selected)
        self.confirmButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def _update_areas(self, world: QtWidgets.QListWidgetItem, previous: QtWidgets.QListWidgetItem):
        self.areaList.clear()
        self.nodeList.clear()
        self.current_world = None if not world else world.data(Qt.UserRole)
        if not world:
            self.areaList.setDisabled(True)
            self.nodeList.setDisabled(True)
            return
        area_list = world.data(Qt.UserRole).areas
        area_list.sort(key=lambda area: area.name)
        self.areaList.clear()
        self.areaList.setDisabled(not area_list)
        for area in area_list:
            item = QtWidgets.QListWidgetItem(area.name)
            item.setData(Qt.UserRole, area)
            self.areaList.addItem(item)

    def _update_nodes(self, area: QtWidgets.QListWidgetItem, previous: QtWidgets.QListWidgetItem):
        self.nodeList.clear()
        self.current_area = None if not area else area.data(Qt.UserRole)
        if not area:
            self.nodeList.setDisabled(True)
            return
        node_list = [node for node in area.data(Qt.UserRole).nodes if not node.is_resource_node]
        node_list.sort(key=lambda node: node.name)
        self.nodeList.setDisabled(not node_list)
        for node in node_list:
            item = QtWidgets.QListWidgetItem(node.name)
            item.setData(Qt.UserRole, node)
            self.nodeList.addItem(item)

    def _node_selected(self, node: QtWidgets.QListWidgetItem, previous: QtWidgets.QListWidgetItem):
        self._enable_confirm(node is not None)
        self.current_node = None if not node else node.data(Qt.UserRole)

    def _enable_confirm(self, enable: bool):
        self.confirmButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enable)