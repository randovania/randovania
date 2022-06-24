from unittest.mock import MagicMock

import pytest

from randovania.game_description import data_reader
from randovania.game_description.requirements.base import MAX_DAMAGE, Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.game_description.world.node import NodeContext
from randovania.games.game import RandovaniaGame


@pytest.fixture(name="database")
def _database() -> ResourceDatabase:
    return ResourceDatabase(
        game_enum=RandovaniaGame.METROID_PRIME_ECHOES,
        item=[
            ItemResourceInfo(i, l, l, 1)
            for i, l in enumerate("ABCDEF")
        ],
        event=[],
        trick=[],
        damage=[],
        version=[],
        misc=[
            SimpleResourceInfo(13, "Trivial", "Trivial", ResourceType.MISC),
            SimpleResourceInfo(14, "Impossible", "Impossible", ResourceType.MISC),
        ],
        requirement_template={},
        damage_reductions={},
        energy_tank_item_index="",
        item_percentage_index=None,
        multiworld_magic_item_index=None,
    )


def _empty_col():
    return ResourceCollection()


def _col_for(db: ResourceDatabase, *args: ResourceInfo):
    return ResourceCollection.from_dict(db, {resource: 1 for resource in args})


def make_req_a(db: ResourceDatabase):
    res = db.item[0]
    return res, ResourceRequirement.simple(res)


def make_req_b(db: ResourceDatabase):
    res = db.item[1]
    return res, ResourceRequirement.simple(res)


def make_req_c(db: ResourceDatabase):
    res = db.item[2]
    return res, ResourceRequirement.simple(res)


def make_single_set(id_req: tuple[ResourceInfo, ResourceRequirement]) -> RequirementSet:
    return RequirementSet([RequirementList([id_req[1]])])


def test_empty_requirement_set_satisfied():
    assert not RequirementSet([]).satisfied(_empty_col(), 99, None)


def test_empty_requirement_list_satisfied():
    assert RequirementList([]).satisfied(_empty_col(), 99, None)


def test_simplify_requirement_set_static(blank_game_description):
    db = blank_game_description.resource_database
    res_a, id_req_a = make_req_a(db)
    res_b, id_req_b = make_req_b(db)
    fd = ResourceCollection.from_dict

    the_set = RequirementOr([
        RequirementAnd([id_req_a]),
        RequirementAnd([id_req_b]),
    ])

    simple_1 = the_set.patch_requirements(fd(db, {res_a: 0, res_b: 0}), 1, db)
    simple_2 = the_set.patch_requirements(fd(db, {res_a: 0, res_b: 1}), 1, db)
    simple_3 = the_set.patch_requirements(fd(db, {res_a: 1, res_b: 1}), 1, db)

    assert simple_1.as_set(db).alternatives == frozenset()
    assert simple_2.as_set(db).alternatives == frozenset([RequirementList([])])
    assert simple_3.as_set(db).alternatives == frozenset([RequirementList([])])


def test_prevent_redundant(blank_game_description):
    db = blank_game_description.resource_database
    res_a, id_req_a = make_req_a(db)
    res_b, id_req_b = make_req_b(db)

    the_set = RequirementSet([
        RequirementList([id_req_a]),
        RequirementList([id_req_a, id_req_b]),
    ])

    assert the_set.alternatives == frozenset([RequirementList([id_req_a])])


def test_trivial_merge(blank_game_description):
    db = blank_game_description.resource_database
    res_a, id_req_a = make_req_a(db)
    trivial = RequirementSet.trivial()
    impossible = RequirementSet.impossible()

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


def test_expand_alternatives_1(blank_resource_db):
    db = blank_resource_db
    a = RequirementSet.impossible()
    b = make_single_set(make_req_a(db))
    expected = make_single_set(make_req_a(db))

    assert a.expand_alternatives(b) == expected


def test_expand_alternatives_2():
    a = RequirementSet.impossible()
    b = RequirementSet.trivial()
    expected = RequirementSet.trivial()

    assert a.expand_alternatives(b) == expected


