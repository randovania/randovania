from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.common import elevators
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class TeleporterDetailsTab(BaseConnectionDetailsTab):
    @classmethod
    def should_appear_for(
        cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        raise NotImplementedError

    def _fill_per_region_connections(
        self,
        per_region: dict[str, dict[str, str]],
        game: GameDatabaseView,
        patches: GamePatches,
    ) -> None:
        for source, destination_loc in patches.all_dock_connections(game):
            # Fix for portal rando showing up in echoes tab
            if source.dock_type not in patches.game.dock_weakness_database.all_teleporter_dock_types:
                continue
            source_region = source.identifier.region
            source_name = elevators.get_elevator_or_area_name(source, True)

            per_region[source_region][source_name] = elevators.get_elevator_or_area_name(destination_loc, True)
