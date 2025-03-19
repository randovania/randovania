from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory

if TYPE_CHECKING:
    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches


class FusionBasePatchesFactory(BasePatchesFactory[FusionConfiguration]):
    def apply_static_dock_weakness(
        self, configuration: FusionConfiguration, game: GameDescription, initial_patches: GamePatches
    ) -> GamePatches:
        get_node = game.region_list.typed_node_by_identifier

        dock_weakness: list[tuple[DockNode, DockWeakness]] = []
        open_transition_door = game.dock_weakness_database.get_by_weakness("Door", "Open Hatch")

        if configuration.unlock_sector_hub:
            for dock_node in game.region_list.iterate_nodes_of_type(DockNode):
                if dock_node.extra.get("sector_hub_elevator_door"):
                    dock_weakness.append((dock_node, open_transition_door))

        if configuration.open_save_recharge_hatches:
            for area in game.region_list.all_areas:
                if configuration.open_save_recharge_hatches and area.extra.get("unlocked_save_recharge_station"):
                    for node in area.nodes:
                        if isinstance(node, DockNode) and node.dock_type.short_name == "Door":
                            if node.default_dock_weakness != open_transition_door:
                                dock_weakness.append((node, open_transition_door))
                                # TODO: This is not correct in entrance rando
                                dock_weakness.append(
                                    (get_node(node.default_connection, DockNode), open_transition_door)
                                )

        return initial_patches.assign_dock_weakness(dock_weakness)
