from typing import Tuple
from unittest.mock import MagicMock

import pytest

from randovania.game_description import data_reader
from randovania.game_description.requirements import ResourceRequirement, RequirementList, RequirementSet, \
    RequirementAnd, RequirementOr, Requirement, MAX_DAMAGE, RequirementTemplate
from randovania.game_description.resources import search
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.games.game import RandovaniaGame


@pytest.fixture(name="database")
def _database() -> ResourceDatabase:
    return ResourceDatabase(
        game_enum=RandovaniaGame.METROID_PRIME_ECHOES,
        item=[
            ItemResourceInfo(0, "A", "A", 1, None),
            ItemResourceInfo(1, "B", "B", 1, None),
            ItemResourceInfo(2, "C", "C", 1, None),
        ],
        event=[],
        trick=[],
        damage=[],
        version=[],
        misc=[
            SimpleResourceInfo(0, "Trivial", "Trivial", ResourceType.MISC),
            SimpleResourceInfo(1, "Impossible", "Impossible", ResourceType.MISC),
        ],
        requirement_template={},
        damage_reductions={},
        energy_tank_item_index=0,
        item_percentage_index=0,
        multiworld_magic_item_index=0
    )


def _make_req(name: str):
    req = SimpleResourceInfo(hash(name), name, name, "")
    id_req = ResourceRequirement(req, 1, False)
    return req, id_req


def _req(name: str):
    return _make_req(name)[1]


def make_req_a():
    return _make_req("A")


def make_req_b():
    return _make_req("B")


def make_req_c():
    return _make_req("C")


def make_single_set(id_req: Tuple[SimpleResourceInfo, ResourceRequirement]) -> RequirementSet:
    return RequirementSet([RequirementList([id_req[1]])])


def test_empty_requirement_set_satisfied():
    assert not RequirementSet([]).satisfied({}, 99, None)


def test_empty_requirement_list_satisfied():
    assert RequirementList([]).satisfied({}, 99, None)


def test_simplify_requirement_set_static():
    res_a, id_req_a = make_req_a()
    res_b, id_req_b = make_req_b()

    the_set = RequirementOr([
        RequirementAnd([id_req_a]),
        RequirementAnd([id_req_b]),
    ])

    simple_1 = the_set.patch_requirements({res_a: 0, res_b: 0}, 1, None)
    simple_2 = the_set.patch_requirements({res_a: 0, res_b: 1}, 1, None)
    simple_3 = the_set.patch_requirements({res_a: 1, res_b: 1}, 1, None)

    assert simple_1.as_set(None).alternatives == frozenset()
    assert simple_2.as_set(None).alternatives == frozenset([RequirementList([])])
    assert simple_3.as_set(None).alternatives == frozenset([RequirementList([])])


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


@pytest.mark.parametrize(["a", "b", "expected"], [
    (RequirementSet.impossible(), make_single_set(make_req_a()), make_single_set(make_req_a())),
    (RequirementSet.impossible(), RequirementSet.trivial(), RequirementSet.trivial()),
    (RequirementSet.trivial(), make_single_set(make_req_a()), RequirementSet.trivial()),
    (make_single_set(make_req_a()), make_single_set(make_req_b()),
     RequirementSet([RequirementList([make_req_a()[1]]), RequirementList([make_req_b()[1]])])),
])
def test_expand_alternatives(a: RequirementSet, b: RequirementSet, expected: RequirementSet):
    assert a.expand_alternatives(b) == expected


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
        (ResourceRequirement(SimpleResourceInfo(item[0], str(item[0]), str(item[0]), ""), 1, item[1])
         for item in input_data))
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


def test_requirement_as_set_1():
    req = RequirementAnd([
        _req("A"),
        RequirementOr([_req("B"), _req("C")]),
        RequirementOr([_req("D"), _req("E")]),
    ])
    assert req.as_set(None) == RequirementSet([
        RequirementList([_req("A"), _req("B"), _req("D")]),
        RequirementList([_req("A"), _req("B"), _req("E")]),
        RequirementList([_req("A"), _req("C"), _req("D")]),
        RequirementList([_req("A"), _req("C"), _req("E")]),
    ])


def test_requirement_as_set_2():
    req = RequirementAnd([
        Requirement.trivial(),
        _req("A"),
    ])
    assert req.as_set(None) == RequirementSet([
        RequirementList([_req("A")]),
    ])


def test_requirement_as_set_3():
    req = RequirementOr([
        Requirement.impossible(),
        _req("A"),
    ])
    assert req.as_set(None) == RequirementSet([
        RequirementList([_req("A")]),
    ])


