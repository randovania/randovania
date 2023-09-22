from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
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
        region_list: RegionList,
        patches: GamePatches,
    ):
        for source, weakness in patches.all_dock_weaknesses():
            source_region, source_area = region_list.region_and_area_by_area_identifier(
                source.identifier.area_identifier
            )
            if source_area.name not in per_region[source_region.name]:
                per_region[source_region.name][source_area.name] = {}
            per_region[source_region.name][source_area.name][source.name] = weakness.long_name
