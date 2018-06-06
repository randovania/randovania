import pytest

from randovania.resolver.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.resolver.resources import SimpleResourceInfo, ResourceDatabase


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
        pickups=[]
    )


def test_empty_requirement_set():
    assert not RequirementSet([]).satisfied({})


def test_empty_requirement_list():
    assert RequirementList([]).satisfied({})


def test_simplify_requirement_set_static(database):
    res_a = SimpleResourceInfo(0, "A", "A")
    res_b = SimpleResourceInfo(0, "B", "B")

    id_req_a = IndividualRequirement(res_a, 1, False)
    id_req_b = IndividualRequirement(res_b, 1, False)

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_b]),
    ])

    simple_1 = the_set.simplify({res_a: 0, res_b: 0}, database)
    simple_2 = the_set.simplify({res_a: 0, res_b: 1}, database)
    simple_3 = the_set.simplify({res_a: 1, res_b: 1}, database)

    assert simple_1.alternatives == frozenset()
    assert simple_2.alternatives == frozenset([RequirementList()])
    assert simple_3.alternatives == frozenset([RequirementList()])


def test_prevent_redundant():
    res_a = SimpleResourceInfo(0, "A", "A")
    res_b = SimpleResourceInfo(0, "B", "B")

    id_req_a = IndividualRequirement(res_a, 1, False)
    id_req_b = IndividualRequirement(res_b, 1, False)

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_a, id_req_b]),
    ])

    assert the_set.alternatives == frozenset([RequirementList([id_req_a])])


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
