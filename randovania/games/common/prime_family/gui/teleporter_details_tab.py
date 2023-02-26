import collections

from PySide6 import QtWidgets

from randovania.game_description.game_patches import GamePatches
from randovania.games.game import RandovaniaGame
from randovania.gui.game_details.game_details_tab import GameDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.lib.dict_lib import iterate_key_sorted
from randovania.patching.prime import elevators


class TeleporterDetailsTab(GameDetailsTab):
    def __init__(self, parent: QtWidgets.QWidget, game: RandovaniaGame):
        super().__init__(parent, game)
        self.tree_widget = QtWidgets.QTreeWidget(parent)

    def widget(self) -> QtWidgets.QWidget:
        return self.tree_widget

    def tab_title(self) -> str:
        if self.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION:
            return "Teleporters"
        return "Elevators"

    def update_content(self, configuration: BaseConfiguration, all_patches: dict[int, GamePatches],
                       players: PlayersConfiguration):
        self.tree_widget.clear()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Source", "Destination"])

        world_list = filtered_database.game_description_for_layout(configuration).world_list
        patches = all_patches[players.player_index]

        per_world: dict[str, dict[str, str]] = collections.defaultdict(dict)

        for source, destination_loc in patches.all_elevator_connections():
            source_world = world_list.world_by_area_location(source.identifier.area_identifier)
            source_name = elevators.get_elevator_or_area_name(self.game_enum, world_list,
                                                              source.identifier.area_identifier, True)

            per_world[source_world.name][source_name] = elevators.get_elevator_or_area_name(self.game_enum, world_list,
                                                                                            destination_loc, True)

        for world_name, world_contents in iterate_key_sorted(per_world):
            world_item = QtWidgets.QTreeWidgetItem(self.tree_widget)
            world_item.setText(0, world_name)
            world_item.setExpanded(True)
            for source_name, destination in iterate_key_sorted(world_contents):
                area_item = QtWidgets.QTreeWidgetItem(world_item)
                area_item.setText(0, source_name)
                area_item.setText(1, destination)

        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
