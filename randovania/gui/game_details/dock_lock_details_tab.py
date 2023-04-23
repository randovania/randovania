from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.world_list import WorldList
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration


class DockLockDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        return "Door Locks"

    @classmethod
    def should_appear_for(cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches],
                          players: PlayersConfiguration) -> bool:
        return configuration.dock_rando.is_enabled()

    def _fill_per_world_connections(self,
                                    per_world: dict[str, dict[str, str | dict[str, str]]],
                                    world_list: WorldList,
                                    patches: GamePatches,
                                    ):
        for source, weakness in patches.all_dock_weaknesses():
            source_world, source_area = world_list.world_and_area_by_area_identifier(source.identifier.area_identifier)
            if source_area.name not in per_world[source_world.name]:
                per_world[source_world.name][source_area.name] = {}
            per_world[source_world.name][source_area.name][source.name] = weakness.long_name
