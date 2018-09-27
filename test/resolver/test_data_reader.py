import copy

from randovania.games.prime import binary_data
from randovania.resolver import data_reader
from randovania.resolver.data_reader import add_requirement_to_set
from randovania.resolver.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.resolver.resources import SimpleResourceInfo


def test_add_requirement_to_set():
    req_a = SimpleResourceInfo(0, "A", "A", "")
    req_b = SimpleResourceInfo(0, "B", "B", "")
    req_c = SimpleResourceInfo(0, "C", "C", "")

    id_req_a = IndividualRequirement(req_a, 1, False)
    id_req_c = IndividualRequirement(req_c, 1, False)

    the_set = RequirementSet([
        RequirementList([id_req_a]),
    ])
    new_set = add_requirement_to_set(the_set, id_req_c)

    assert the_set != new_set
    for the_set_list, new_set_list in zip(the_set.alternatives,
                                          new_set.alternatives):
        assert the_set_list.union([id_req_c]) == new_set_list


def test_copy_worlds():
    data = binary_data.decode_default_prime2()
    game_description = data_reader.decode_data(data, [])

    worlds_copy = copy.deepcopy(game_description.worlds)

    assert worlds_copy == game_description.worlds
    assert worlds_copy is not game_description.worlds