def test_expand_alternatives_3(blank_resource_db):
    db = blank_resource_db
    a = RequirementSet.trivial()
    b = make_single_set(make_req_a(db))
    expected = RequirementSet.trivial()

    assert a.expand_alternatives(b) == expected


def test_expand_alternatives_4(blank_resource_db):
    db = blank_resource_db
    a = make_single_set(make_req_a(db))
    b = make_single_set(make_req_b(db))
    expected = RequirementSet([RequirementList([make_req_a(db)[1]]), RequirementList([make_req_b(db)[1]])])

    assert a.expand_alternatives(b) == expected


@pytest.mark.parametrize(["input_data", "output_data"], [
    ([], []),
    ([(0, False)], []),
    ([(0, True)], [0]),
    ([(0, True), (0, False)], [0]),
    ([(0, True), (1, False)], [0]),
    ([(0, True), (1, True)], [0, 1]),
])
def test_list_dangerous_resources(database, input_data, output_data):
    # setup
    req_list = RequirementList(
        ResourceRequirement.create(database.resource_by_index[item[0]], 1, item[1])
        for item in input_data
    )

    expected_result = {
        database.resource_by_index[item]
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


def test_requirement_as_set_1(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementAnd([
        _req("A"),
        RequirementOr([_req("B"), _req("C")]),
        RequirementOr([_req("D"), _req("E")]),
    ])
    assert req.as_set(database) == RequirementSet([
        RequirementList([_req("A"), _req("B"), _req("D")]),
        RequirementList([_req("A"), _req("B"), _req("E")]),
        RequirementList([_req("A"), _req("C"), _req("D")]),
        RequirementList([_req("A"), _req("C"), _req("E")]),
    ])


def test_requirement_as_set_2(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementAnd([
        Requirement.trivial(),
        _req("A"),
    ])
    assert req.as_set(database) == RequirementSet([
        RequirementList([_req("A")]),
    ])


def test_requirement_as_set_3(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementOr([
        Requirement.impossible(),
        _req("A"),
    ])
    assert req.as_set(database) == RequirementSet([
        RequirementList([_req("A")]),
    ])


def test_requirement_as_set_4(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementOr([
        Requirement.impossible(),
        _req("A"),
        Requirement.trivial(),
    ])
    assert req.as_set(database) == RequirementSet([
        RequirementList([]),
    ])


def test_requirement_as_set_5(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementAnd([
        _req("A"),
        _req("B"),
        _req("C"),
    ])
    assert req.as_set(database) == RequirementSet([
        RequirementList([_req("A"), _req("B"), _req("C")]),
    ])


def test_requirement_and_str(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementAnd([
        _req("B"),
        _req("A"),
        _req("C"),
    ])
    assert str(req) == "(A ≥ 1 and B ≥ 1 and C ≥ 1)"


def test_requirement_or_str(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementOr([
        _req("C"),
        _req("A"),
        _req("B"),
    ])
    assert str(req) == "(A ≥ 1 or B ≥ 1 or C ≥ 1)"


def test_impossible_requirement_as_set():
    assert Requirement.impossible().as_set(None) == RequirementSet.impossible()


def test_impossible_requirement_satisfied():
    assert not Requirement.impossible().satisfied(_empty_col(), 99, None)


def test_impossible_requirement_damage():
    assert Requirement.impossible().damage(_empty_col(), None) == MAX_DAMAGE


def test_impossible_requirement_str():
    assert str(Requirement.impossible()) == "Impossible"


def test_trivial_requirement_as_set():
    assert Requirement.trivial().as_set(None) == RequirementSet.trivial()


def test_trivial_requirement_satisfied():
    assert Requirement.trivial().satisfied(_empty_col(), 99, None)


def test_trivial_requirement_damage():
    assert Requirement.trivial().damage(_empty_col(), None) == 0


def test_trivial_requirement_str():
    assert str(Requirement.trivial()) == "Trivial"


def test_simplified_requirement(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    test_parameters = [
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
    ]

    for original, expected in test_parameters:
        simplified = original.simplify()
        assert simplified == expected
        assert simplified.as_set(database) == expected.as_set(database)


def test_requirement_template(database):
    def _make_req(name: str):
        req = database.get_item(name)
        id_req = ResourceRequirement.simple(req)
        return req, id_req

    # Setup
    database.requirement_template["Use A"] = _make_req("A")[1]
    use_a = RequirementTemplate("Use A")

    # Run
    as_set = use_a.as_set(database)

    # Assert
    assert as_set == make_single_set(_make_req("A"))
    assert hash(use_a)


def test_requirement_template_nested(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

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


def _json_req(amount: int, name: str = "Damage", resource_type: ResourceType = ResourceType.DAMAGE):
    return {"type": "resource",
            "data": {
                "type": resource_type.as_string,
                "name": name,
                "amount": amount,
                "negate": False,
            }}


def _arr_req(req_type: str, items: list):
    return {"type": req_type, "data": {"comment": None, "items": items}}


@pytest.mark.parametrize(["damage", "items", "requirement"], [
    (50, [], _arr_req("and", [_json_req(50)])),
    (MAX_DAMAGE, [], _arr_req("and", [_json_req(1, "Dark", ResourceType.ITEM)])),
    (80, [], _arr_req("and", [_json_req(50), _json_req(30)])),
    (30, [], _arr_req("or", [_json_req(50), _json_req(30)])),
    (50, [], _arr_req("or", [_json_req(50), _json_req(1, "Dark", ResourceType.ITEM)])),
    (0, ["Dark"], _arr_req("or", [_json_req(50), _json_req(1, "Dark", ResourceType.ITEM)])),
    (100, [], _arr_req("or", [
        _json_req(100),
        _arr_req("and", [_json_req(50), _json_req(1, "Dark", ResourceType.ITEM)]),
    ])),
    (50, ["Dark"], _arr_req("or", [
        _json_req(100),
        _arr_req("and", [_json_req(50), _json_req(1, "Dark", ResourceType.ITEM)]),
    ])),
    (150, [], _arr_req("and", [
        _json_req(100),
        _arr_req("or", [_json_req(50), _json_req(1, "Dark", ResourceType.ITEM)]),
    ])),
    (100, ["Dark"], _arr_req("and", [
        _json_req(100),
        _arr_req("or", [_json_req(50), _json_req(1, "Dark", ResourceType.ITEM)]),
    ])),
    (200, [], _arr_req("and", [_json_req(100), _json_req(100, "DarkWorld1")])),
    (121, ["DarkSuit"], _arr_req("and", [_json_req(100), _json_req(100, "DarkWorld1")])),
    (100, ["LightSuit"], _arr_req("and", [_json_req(100), _json_req(100, "DarkWorld1")])),
])
def test_requirement_damage(damage, items, requirement, echoes_resource_database):
    req = data_reader.read_requirement(requirement, echoes_resource_database)

    collection = ResourceCollection.from_dict(echoes_resource_database, {
        echoes_resource_database.get_item(item): 1
        for item in items
    })

    assert req.damage(collection, echoes_resource_database) == damage


def test_simple_echoes_damage(echoes_resource_database):
    db = echoes_resource_database
    req = ResourceRequirement.create(
        db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1"),
        50, False,
    )
    d_suit = db.get_item_by_name("Dark Suit")
    l_suit = db.get_item_by_name("Light Suit")

    assert req.damage(_empty_col(), db) == 50
    assert req.damage(_col_for(db, d_suit), db) == 11
    assert req.damage(_col_for(db, l_suit), db) == 0


def test_requirement_list_constructor(echoes_resource_database):
    def item(name):
        return search.find_resource_info_with_long_name(echoes_resource_database.item, name)

    req_list = RequirementList([
        ResourceRequirement.simple(item("Dark Visor")),
        ResourceRequirement.create(item("Missile"), 5, False),
        ResourceRequirement.simple(item("Seeker Launcher")),
    ])
    extract = [(req.resource.long_name, req.amount) for req in req_list.values()]

    assert sorted(extract) == [
        ("Dark Visor", 1),
        ("Missile", 5),
        ("Seeker Launcher", 1),
    ]


def test_requirement_set_constructor(echoes_resource_database):
    item = echoes_resource_database.get_item_by_name

    req_set = RequirementSet([
        RequirementList([
            ResourceRequirement.simple(item("Dark Visor")),
            ResourceRequirement.create(item("Missile"), 5, False),
            ResourceRequirement.simple(item("Seeker Launcher")),
        ]),
        RequirementList([
            ResourceRequirement.simple(item("Screw Attack")),
            ResourceRequirement.simple(item("Space Jump Boots")),
        ]),
        RequirementList([
            ResourceRequirement.simple(item("Power Bomb")),
            ResourceRequirement.simple(item("Boost Ball")),
        ]),
    ])
    extract = [
        sorted((req.resource.long_name, req.amount) for req in req_list.values())
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


def test_node_resource_info_as_requirement(blank_game_description):
    db = blank_game_description.resource_database
    node = blank_game_description.world_list.all_nodes[0]
    context = NodeContext(None, None, db, blank_game_description.world_list)

    nri = NodeResourceInfo.from_node
    req = ResourceRequirement.simple(nri(node, context))

    assert not req.satisfied(_empty_col(), 0, db)
    assert req.satisfied(_col_for(db, nri(node, context)), 0, db)


def test_set_as_str_impossible():
    assert RequirementSet.impossible().as_str == "Impossible"


def test_set_as_str_trivial():
    assert RequirementSet.trivial().as_str == "Trivial"


def test_set_as_str_things(echoes_resource_database):
    item = echoes_resource_database.get_item_by_name

    req_set = RequirementSet([
        RequirementList([
            ResourceRequirement.simple(item("Screw Attack")),
            ResourceRequirement.simple(item("Space Jump Boots")),
        ]),
        RequirementList([
            ResourceRequirement.simple(item("Power Bomb")),
        ]),
    ])

    assert req_set.as_str == "(Power Bomb ≥ 1) or (Screw Attack ≥ 1, Space Jump Boots ≥ 1)"


def test_set_hash(echoes_resource_database):
    req_set_a = RequirementSet([
        RequirementList([
            ResourceRequirement.simple(echoes_resource_database.get_item_by_name("Power Bomb")),
        ]),
    ])
    req_set_b = RequirementSet([
        RequirementList([
            ResourceRequirement.simple(echoes_resource_database.get_item_by_name("Power Bomb")),
        ]),
    ])

    assert req_set_a == req_set_b
    assert req_set_a is not req_set_b

    hash_a = hash(req_set_a)
    hash_b = hash(req_set_b)
    assert hash_a == hash_b

    assert hash_a == req_set_a._cached_hash


def test_sort_resource_requirement(blank_game_description):
    db = blank_game_description.resource_database
    node = blank_game_description.world_list.all_nodes[0]
    assert node is not None

    resources = [
        NodeResourceInfo.from_node(node, NodeContext(None, None, db, blank_game_description.world_list)),
        SimpleResourceInfo(1, "Resource", "Resource", ResourceType.MISC),
        TrickResourceInfo(2, "Trick", "Trick", "Long Description"),
        ItemResourceInfo(3, "Item", "Item", 1),
    ]

    # Assert resources has an entry for every type of ResourceInfo
    assert {type(it) for it in resources} == set(ResourceInfo.__args__)
    assert len(resources) == len(ResourceInfo.__args__)

    requirements = [
        ResourceRequirement.simple(it)
        for it in resources
    ]

    result = sorted(requirements)
    assert result == list(reversed(requirements))
