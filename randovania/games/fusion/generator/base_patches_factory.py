from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory, weaknesses_for_unlocked_saves

if TYPE_CHECKING:
    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches


class FusionBasePatchesFactory(BasePatchesFactory[FusionConfiguration]):
    def assign_static_dock_weakness(
        self, configuration: FusionConfiguration, game: GameDescription, initial_patches: GamePatches
    ) -> GamePatches:
        parent = super().assign_static_dock_weakness(configuration, game, initial_patches)

        dock_weakness: list[tuple[DockNode, DockWeakness]] = []
        open_transition_door = game.dock_weakness_database.get_by_weakness("Door", "Open Hatch")

        if configuration.unlock_sector_hub:
            for dock_node in game.region_list.iterate_nodes_of_type(DockNode):
                if dock_node.extra.get("sector_hub_elevator_door"):
                    dock_weakness.append((dock_node, open_transition_door))

        if configuration.open_save_recharge_hatches:
            dock_weakness.extend(
                weaknesses_for_unlocked_saves(
                    game,
                    unlocked_weakness=open_transition_door,
                    target_dock_type=game.dock_weakness_database.find_type("Door"),
                    area_filter=lambda area: area.extra.get("unlocked_save_recharge_station") is True,
                    dock_filter=lambda node: node.default_dock_weakness != open_transition_door,
                )
            )

        return parent.assign_dock_weakness(dock_weakness)