def test_requirement_as_set_4():
    req = RequirementOr([
        Requirement.impossible(),
        _req("A"),
        Requirement.trivial(),
    ])
    assert req.as_set(None) == RequirementSet([
        RequirementList([]),
    ])


def test_requirement_as_set_5():
    req = RequirementAnd([
        _req("A"),
        _req("B"),
        _req("C"),
    ])
    assert req.as_set(None) == RequirementSet([
        RequirementList([_req("A"), _req("B"), _req("C")]),
    ])


def test_requirement_and_str():
    req = RequirementAnd([
        _req("B"),
        _req("A"),
        _req("C"),
    ])
    assert str(req) == "(A ≥ 1 and B ≥ 1 and C ≥ 1)"


def test_requirement_or_str():
    req = RequirementOr([
        _req("C"),
        _req("A"),
        _req("B"),
    ])
    assert str(req) == "(A ≥ 1 or B ≥ 1 or C ≥ 1)"


def test_impossible_requirement_as_set():
    assert Requirement.impossible().as_set(None) == RequirementSet.impossible()


def test_impossible_requirement_satisfied():
    assert not Requirement.impossible().satisfied({}, 99, None)


def test_impossible_requirement_damage():
    assert Requirement.impossible().damage({}, None) == MAX_DAMAGE


def test_impossible_requirement_str():
    assert str(Requirement.impossible()) == "Impossible"


def test_trivial_requirement_as_set():
    assert Requirement.trivial().as_set(None) == RequirementSet.trivial()


def test_trivial_requirement_satisfied():
    assert Requirement.trivial().satisfied({}, 99, None)


def test_trivial_requirement_damage():
    assert Requirement.trivial().damage({}, None) == 0


def test_trivial_requirement_str():
    assert str(Requirement.trivial()) == "Trivial"


@pytest.mark.parametrize(["original", "expected"], [
    (
            RequirementOr([
                RequirementAnd([
                    _req("A"),
                ]),
            ]),
            _req("A"),
    ),
    (
            RequirementAnd([
                RequirementOr([
                    _req("A"),
                ]),
            ]),
            _req("A"),
    ),
    (
            RequirementAnd([
                RequirementOr([
                    _req("B"),
                    Requirement.trivial()
                ]),
                RequirementAnd([
                    Requirement.trivial(),
                    _req("A"),
                ]),
            ]),
            _req("A"),
    ),
    (
            RequirementOr([
                _req("A"),
                RequirementAnd([_req("B"), _req("C")]),
                RequirementAnd([_req("B"), _req("D")]),
            ]),
            RequirementOr([
                _req("A"),
                RequirementAnd([
                    _req("B"),
                    RequirementOr([
                        _req("C"),
                        _req("D"),
                    ]),
                ]),
            ]),
    ),
    (
            RequirementOr([
                RequirementAnd([_req("B"), _req("C")]),
                RequirementAnd([_req("B"), _req("D")]),
            ]),
            RequirementAnd([
                _req("B"),
                RequirementOr([
                    _req("C"),
                    _req("D"),
                ]),
            ]),
    ),
    (
            RequirementOr([
                _req("A"),
                _req("A"),
            ]),
            _req("A"),
    ),
    (
            RequirementAnd([
                _req("A"),
                _req("A"),
            ]),
            _req("A"),
    ),
    (
            RequirementOr([
                RequirementAnd([
                    _req("A"),
                    RequirementOr([
                        _req("A"),
                        RequirementOr([_req("A")])
                    ])
                ]),
                RequirementAnd([
                    _req("A"),
                    RequirementOr([
                        _req("A"),
                        RequirementOr([]),
                    ]),
                ]),
            ]),
            _req("A"),
    ),
    (
            RequirementOr([
                RequirementAnd([
                    _req("A"),
                    RequirementOr([
                        _req("A"),
                        RequirementOr([_req("A")])
                    ])
                ]),
                RequirementAnd([
                    _req("A"),
                    RequirementOr([
                        _req("A"),
                        RequirementOr([_req("A")]),
                    ])
                ])
            ]),
            _req("A"),
    )
])
def test_simplified_requirement(original, expected):
    simplified = original.simplify()
    assert simplified == expected
    assert simplified.as_set(None) == expected.as_set(None)


def test_requirement_template(database):
    # Setup
    database.requirement_template["Use A"] = _make_req("A")[1]
    use_a = RequirementTemplate("Use A")

    # Run
    as_set = use_a.as_set(database)

    # Assert
    assert as_set == make_single_set(_make_req("A"))
    assert hash(use_a)


