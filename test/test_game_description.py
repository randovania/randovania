from randovania.game_description import RequirementSet, SimpleResourceInfo, IndividualRequirement, RequirementList


def test_empty_requirement_set():
    assert not RequirementSet([]).satisfied({})


def test_empty_requirement_list():
    assert RequirementList([]).satisfied({})


def test_simplify_requirement_set():
    req_a = SimpleResourceInfo(0, "A", "A")
    req_b = SimpleResourceInfo(0, "B", "B")

    id_req_a = IndividualRequirement(req_a, 1, False)
    id_req_b = IndividualRequirement(req_b, 1, False)

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_b]),
    ])

    simple_1 = the_set.simplify({req_a: 0, req_b: 0})
    simple_2 = the_set.simplify({req_a: 0, req_b: 1})
    simple_3 = the_set.simplify({req_a: 1, req_b: 1})

    assert simple_1.alternatives == frozenset()
    assert simple_2.alternatives == frozenset([tuple()])
    assert simple_3.alternatives == frozenset([tuple()])
ws

