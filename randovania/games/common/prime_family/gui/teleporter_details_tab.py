from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.patching.prime import elevators


class TeleporterDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        if self.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION:
            return "Teleporters"
        return "Elevators"

    @classmethod
    def should_appear_for(cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches],
                          players: PlayersConfiguration) -> bool:
        assert isinstance(configuration, (PrimeConfiguration, EchoesConfiguration))
        return not configuration.elevators.is_vanilla

    def _fill_per_world_connections(self,
                                    per_world: dict[str, dict[str, str]],
                                    world_list: WorldList,
                                    patches: GamePatches,
                                    ):
        for source, destination_loc in patches.all_elevator_connections():
            source_world = world_list.world_by_area_location(source.identifier.area_identifier)
            source_name = elevators.get_elevator_or_area_name(self.game_enum, world_list,
                                                              source.identifier.area_identifier, True)

            per_world[source_world.name][source_name] = elevators.get_elevator_or_area_name(self.game_enum, world_list,
                                                                                            destination_loc, True)
