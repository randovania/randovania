from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class DockLockDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        return "Door Locks"

    @classmethod
    def should_appear_for(
        cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        return configuration.dock_rando.is_enabled()

    def _fill_per_region_connections(
        self,
        per_region: dict[str, dict[str, str | dict[str, str]]],
        game: GameDatabaseView,
        patches: GamePatches,
    ) -> None:
        for source, weakness in patches.all_dock_weaknesses(game):
            source_region = source.identifier.region
            source_area = source.identifier.area
            if source_area not in per_region[source_region]:
                per_region[source_region][source_area] = {}

            target = per_region[source_region][source_area]
            assert isinstance(target, dict)
            target[source.name] = weakness.long_name
