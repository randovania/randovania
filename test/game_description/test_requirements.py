from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.requirements import fast_as_set
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_database import NamedRequirementTemplate, ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_info import ResourceInfo


@pytest.fixture
def database() -> ResourceDatabase:
    return ResourceDatabase(
        game_enum=RandovaniaGame.METROID_PRIME_ECHOES,
        item=[ItemResourceInfo(i, letter, letter, 1) for i, letter in enumerate("ABCDEF")],
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
        energy_tank_item=ItemResourceInfo(4, "E", "E", 1),
    )


def _col_for(db: ResourceDatabase, *args: ResourceInfo) -> ResourceCollection:
    collection = ResourceCollection.with_resource_count(db, len(db.resource_by_index))
    collection.add_resource_gain((it, 1) for it in args)
    return collection


def make_req_a(db: ResourceDatabase):
    res = db.item[0]
    return res, ResourceRequirement.simple(res)


def make_req_b(db: ResourceDatabase):
    res = db.item[1]
    return res, ResourceRequirement.simple(res)


def make_req_c(db: ResourceDatabase):
    res = db.item[2]
    return res, ResourceRequirement.simple(res)


def test_requirement_as_set_0(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    expected = [
        RequirementList([_req("A"), _req("B")]),
        RequirementList([_req("A"), _req("C")]),
    ]
    req = RequirementAnd(
        [
            _req("A"),
            RequirementOr([_req("B"), _req("C")]),
        ]
    )
    assert list(fast_as_set.fast_as_alternatives(req, database)) == expected


def test_requirement_as_set_1(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    expected = [
        RequirementList([_req("A"), _req("B"), _req("D")]),
        RequirementList([_req("A"), _req("B"), _req("E")]),
        RequirementList([_req("A"), _req("C"), _req("D")]),
        RequirementList([_req("A"), _req("C"), _req("E")]),
    ]

    req = RequirementAnd(
        [
            _req("A"),
            RequirementOr([_req("B"), _req("C")]),
            RequirementOr([_req("D"), _req("E")]),
        ]
    )
    assert list(fast_as_set.fast_as_alternatives(req, database)) == expected


def test_requirement_as_set_2(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    expected = [
        RequirementList([_req("A")]),
    ]

    req = RequirementAnd(
        [
            Requirement.trivial(),
            _req("A"),
        ]
    )
    assert list(fast_as_set.fast_as_alternatives(req, database)) == expected


def test_requirement_as_set_3(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    expected = [
        RequirementList([_req("A")]),
    ]

    req = RequirementOr(
        [
            Requirement.impossible(),
            _req("A"),
        ]
    )
    assert list(fast_as_set.fast_as_alternatives(req, database)) == expected


def test_requirement_as_set_4(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementOr(
        [
            Requirement.impossible(),
            _req("A"),
            Requirement.trivial(),
        ]
    )
    assert set(fast_as_set.fast_as_alternatives(req, database)) == {
        RequirementList([]),
        RequirementList([_req("A")]),
    }


def test_requirement_as_set_5(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    expected = [
        RequirementList([_req("A"), _req("B"), _req("C")]),
    ]

    req = RequirementAnd(
        [
            _req("A"),
            _req("B"),
            _req("C"),
        ]
    )
    assert list(fast_as_set.fast_as_alternatives(req, database)) == expected


def test_requirement_as_set_6(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    expected = [
        RequirementList([_req("A"), _req("B"), _req("C")]),
        RequirementList([_req("A"), _req("B"), _req("D"), _req("E")]),
    ]

    req = RequirementAnd(
        [
            _req("A"),
            RequirementAnd(
                [
                    _req("B"),
                    RequirementOr(
                        [
                            _req("C"),
                            RequirementAnd([_req("D"), _req("E")]),
                        ],
                    ),
                ],
            ),
        ]
    )
    assert list(fast_as_set.fast_as_alternatives(req, database)) == expected


def test_requirement_and_str(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementAnd(
        [
            _req("B"),
            _req("A"),
            _req("C"),
        ]
    )
    assert str(req) == "(A ≥ 1 and B ≥ 1 and C ≥ 1)"


def test_requirement_or_str(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    req = RequirementOr(
        [
            _req("C"),
            _req("A"),
            _req("B"),
        ]
    )
    assert str(req) == "(A ≥ 1 or B ≥ 1 or C ≥ 1)"


def test_impossible_requirement_str():
    assert str(Requirement.impossible()) == "Impossible"


def test_trivial_requirement_str():
    assert str(Requirement.trivial()) == "Trivial"


def test_simplified_requirement(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    test_parameters: list[tuple[Requirement, Requirement]] = [
        (
            RequirementOr(
                [
                    RequirementAnd(
                        [
                            _req("A"),
                        ]
                    ),
                ]
            ),
            _req("A"),
        ),
        (
            RequirementAnd(
                [
                    RequirementOr(
                        [
                            _req("A"),
                        ]
                    ),
                ]
            ),
            _req("A"),
        ),
        (
            RequirementAnd(
                [
                    RequirementOr([_req("B"), Requirement.trivial()]),
                    RequirementAnd(
                        [
                            Requirement.trivial(),
                            _req("A"),
                        ]
                    ),
                ]
            ),
            _req("A"),
        ),
        (
            RequirementOr(
                [
                    _req("A"),
                    RequirementAnd([_req("B"), _req("C")]),
                    RequirementAnd([_req("B"), _req("D")]),
                ]
            ),
            RequirementOr(
                [
                    _req("A"),
                    RequirementAnd(
                        [
                            _req("B"),
                            RequirementOr(
                                [
                                    _req("C"),
                                    _req("D"),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ),
        (
            RequirementOr(
                [
                    RequirementAnd([_req("B"), _req("C")]),
                    RequirementAnd([_req("B"), _req("D")]),
                ]
            ),
            RequirementAnd(
                [
                    _req("B"),
                    RequirementOr(
                        [
                            _req("C"),
                            _req("D"),
                        ]
                    ),
                ]
            ),
        ),
        (
            RequirementOr(
                [
                    _req("A"),
                    _req("A"),
                ]
            ),
            _req("A"),
        ),
        (
            RequirementAnd(
                [
                    _req("A"),
                    _req("A"),
                ]
            ),
            _req("A"),
        ),
        (
            RequirementOr(
                [
                    RequirementAnd([_req("A"), RequirementOr([_req("A"), RequirementOr([_req("A")])])]),
                    RequirementAnd(
                        [
                            _req("A"),
                            RequirementOr(
                                [
                                    _req("A"),
                                    RequirementOr([]),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            _req("A"),
        ),
        (
            RequirementOr(
                [
                    RequirementAnd([_req("A"), RequirementOr([_req("A"), RequirementOr([_req("A")])])]),
                    RequirementAnd(
                        [
                            _req("A"),
                            RequirementOr(
                                [
                                    _req("A"),
                                    RequirementOr([_req("A")]),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            _req("A"),
        ),
    ]

    for original, expected in test_parameters:
        simplified = original.simplify()
        assert simplified == expected


def test_requirement_template(database):
    def _make_req(name: str):
        req = database.get_item(name)
        id_req = ResourceRequirement.simple(req)
        return req, id_req

    # Setup
    database.requirement_template["Use A"] = NamedRequirementTemplate("Use A", _make_req("A")[1])
    use_a = RequirementTemplate("Use A")
    expected = [RequirementList([_make_req("A")[1]])]

    # Run
    result = list(fast_as_set.fast_as_alternatives(use_a, database))

    # Assert
    assert result == expected
    assert hash(use_a)


def test_requirement_template_nested(database):
    def _req(name: str):
        id_req = ResourceRequirement.simple(database.get_item(name))
        return id_req

    # Setup
    use_a = RequirementTemplate("Use A")
    use_b = RequirementTemplate("Use B")

    database.requirement_template["Use A"] = NamedRequirementTemplate("Use A", _req("A"))
    database.requirement_template["Use B"] = NamedRequirementTemplate("Use B", RequirementOr([use_a, _req("B")]))

    # Run
    result = list(fast_as_set.fast_as_alternatives(use_b, database))

    # Assert
    assert result == [
        RequirementList([_req("A")]),
        RequirementList([_req("B")]),
    ]
    assert hash(use_a) != hash(use_b)


def test_simple_echoes_damage(echoes_resource_database: ResourceDatabase):
    db = echoes_resource_database
    req = ResourceRequirement.create(
        db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1"),
        50,
        False,
    )
    d_suit = db.get_item_by_display_name("Dark Suit")
    l_suit = db.get_item_by_display_name("Light Suit")

    assert req.damage(_col_for(db)) == 50
    assert req.damage(_col_for(db, d_suit)) == 11
    assert req.damage(_col_for(db, l_suit)) == 0


def test_requirement_list_constructor(echoes_resource_database):
    def item(name):
        return search.find_resource_info_with_long_name(echoes_resource_database.item, name)

    req_list = RequirementList(
        [
            ResourceRequirement.simple(item("Dark Visor")),
            ResourceRequirement.create(item("Missile"), 5, False),
            ResourceRequirement.simple(item("Seeker Launcher")),
        ]
    )
    extract = [(req.resource.long_name, req.amount) for req in req_list.values()]

    assert sorted(extract) == [
        ("Dark Visor", 1),
        ("Missile", 5),
        ("Seeker Launcher", 1),
    ]


def test_sort_resource_requirement(blank_game_description):
    node = blank_game_description.region_list.all_nodes[0]
    assert node is not None

    resources = [
        SimpleResourceInfo(1, "Resource", "Resource", ResourceType.MISC),
        TrickResourceInfo(2, "Trick", "Trick", "Long Description"),
        ItemResourceInfo(3, "Item", "Item", 1),
    ]

    requirements = [ResourceRequirement.simple(it) for it in resources]

    result = sorted(requirements)
    assert result == list(reversed(requirements))


def test_damage_satisfied(echoes_resource_database: ResourceDatabase):
    req = ResourceRequirement.create(
        echoes_resource_database.get_damage("Damage"),
        50,
        False,
    )
    col = echoes_resource_database.create_resource_collection()
    assert req.satisfied(col, 99)
    assert req.satisfied(col, 51)
    assert not req.satisfied(col, 50)