def test_requirement_template_nested(database):
    # Setup
    use_a = RequirementTemplate("Use A")
    use_b = RequirementTemplate("Use B")

    database.requirement_template["Use A"] = _req("A")
    database.requirement_template["Use B"] = RequirementOr([use_a, _req("B")])

    # Run
    as_set = use_b.as_set(database)

    # Assert
    assert as_set == RequirementSet([
        RequirementList([_req("A")]),
        RequirementList([_req("B")]),
    ])
    assert hash(use_a) != hash(use_b)


def _json_req(amount: int, index: int = 1, resource_type: int = 3):
    return {"type": "resource", "data": {"type": resource_type, "index": index, "amount": amount, "negate": False}}


@pytest.mark.parametrize(["damage", "items", "requirement"], [
    (50, [], {"type": "and", "data": [_json_req(50)]}),
    (MAX_DAMAGE, [], {"type": "and", "data": [_json_req(1, resource_type=0)]}),
    (80, [], {"type": "and", "data": [_json_req(50), _json_req(30)]}),
    (30, [], {"type": "or", "data": [_json_req(50), _json_req(30)]}),
    (50, [], {"type": "or", "data": [_json_req(50), _json_req(1, resource_type=0)]}),
    (0, [1], {"type": "or", "data": [_json_req(50), _json_req(1, resource_type=0)]}),
    (100, [], {"type": "or", "data": [
        _json_req(100),
        {"type": "and", "data": [_json_req(50), _json_req(1, resource_type=0)]},
    ]}),
    (50, [1], {"type": "or", "data": [
        _json_req(100),
        {"type": "and", "data": [_json_req(50), _json_req(1, resource_type=0)]},
    ]}),
    (150, [], {"type": "and", "data": [
        _json_req(100),
        {"type": "or", "data": [_json_req(50), _json_req(1, resource_type=0)]},
    ]}),
    (100, [1], {"type": "and", "data": [
        _json_req(100),
        {"type": "or", "data": [_json_req(50), _json_req(1, resource_type=0)]},
    ]}),
    (200, [], {"type": "and", "data": [_json_req(100), _json_req(100, 2)]}),
    (121, [13], {"type": "and", "data": [_json_req(100), _json_req(100, 2)]}),
    (100, [14], {"type": "and", "data": [_json_req(100), _json_req(100, 2)]}),
])
def test_requirement_damage(damage, items, requirement, echoes_resource_database):
    req = data_reader.read_requirement(requirement, echoes_resource_database)

    resources = {
        echoes_resource_database.get_item(item): 1
        for item in items
    }

    assert req.damage(resources, echoes_resource_database) == damage


def test_simple_echoes_damage(echoes_resource_database):
    db = echoes_resource_database
    req = ResourceRequirement(
        db.get_by_type_and_index(ResourceType.DAMAGE, 2),
        50, False,
    )
    d_suit = db.get_item_by_name("Dark Suit")
    l_suit = db.get_item_by_name("Light Suit")

    assert req.damage({}, db) == 50
    assert req.damage({d_suit: 1}, db) == 11
    assert req.damage({l_suit: 1}, db) == 0


def test_requirement_list_constructor(echoes_resource_database):
    def item(name):
        return search.find_resource_info_with_long_name(echoes_resource_database.item, name)

    req_list = RequirementList([
        ResourceRequirement(item("Dark Visor"), 1, False),
        ResourceRequirement(item("Missile"), 5, False),
        ResourceRequirement(item("Seeker Launcher"), 1, False),
    ])
    extract = [(req.resource.long_name, req.amount) for req in req_list.items]

    assert sorted(extract) == [
        ("Dark Visor", 1),
        ("Missile", 5),
        ("Seeker Launcher", 1),
    ]


def test_requirement_set_constructor(echoes_resource_database):
    def item(name):
        return search.find_resource_info_with_long_name(echoes_resource_database.item, name)

    req_set = RequirementSet([
        RequirementList([
            ResourceRequirement(item("Dark Visor"), 1, False),
            ResourceRequirement(item("Missile"), 5, False),
            ResourceRequirement(item("Seeker Launcher"), 1, False),
        ]),
        RequirementList([
            ResourceRequirement(item("Screw Attack"), 1, False),
            ResourceRequirement(item("Space Jump Boots"), 1, False),
        ]),
        RequirementList([
            ResourceRequirement(item("Power Bomb"), 1, False),
            ResourceRequirement(item("Boost Ball"), 1, False),
        ]),
    ])
    extract = [
        sorted((req.resource.long_name, req.amount) for req in req_list.items)
        for req_list in req_set.alternatives
    ]

    assert sorted(extract) == [
        [
            ("Boost Ball", 1),
            ("Power Bomb", 1),
        ],
        [
            ("Dark Visor", 1),
            ("Missile", 5),
            ("Seeker Launcher", 1),
        ],
        [
            ("Screw Attack", 1),
            ("Space Jump Boots", 1),
        ],
    ]
