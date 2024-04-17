from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.prime2.gui.preset_settings.echoes_translators_tab import gate_data
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.layout import filtered_database
from randovania.lib.container_lib import iterate_key_sorted

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class TranslatorGateDetailsTab(GameDetailsTab):
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.tree_widget = QtWidgets.QTreeWidget(parent)

    def widget(self) -> QtWidgets.QWidget:
        return self.tree_widget

    def tab_title(self) -> str:
        return "Translator Gate"

    def update_content(
        self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ):
        self.tree_widget.clear()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Gate", "Requirement"])

        game = filtered_database.game_description_for_layout(configuration)
        region_list = game.region_list
        patches = all_patches[players.player_index]

        gate_index_to_name, identifier_to_gate = gate_data()
        resource_db = game.resource_database

        per_region: dict[str, dict[str, str]] = collections.defaultdict(dict)

        for source_loc, requirement in patches.game_specific["translator_gates"].items():
            source_loc = NodeIdentifier.from_string(source_loc)
            requirement = LayoutTranslatorRequirement(requirement)

            source_region = region_list.region_by_area_location(source_loc.area_identifier)
            source_name = gate_index_to_name[identifier_to_gate[source_loc]]

            per_region[source_region.name][source_name] = resource_db.get_item(requirement.item_name).long_name

        for region_name, region_contents in iterate_key_sorted(per_region):
            region_item = QtWidgets.QTreeWidgetItem(self.tree_widget)
            region_item.setText(0, region_name)
            region_item.setExpanded(True)
            for source_name, destination in iterate_key_sorted(region_contents):
                area_item = QtWidgets.QTreeWidgetItem(region_item)
                area_item.setText(0, source_name)
                area_item.setText(1, destination)

        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
