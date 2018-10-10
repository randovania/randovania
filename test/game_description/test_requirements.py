from typing import Tuple

import pytest

from randovania.game_description.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.game_description.resources import SimpleResourceInfo, ResourceDatabase, ResourceType


@pytest.fixture(name="database")
def _database() -> ResourceDatabase:
    return ResourceDatabase(
        item=[
            SimpleResourceInfo(0, "A", "A", ""),
            SimpleResourceInfo(1, "B", "B", ""),
            SimpleResourceInfo(2, "C", "C", ""),
        ],
        event=[],
        trick=[],
        damage=[],
        version=[],
        misc=[
            SimpleResourceInfo(0, "Trivial", "Trivial", ""),
            SimpleResourceInfo(1, "Impossible", "Impossible", ""),
        ],
        difficulty=[
            SimpleResourceInfo(0, "Difficulty", "Difficulty", ""),
        ],
        pickups=[]
    )


def _make_req(name: str, index: int):
    req = SimpleResourceInfo(index, name, name, "")
    id_req = IndividualRequirement(req, 1, False)
    return req, id_req


def make_req_a():
    return _make_req("A", 0)


def make_req_b():
    return _make_req("B", 1)


def make_req_c():
    return _make_req("C", 2)


def make_single_set(id_req: Tuple[SimpleResourceInfo, IndividualRequirement]) -> RequirementSet:
    return RequirementSet([RequirementList([id_req[1]])])


def test_empty_requirement_set(database):
    assert not RequirementSet([]).satisfied({}, database)


def test_empty_requirement_list(database):
    assert RequirementList([]).satisfied({}, database)


def test_simplify_requirement_set_static(database):
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()

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
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_a, id_req_b]),
    ])

    assert the_set.alternatives == frozenset([RequirementList([id_req_a])])


def test_trivial_merge():
    trivial = RequirementSet.trivial()
    impossible = RequirementSet.impossible()
    res_a, id_req_a = make_req_a()

    the_set = RequirementSet([
        RequirementList([id_req_a]),
    ])

    assert trivial.union(trivial) == trivial
    assert trivial.union(the_set) == the_set
    assert the_set.union(trivial) == the_set
    assert trivial.union(impossible) == impossible
    assert impossible.union(the_set) == impossible
    assert the_set.union(impossible) == impossible
    assert the_set.union(the_set) == the_set


@pytest.mark.parametrize("replacement", [
    RequirementSet.impossible(),
    make_single_set(make_req_a()),
    RequirementSet([RequirementList([make_req_a()[1], make_req_b()[1]])]),
])
def test_replace_missing(replacement):
    trivial = RequirementSet.trivial()

    req_a = SimpleResourceInfo(0, "A", "A", "")
    id_req_a = IndividualRequirement(req_a, 1, False)

    result = trivial.replace(id_req_a, replacement)

    assert result == trivial


@pytest.mark.parametrize(["a", "b", "expected"], [
    (RequirementSet.impossible(), make_single_set(make_req_a()), make_single_set(make_req_a())),
    (RequirementSet.impossible(), RequirementSet.trivial(), RequirementSet.trivial()),
    (RequirementSet.trivial(), make_single_set(make_req_a()), RequirementSet.trivial()),
    (make_single_set(make_req_a()), make_single_set(make_req_b()),
     RequirementSet([RequirementList([make_req_a()[1]]), RequirementList([make_req_b()[1]])])),
])
def test_expand_alternatives(a: RequirementSet, b: RequirementSet, expected: RequirementSet):
    assert a.expand_alternatives(b) == expected


@pytest.mark.parametrize(["resources", "expected_level"], [
    ([], None),
    ([0], 0),
    ([1], 1),
    ([2], 2),
    ([1, 2], 1),
])
def test_minimum_satisfied_difficulty(database: ResourceDatabase, resources, expected_level):
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()
    res_c, id_req_c = make_req_c()
    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_b, IndividualRequirement(database.difficulty_resource, 1, False)]),
        RequirementList([id_req_c, IndividualRequirement(database.difficulty_resource, 2, False)]),
    ])

    res = {
        database.get_by_type_and_index(ResourceType.ITEM, x): 1
        for x in resources
    }
    res[database.difficulty_resource] = 10
    diff = the_set.minimum_satisfied_difficulty(res, database)
    assert diff == expected_level
