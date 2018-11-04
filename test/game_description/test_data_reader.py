import copy

from randovania.game_description import data_reader
from randovania.game_description.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.game_description.resources import SimpleResourceInfo
from randovania.games.prime import binary_data


def test_copy_worlds():
    data = binary_data.decode_default_prime2()
    game_description = data_reader.decode_data(data, [])

    worlds_copy = copy.deepcopy(game_description.worlds)

    assert worlds_copy == game_description.worlds
    assert worlds_copy is not game_description.worlds
