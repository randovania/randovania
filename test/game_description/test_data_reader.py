import copy

from randovania.game_description.default_database import default_prime2_game_description


def test_copy_worlds():
    game_description = default_prime2_game_description()
    worlds_copy = copy.deepcopy(game_description.worlds)

    assert worlds_copy == game_description.worlds
    assert worlds_copy is not game_description.worlds
