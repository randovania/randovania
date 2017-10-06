from randovania.datareader import add_requirement_to_set
from randovania.game_description import RequirementSet, RequirementList, IndividualRequirement, SimpleResourceInfo


def test_add_requirement_to_set():
    req_a = SimpleResourceInfo(0, "A", "A")
    req_b = SimpleResourceInfo(0, "B", "B")
    req_c = SimpleResourceInfo(0, "C", "C")

    id_req_a = IndividualRequirement(req_a, 1, False)
    id_req_b = IndividualRequirement(req_b, 1, False)
    id_req_c = IndividualRequirement(req_c, 1, False)

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_b]),
    ])
    new_set = add_requirement_to_set(the_set, id_req_c)

    assert the_set != new_set
    for the_set_list, new_set_list in zip(sorted(the_set.alternatives), sorted(new_set.alternatives)):
        assert the_set_list + (id_req_c,) == new_set_list
