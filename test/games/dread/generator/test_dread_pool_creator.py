from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.generator.item_pool import pool_creator


def test_dread_pool_creator(dread_game_description, preset_manager):
    # Setup
    preset = preset_manager.default_preset_for_game(dread_game_description.game).get_preset()
    patches = GamePatches.create_from_game(dread_game_description, 0, preset.configuration)

    # Run
    results = pool_creator.calculate_pool_results(
        preset.configuration,
        dread_game_description,
        patches,
        Random(5000),
        True,
    )

    # Assert
    wl = dread_game_description.world_list
    c = NodeIdentifier.create

    locations = [
        wl.identifier_for_node(wl.node_from_pickup_index(index))
        for index in results.assignment.keys()
    ]
    assert locations == [
        c("Burenia", "Drogyga Arena", "Pickup (Drogyga)"),
        c("Cataris", "Above Z-57 Fight", "Pickup (Z-57)"),
        c("Ghavoran", "Golzuna Arena", "Pickup (Cross Bomb)"),
    ]

    assert len(results.pickups) == wl.num_pickup_nodes - 1 - len(results.assignment)
