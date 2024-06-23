from __future__ import annotations

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.games.prime3.layout.corruption_cosmetic_patches import CorruptionCosmeticPatches
from randovania.games.prime3.patcher import gollop_corruption_patcher


class CorruptionPatchDataFactory(PatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_CORRUPTION

    def create_game_specific_data(self) -> dict:
        cosmetic = self.cosmetic_patches
        assert isinstance(cosmetic, CorruptionCosmeticPatches)
        configuration = self.configuration
        assert isinstance(configuration, CorruptionConfiguration)
        patches = self.patches
        game = self.game

        pickup_names = []
        for index in range(game.region_list.num_pickup_nodes):
            p_index = PickupIndex(index)
            if p_index in patches.pickup_assignment:
                name = patches.pickup_assignment[p_index].pickup.name
            else:
                name = "Missile Expansion"
            pickup_names.append(name)

        layout_string = gollop_corruption_patcher.layout_string_for_items(pickup_names)
        starting_location = patches.starting_location

        starting_items = patches.starting_resources()
        starting_items.add_resource_gain(
            [
                (
                    game.resource_database.get_item_by_name("Suit Type"),
                    cosmetic.player_suit.value,
                ),
            ]
        )
        if configuration.start_with_corrupted_hypermode:
            hypermode_original = 0
        else:
            hypermode_original = 1

        starting_items_text = gollop_corruption_patcher.starting_items_for(starting_items, hypermode_original)
        starting_location_text = gollop_corruption_patcher.starting_location_for(
            game, starting_location.area_identifier
        )
        commands = "\n".join(
            [
                f'set seed="{layout_string}"',
                f'set "starting_items={starting_items_text}"',
                f'set "starting_location={starting_location_text}"',
                f'set "random_door_colors={str(cosmetic.random_door_colors).lower()}"',
                f'set "random_welding_colors={str(cosmetic.random_welding_colors).lower()}"',
            ]
        )

        return {"commands": commands}
