import copy

from randovania.game_description.default_database import default_prime2_game_description


def test_copy_worlds():
    game_description = default_prime2_game_description()
    game_copy = copy.deepcopy(game_description)

    assert game_description.world_list.worlds == game_copy.world_list.worlds
    assert game_description.world_list.worlds is not game_copy.world_list.worlds
