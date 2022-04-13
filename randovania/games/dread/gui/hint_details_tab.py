import collections
import random

from PySide6 import QtWidgets

from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.game_description.game_patches import GamePatches
from randovania.games.dread.exporter.hint_namer import DreadHintNamer
from randovania.games.game import RandovaniaGame
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.lib.dict_lib import iterate_key_sorted


class DreadHintDetailsTab(GameDetailsTab):
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.tree_widget = QtWidgets.QTreeWidget(parent)

    def widget(self) -> QtWidgets.QWidget:
        return self.tree_widget

    def tab_title(self) -> str:
        return "Hints"

    def update_content(self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches],
                       players: PlayersConfiguration):
        self.tree_widget.clear()
        self.tree_widget.setColumnCount(3)
        self.tree_widget.setHeaderLabels(["Hint", "Pickup", "In-Game Text"])

        game = filtered_database.game_description_for_layout(configuration)
        world_list = game.world_list
        patches = all_patches[players.player_index]

        per_world: dict[str, dict[str, tuple[str, str]]] = collections.defaultdict(dict)
        namer = DreadHintNamer(all_patches, players)
        exporter = HintExporter(namer, random.Random(0), ["A joke hint."])

        for identifier, hint in patches.hints.items():
            node = game.world_list.node_by_identifier(identifier)
            source_world = world_list.nodes_to_world(node)
            source_name = world_list.node_name(node)

            hint_text = exporter.create_message_for_hint(hint, all_patches, players, False)

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
