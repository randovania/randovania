from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from randovania.game_description.db.node import Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.region_list import RegionList
from randovania.gui.lib import signal_handling

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region


class NodeSelectorWidget(QtWidgets.QWidget):
    SelectedNodeChanged = QtCore.Signal()

    def __init__(self, region_list: RegionList, node_filter_criteria: Callable[[Node], bool]):
        super().__init__()
        self.region_list = region_list
        self.node_filter_criteria = node_filter_criteria

        self.line_layout = QtWidgets.QHBoxLayout()
        self.line_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.line_layout)

        self.region_combo = QtWidgets.QComboBox(self)
        self.area_combo = QtWidgets.QComboBox(self)
        self.node_combo = QtWidgets.QComboBox(self)
        self.line_layout.addWidget(self.region_combo)
        self.line_layout.addWidget(self.area_combo)
        self.line_layout.addWidget(self.node_combo)

        for region in sorted(region_list.regions, key=lambda x: x.name):
            self.region_combo.addItem(region.name, userData=region)
        assert self.region_combo.count() > 0

        signal_handling.refresh_if_needed(self.region_combo, self.on_region_combo)
        self.region_combo.currentIndexChanged.connect(self.on_region_combo)
        self.area_combo.currentIndexChanged.connect(self.on_area_combo)
        self.node_combo.currentIndexChanged.connect(self.on_node_combo)

    def on_region_combo(self, _: int) -> None:
        region: Region = self.region_combo.currentData()

        signal_handling.clear_without_notify(self.area_combo)
        for area in sorted(region.areas, key=lambda x: x.name):
            if area.nodes:
                self.area_combo.addItem(area.name, userData=area)
        assert self.area_combo.count() > 0

    def on_area_combo(self, _: int) -> None:
        area: Area | None = self.area_combo.currentData()
        assert area is not None

        signal_handling.clear_without_notify(self.node_combo)
        for node in area.nodes:
            if self.node_filter_criteria(node):
                self.node_combo.addItem(node.name, userData=node)

        if not self.node_combo.count():
            self.node_combo.addItem("<No Valid Options>", userData=None)

    def on_node_combo(self, _: None) -> None:
        self.SelectedNodeChanged.emit()

    def select_by_identifier(self, identifier: NodeIdentifier) -> None:
        self.region_list.node_by_identifier(identifier)  # asserts that identifier points to a valid node
        self.region_combo.setCurrentIndex(self.region_combo.findText(identifier.region))
        self.area_combo.setCurrentIndex(self.area_combo.findText(identifier.area))
        self.node_combo.setCurrentIndex(self.node_combo.findText(identifier.node))

    def selected_node(self) -> Node | None:
        return self.node_combo.currentData()
