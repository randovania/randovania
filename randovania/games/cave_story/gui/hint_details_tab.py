import collections
from random import Random

from PySide2 import QtWidgets

from randovania.game_description import default_database
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.node import LogbookNode
from randovania.games.cave_story.patcher.caver_patcher import get_hints
from randovania.games.game import RandovaniaGame
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.lib.dict_lib import iterate_key_sorted


class HintDetailsTab(GameDetailsTab):
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.tree_widget = QtWidgets.QTreeWidget(parent)

    def widget(self) -> QtWidgets.QWidget:
        return self.tree_widget

    def tab_title(self) -> str:
        return "Hints"

    def update_content(self, configuration: BaseConfiguration, patches: GamePatches, players: PlayersConfiguration):
        self.tree_widget.clear()
        self.tree_widget.setColumnCount(3)
        self.tree_widget.setHeaderLabels(["Hint", "Pickup", "In-Game Text"])

        game = default_database.game_description_for(self.game_enum)
        world_list = game.world_list

        asset_to_node = {
            node.resource(): node
            for node in game.world_list.all_nodes
            if isinstance(node, LogbookNode)
        }

        per_world: dict[str, dict[str, tuple[str, str]]] = collections.defaultdict(dict)

        hints = get_hints({players.player_index: patches}, players, Random())
        for asset, hint in patches.hints.items():
            node = asset_to_node[asset]
            source_world = world_list.nodes_to_world(node)
            source_name = world_list.node_name(node)

            hint_text = hints[asset._string_asset_id]

            hint = patches.hints[asset]
            if hint.target is None:
                hinted_pickup = "No target for hint"
            else:
                target = patches.pickup_assignment.get(hint.target)
                if target is None:
                    hinted_pickup = "Nothing"
                else:
                    hinted_pickup = target.pickup.name
                    if players.is_multiworld:
                        hinted_pickup = f"{players.player_names[target.player]}'s {hinted_pickup}"

            per_world[source_world.name][source_name] = (hint_text, hinted_pickup)

        for world_name, world_contents in iterate_key_sorted(per_world):
            world_item = QtWidgets.QTreeWidgetItem(self.tree_widget)
            world_item.setText(0, world_name)
            world_item.setExpanded(True)
            for source_name, content in iterate_key_sorted(world_contents):
                area_item = QtWidgets.QTreeWidgetItem(world_item)
                area_item.setText(0, source_name)
                area_item.setText(1, content[1])
                area_item.setText(2, content[0])

        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
        self.tree_widget.resizeColumnToContents(3)
