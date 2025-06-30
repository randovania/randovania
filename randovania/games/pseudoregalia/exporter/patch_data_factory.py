from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.games.pseudoregalia.exporter.hint_namer import PseudoregaliaHintNamer
from randovania.games.pseudoregalia.layout import PseudoregaliaConfiguration, PseudoregaliaCosmeticPatches
from randovania.generator.pickup_pool.pickup_creator import create_visual_nothing

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer


class PseudoregaliaPatchDataFactory(PatchDataFactory[PseudoregaliaConfiguration, PseudoregaliaCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.PSEUDOREGALIA

    def create_visual_nothing(self):
        return create_visual_nothing(self.game_enum(), "Nothing")

    def create_game_specific_data(self) -> dict:
        start_node = self.game.region_list.node_by_identifier(self.patches.starting_location)

        level_data = {}

        for pickup_details in self.export_pickup_list():
            pickup_node = self.game.region_list.node_from_pickup_index(pickup_details.index)
            region_name = self.game.region_list.region_name_from_node(pickup_node)
            if region_name not in level_data:
                level_data[region_name] = {
                    "pickups": [],
                }

            level_data[region_name]["pickups"].append(
                {
                    "index": pickup_details.index.index,
                    "pickupType": pickup_details.original_pickup.name,
                }
            )

        return {
            "gameConfig": {"startingRoom": start_node.extra["start_tag"], "majorKeyHints": {}},
            "levelData": level_data,
        }

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return PseudoregaliaHintNamer
