from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.db.dock import DockType
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class DockWeaknessDistributionDetailsTab(BaseConnectionDetailsTab):
    """Displays details for the results of the Dock Weakness Distribution, for one specific dock type."""

    @classmethod
    def dock_type(cls, game: GameDatabaseView) -> DockType:
        """What dock type are we displaying details of?"""
        raise NotImplementedError

    @classmethod
    @override
    def should_appear_for(
        cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        return configuration.dock_rando.is_enabled_for(
            cls.dock_type(all_patches[players.player_index].game),
        )

    @override
    def _fill_per_region_connections(
        self,
        per_region: dict[str, dict[str, str | dict[str, str]]],
        game: GameDatabaseView,
        patches: GamePatches,
    ) -> None:
        dock_type = self.dock_type(game)

        for source, weakness in patches.all_dock_weaknesses(game, dock_type):
            source_region = source.identifier.region
            source_area = source.identifier.area
            if source_area not in per_region[source_region]:
                per_region[source_region][source_area] = {}

            target = per_region[source_region][source_area]
            assert isinstance(target, dict)
            target[source.name] = weakness.long_name
