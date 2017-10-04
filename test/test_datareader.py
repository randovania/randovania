from randovania.datareader import add_requirement_to_set
from randovania.game_description import RequirementSet, RequirementList, IndividualRequirement, SimpleResourceInfo


def test_add_requirement_to_set():
    req_a = SimpleResourceInfo(0, "A", "A")
    req_b = SimpleResourceInfo(0, "B", "B")
    req_c = SimpleResourceInfo(0, "C", "C")

    id_req_a = IndividualRequirement(req_a, 1, False)
    id_req_b = IndividualRequirement(req_b, 1, False)
    id_req_c = IndividualRequirement(req_c, 1, False)

    the_set = RequirementSet(tuple([
        RequirementList([id_req_a]),
        RequirementList([id_req_b]),
    ]))
    new_set = add_requirement_to_set(the_set, id_req_c)

    assert the_set != new_set
    for i in range(2):
        assert the_set.alternatives[i] + (id_req_c,) == new_set.alternatives[i]

