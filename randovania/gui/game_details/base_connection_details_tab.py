from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.layout import filtered_database
from randovania.lib.container_lib import iterate_key_sorted

if TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class BaseConnectionDetailsTab(GameDetailsTab):
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.tree_widget = QtWidgets.QTreeWidget(parent)

    def widget(self) -> QtWidgets.QWidget:
        return self.tree_widget

    def tab_title(self) -> str:
        raise NotImplementedError

    def _fill_per_region_connections(
        self,
        per_region: dict[str, dict[str, str | dict[str, str]]],
        region_list: RegionList,
        patches: GamePatches,
    ):
        raise NotImplementedError

    def update_content(
        self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ):
        self.tree_widget.clear()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Source", "Destination"])

        region_list = filtered_database.game_description_for_layout(configuration).region_list
        patches = all_patches[players.player_index]

        per_region: dict[str, dict[str, str | dict[str, str]]] = collections.defaultdict(dict)
        self._fill_per_region_connections(per_region, region_list, patches)

        for region_name, region_contents in iterate_key_sorted(per_region):
            region_item = QtWidgets.QTreeWidgetItem(self.tree_widget)
            region_item.setText(0, region_name)
            region_item.setExpanded(True)
            for source_name, destination in iterate_key_sorted(region_contents):
                area_item = QtWidgets.QTreeWidgetItem(region_item)
                area_item.setText(0, source_name)

                if isinstance(destination, str):
                    area_item.setText(1, destination)
                else:
                    area_item.setExpanded(True)
                    for node_name, node_value in destination.items():
                        node_item = QtWidgets.QTreeWidgetItem(area_item)
                        node_item.setText(0, node_name)
                        node_item.setText(1, node_value)

        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
