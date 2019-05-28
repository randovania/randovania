from typing import Tuple
from unittest.mock import MagicMock

import pytest

from randovania.game_description.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


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
    return RequirementSet([RequirementList(0, [id_req[1]])])


def test_empty_requirement_set():
    assert not RequirementSet([]).satisfied({}, 99)


def test_empty_requirement_list():
    assert RequirementList(0, []).satisfied({}, 99)


def test_simplify_requirement_set_static():
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()

    the_set = RequirementSet([
        RequirementList(0, [id_req_a]),
        RequirementList(0, [id_req_b]),
    ])

    simple_1 = the_set.simplify({res_a: 0, res_b: 0})
    simple_2 = the_set.simplify({res_a: 0, res_b: 1})
    simple_3 = the_set.simplify({res_a: 1, res_b: 1})

    assert simple_1.alternatives == frozenset()
    assert simple_2.alternatives == frozenset([RequirementList(0, [])])
    assert simple_3.alternatives == frozenset([RequirementList(0, [])])


def test_prevent_redundant():
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()

    the_set = RequirementSet([
        RequirementList(0, [id_req_a]),
        RequirementList(0, [id_req_a, id_req_b]),
    ])

    assert the_set.alternatives == frozenset([RequirementList(0, [id_req_a])])


def test_trivial_merge():
    trivial = RequirementSet.trivial()
    impossible = RequirementSet.impossible()
    res_a, id_req_a = make_req_a()

    the_set = RequirementSet([
        RequirementList(0, [id_req_a]),
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
    RequirementSet([RequirementList(0, [make_req_a()[1], make_req_b()[1]])]),
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
     RequirementSet([RequirementList(0, [make_req_a()[1]]), RequirementList(0, [make_req_b()[1]])])),
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
        RequirementList(0, [id_req_a]),
        RequirementList(1, [id_req_b, IndividualRequirement(database.difficulty_resource, 1, False)]),
        RequirementList(2, [id_req_c, IndividualRequirement(database.difficulty_resource, 2, False)]),
    ])

    res = {
        database.get_by_type_and_index(ResourceType.ITEM, x): 1
        for x in resources
    }
    res[database.difficulty_resource] = 10
    diff = the_set.minimum_satisfied_difficulty(res, 99)
    assert diff == expected_level


@pytest.mark.parametrize(["input_data", "output_data"], [
    ([], []),
    ([(0, False)], []),
    ([(0, True)], [0]),
    ([(0, True), (0, False)], [0]),
    ([(0, True), (1, False)], [0]),
    ([(0, True), (1, True)], [0, 1]),
])
def test_list_dangerous_resources(input_data, output_data):
    # setup
    req_list = RequirementList(
        0,
        (IndividualRequirement(SimpleResourceInfo(item[0], str(item[0]), str(item[0]), ""), 1, item[1])
         for item in input_data)
    )
    expected_result = {
        SimpleResourceInfo(item, str(item), str(item), "")
        for item in output_data
    }

    # run
    result = set(req_list.dangerous_resources)

    # assert
    assert result == expected_result


def test_set_dangerous_resources():
    # setup
    list_a = MagicMock()
    list_b = MagicMock()
    list_a.dangerous_resources = [1, 2, 3]
    list_b.dangerous_resources = ["a", "b", "c"]

    req_set = RequirementSet([])
    req_set.alternatives = frozenset([list_a, list_b])

    # Run
    result = set(req_set.dangerous_resources)

    # Assert
    assert result == {1, 2, 3, "a", "b", "c"}
