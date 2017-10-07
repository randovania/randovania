import pytest

from randovania.resolver.game_description import RequirementSet, SimpleResourceInfo, IndividualRequirement, \
    RequirementList, ResourceDatabase


@pytest.fixture
def database():
    return ResourceDatabase(
        item=[],
        event=[],
        trick=[],
        damage=[],
        version=[],
        misc=[
            SimpleResourceInfo(0, "Trivial", "Trivial"),
            SimpleResourceInfo(1, "Impossible", "Impossible"),
        ],
        difficulty=[],
    )


def test_empty_requirement_set():
    assert not RequirementSet([]).satisfied({})


def test_empty_requirement_list():
    assert RequirementList([]).satisfied({})


def test_simplify_requirement_set(database):
    req_a = SimpleResourceInfo(0, "A", "A")
    req_b = SimpleResourceInfo(0, "B", "B")

    id_req_a = IndividualRequirement(req_a, 1, False)
    id_req_b = IndividualRequirement(req_b, 1, False)

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_b]),
    ])

    simple_1 = the_set.simplify({req_a: 0, req_b: 0}, database)
    simple_2 = the_set.simplify({req_a: 0, req_b: 1}, database)
    simple_3 = the_set.simplify({req_a: 1, req_b: 1}, database)

    assert simple_1.alternatives == frozenset()
    assert simple_2.alternatives == frozenset([RequirementList()])
    assert simple_3.alternatives == frozenset([RequirementList()])


def test_trivial_merge():
    trivial = RequirementSet.trivial()
    impossible = RequirementSet.impossible()

    req_a = SimpleResourceInfo(0, "A", "A")
    id_req_a = IndividualRequirement(req_a, 1, False)
    the_set = RequirementSet([
        RequirementList([id_req_a]),
    ])

    assert trivial.merge(trivial) == trivial
    assert trivial.merge(the_set) == the_set
    assert the_set.merge(trivial) == the_set
    assert trivial.merge(impossible) == impossible
    assert impossible.merge(the_set) == impossible
    assert the_set.merge(impossible) == impossible
    assert the_set.merge(the_set) == the_set
