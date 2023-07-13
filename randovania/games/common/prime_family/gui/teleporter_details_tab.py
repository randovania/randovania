from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab
from randovania.patching.prime import elevators

if TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class TeleporterDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        if self.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION:
            return "Teleporters"
        return "Elevators"

    @classmethod
    def should_appear_for(cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches],
                          players: PlayersConfiguration) -> bool:
        assert isinstance(configuration, PrimeConfiguration | EchoesConfiguration)
        return not configuration.elevators.is_vanilla

    def _fill_per_region_connections(self,
                                     per_region: dict[str, dict[str, str]],
                                     region_list: RegionList,
                                     patches: GamePatches,
                                     ):
        for source, destination_loc in patches.all_dock_connections():
            source_region = region_list.region_by_area_location(source.identifier.area_identifier)
            source_name = elevators.get_elevator_or_area_name(self.game_enum, region_list,
                                                              source.identifier.area_identifier, True)

            per_region[source_region.name][source_name] = elevators.get_elevator_or_area_name(
                self.game_enum, region_list,
                destination_loc.identifier.area_identifier, True
            )
