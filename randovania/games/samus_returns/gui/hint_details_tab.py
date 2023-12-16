from __future__ import annotations

import collections
import random
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.games.samus_returns.exporter.hint_namer import MSRHintNamer
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.layout import filtered_database
from randovania.lib.container_lib import iterate_key_sorted

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class MSRHintDetailsTab(GameDetailsTab):
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.tree_widget = QtWidgets.QTreeWidget(parent)

    def widget(self) -> QtWidgets.QWidget:
        return self.tree_widget

    def tab_title(self) -> str:
        return "Hints"

    def update_content(
        self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> None:
        self.tree_widget.clear()
        self.tree_widget.setColumnCount(3)
        self.tree_widget.setHeaderLabels(["Hint", "Pickup", "In-Game Text"])

        game = filtered_database.game_description_for_layout(configuration)
        region_list = game.region_list
        patches = all_patches[players.player_index]

        per_region: dict[str, dict[str, tuple[str, str]]] = collections.defaultdict(dict)
        namer = MSRHintNamer(all_patches, players)
        exporter = HintExporter(namer, random.Random(0), ["A joke hint."])

        for identifier, hint in patches.hints.items():
            node = game.region_list.node_by_identifier(identifier)
            source_region = region_list.nodes_to_region(node)
            source_name = region_list.node_name(node)

            hint_text = exporter.create_message_for_hint(hint, all_patches, players, False).strip()

            # FIXME: tell the room name instead of the pickup name
            if hint.target is None:
                hinted_pickup = ""
            else:
                target = patches.pickup_assignment.get(hint.target)
                if target is None:
                    hinted_pickup = "Nothing"
                else:
                    hinted_pickup = target.pickup.name
                    if players.is_multiworld:
                        hinted_pickup = f"{players.player_names[target.player]}'s {hinted_pickup}"

            per_region[source_region.name][source_name] = (hint_text, hinted_pickup)

        for region_name, region_contents in iterate_key_sorted(per_region):
            region_item = QtWidgets.QTreeWidgetItem(self.tree_widget)
            region_item.setText(0, region_name)
            region_item.setExpanded(True)
            for source_name, content in iterate_key_sorted(region_contents):
                area_item = QtWidgets.QTreeWidgetItem(region_item)
                area_item.setText(0, source_name)
                area_item.setText(1, content[1])
                area_item.setText(2, content[0])

        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
        self.tree_widget.resizeColumnToContents(3)
