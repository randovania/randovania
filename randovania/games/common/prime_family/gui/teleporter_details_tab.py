from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab
from randovania.patching.prime import elevators


class TeleporterDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        if self.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION:
            return "Teleporters"
        return "Elevators"

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
