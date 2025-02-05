from __future__ import annotations

import collections
import random
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.hint import LocationHint
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.layout import filtered_database
from randovania.lib.container_lib import iterate_key_sorted
from randovania.lib.enum_lib import enum_definition_order

if TYPE_CHECKING:
    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.hint import Hint
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class HintDetailsTab(GameDetailsTab):
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.tree_widget = QtWidgets.QTreeWidget(parent)
        self.tree_widget.setWordWrap(True)

    def widget(self) -> QtWidgets.QWidget:
        return self.tree_widget

    def tab_title(self) -> str:
        return "Hints"

    def update_content(
        self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ):
        NUM_COLUMNS = 4

        self.tree_widget.clear()
        self.tree_widget.setColumnCount(NUM_COLUMNS)
        self.tree_widget.setHeaderLabels(["Hint", "Pickup", "Location", "In-Game Text"])

        game = filtered_database.game_description_for_layout(configuration)
        region_list = game.region_list
        patches = all_patches[players.player_index]

        per_region: dict[str, dict[HintNode, tuple[str, str, str]]] = collections.defaultdict(dict)
        exporter = game.game.data.patch_data_factory().get_hint_exporter(
            all_patches,
            players,
            random.Random(0),
            ["A joke hint."],
        )

        # sort by kind, then type, for ease of reading
        def keyfunc(item: tuple[NodeIdentifier, Hint]) -> tuple[int, int, HintNode]:
            hint_node = region_list.typed_node_by_identifier(item[0], HintNode)
            hint_kind = -enum_definition_order(hint_node.kind)
            hint_type = enum_definition_order(item[1].hint_type())

            return hint_kind, hint_type, hint_node

        for identifier, hint in sorted(patches.hints.items(), key=keyfunc):
            node = region_list.typed_node_by_identifier(identifier, HintNode)
            source_region = region_list.nodes_to_region(node)

            hint_text = exporter.create_message_for_hint(hint, False)

            if not isinstance(hint, LocationHint):
                hinted_pickup = ""
                hinted_location = ""
            else:
                hinted_node = region_list.node_from_pickup_index(hint.target)
                hinted_location = region_list.node_name(hinted_node, True, True)

                target = patches.pickup_assignment.get(hint.target)
                if target is None:
                    hinted_pickup = "Nothing"
                else:
                    hinted_pickup = target.pickup.name
                    if players.is_multiworld:
                        hinted_pickup = f"{players.player_names[target.player]}'s {hinted_pickup}"

            per_region[source_region.name][node] = (hinted_pickup, hinted_location, hint_text)

        for region_name, region_contents in iterate_key_sorted(per_region):
            region_item = QtWidgets.QTreeWidgetItem(self.tree_widget)
            region_item.setText(0, region_name)
            region_item.setExpanded(True)
            for node, content in region_contents.items():
                source_name = region_list.node_name(node)
                area_item = QtWidgets.QTreeWidgetItem(region_item)
                area_item.setText(0, source_name)
                for i in range(1, NUM_COLUMNS):
                    area_item.setText(i, content[i - 1])

        for i in range(NUM_COLUMNS):
            self.tree_widget.resizeColumnToContents(i)
