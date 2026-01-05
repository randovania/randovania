import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.game_database_view import ResourceDatabaseView
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.graph.graph_requirement import GraphRequirementSet, create_requirement_list, create_requirement_set
from randovania.graph.requirement_converter import GraphRequirementConverter
from randovania.graph.world_graph import WorldGraph


@pytest.fixture
def converter(blank_world_graph: WorldGraph) -> GraphRequirementConverter:
    resource_db = blank_world_graph.resource_database
    return GraphRequirementConverter(resource_db, blank_world_graph, resource_db.create_resource_collection(), 1.0)


fake_graph: WorldGraph = None  # type: ignore[assignment]


class ResourceFactory:
    def __init__(self, database: ResourceDatabaseView):
        self.database = database

    def res(self, name: str) -> SimpleResourceInfo:
        assert len(name) == 1
        resource = SimpleResourceInfo(
            resource_index=ord(name[0]),
            long_name=name,
            short_name=name,
            resource_type=ResourceType.EVENT,
        )
        self.database.get_resource_mapping()[resource.resource_index] = resource
        return resource

    def req(self, name: str) -> ResourceRequirement:
        return ResourceRequirement.simple(self.res(name))


@pytest.fixture
def fac(converter: GraphRequirementConverter) -> ResourceFactory:
    return ResourceFactory(converter.resource_database)


def test_convert(converter: GraphRequirementConverter, fac: ResourceFactory) -> None:
    res_a = fac.req("A")
    res_b = fac.req("B")

    def col(*args):
        c = converter.resource_database.create_resource_collection()
        for n in args:
            c.set_resource(fac.res(n), 1)
        return c

    assert converter.convert_db(Requirement.trivial()).satisfied(col(), 0)

    result_1_a = converter.convert_db(res_a)
    assert str(result_1_a) == "After A"
    assert not result_1_a.satisfied(col(), 0)
    assert result_1_a.satisfied(col("A"), 0)

    result_1_b = converter.convert_db(RequirementAnd([res_a]))
    assert str(result_1_b) == "After A"

    result_1_c = converter.convert_db(RequirementAnd([res_a, res_a]))
    assert str(result_1_c) == "After A"

    result_1_d = converter.convert_db(RequirementOr([res_a]))
    assert str(result_1_d) == "After A"

    assert result_1_a == result_1_b == result_1_c == result_1_d

    result_2_a = converter.convert_db(RequirementAnd([res_a, res_b]))
    assert str(result_2_a) == "After A and After B"
    assert not result_2_a.satisfied(col(), 0)
    assert not result_2_a.satisfied(col("A"), 0)
    assert result_2_a.satisfied(col("A", "B"), 0)

    result_2_b = converter.convert_db(
        RequirementAnd(
            [
                RequirementAnd([res_a, res_b]),
                RequirementAnd([res_a, res_b]),
            ]
        )
    )
    assert str(result_2_b) == "After A and After B"

    result_3 = converter.convert_db(RequirementOr([res_a, res_b]))
    assert str(result_3) == "(After A) or (After B)"
    assert not result_3.satisfied(col(), 0)
    assert result_3.satisfied(col("A"), 0)
    assert result_3.satisfied(col("B"), 0)

    result_4 = converter.convert_db(
        RequirementOr(
            [
                RequirementAnd([res_a, res_b]),
                RequirementAnd([res_a, res_b]),
            ]
        )
    )
    assert str(result_4) == "After A and After B"


def test_convert_2(converter: GraphRequirementConverter, fac: ResourceFactory) -> None:
    res_a = fac.req("A")
    res_b = fac.req("B")
    res_c = fac.req("C")
    res_d = fac.req("D")
    result = converter.convert_db(
        RequirementAnd(
            [
                RequirementOr([res_a, res_b]),
                RequirementOr([res_c, res_d]),
            ]
        )
    )
    assert str(result) == (
        "(After A and After C) or (After A and After D) or (After B and After C) or (After B and After D)"
    )

    result2 = converter.convert_db(
        RequirementAnd(
            [
                res_a,
                Requirement.impossible(),
            ]
        )
    )
    assert str(result2) == "Impossible"


def test_requirement_as_set_0(converter: GraphRequirementConverter, fac: ResourceFactory):
    expected = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("B")]),
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("C")]),
        ]
    )
    req = RequirementAnd(
        [
            fac.req("A"),
            RequirementOr([fac.req("B"), fac.req("C")]),
        ]
    )

    result = converter.convert_db(req)
    assert str(result) == str(expected)
    assert result == expected


def test_requirement_as_set_1(converter: GraphRequirementConverter, fac: ResourceFactory):
    expected = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("B"), fac.req("D")]),
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("B"), fac.req("E")]),
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("C"), fac.req("D")]),
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("C"), fac.req("E")]),
        ]
    )
    req = RequirementAnd(
        [
            fac.req("A"),
            RequirementOr([fac.req("B"), fac.req("C")]),
            RequirementOr([fac.req("D"), fac.req("E")]),
        ]
    )
    result = converter.convert_db(req)
    assert str(result) == str(expected)
    assert result == expected


def test_requirement_as_set_2(converter: GraphRequirementConverter, fac: ResourceFactory):
    expected = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, [fac.req("A")]),
        ]
    )
    req = RequirementAnd(
        [
            Requirement.trivial(),
            fac.req("A"),
        ]
    )
    result = converter.convert_db(req)
    assert str(result) == str(expected)
    assert result == expected


def test_requirement_as_set_3(converter: GraphRequirementConverter, fac: ResourceFactory):
    expected = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, [fac.req("A")]),
        ]
    )
    req = RequirementOr(
        [
            Requirement.impossible(),
            fac.req("A"),
        ]
    )
    result = converter.convert_db(req)
    assert str(result) == str(expected)
    assert result == expected


def test_requirement_as_set_4(converter: GraphRequirementConverter, fac: ResourceFactory):
    expected_bad = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, [fac.req("A")]),
            create_requirement_list(converter.resource_database, []),
        ]
    )
    expected_opt = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, []),
        ]
    )
    req = RequirementOr(
        [
            Requirement.impossible(),
            fac.req("A"),
            Requirement.trivial(),
        ]
    )
    result = converter._internal_convert(req)
    assert str(result) == str(expected_bad)
    assert result == expected_bad

    assert isinstance(result, GraphRequirementSet)
    result.optimize_alternatives()
    assert str(result) == str(expected_opt)
    assert result == expected_opt


def test_requirement_as_set_5(converter: GraphRequirementConverter, fac: ResourceFactory):
    expected = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("B"), fac.req("C")]),
        ]
    )
    req = RequirementAnd(
        [
            fac.req("A"),
            fac.req("B"),
            fac.req("C"),
        ]
    )
    result = converter.convert_db(req)
    assert str(result) == str(expected)
    assert result == expected


def test_requirement_as_set_6(converter: GraphRequirementConverter, fac: ResourceFactory):
    expected = create_requirement_set(
        [
            create_requirement_list(converter.resource_database, [fac.req("A"), fac.req("B"), fac.req("C")]),
            create_requirement_list(
                converter.resource_database, [fac.req("A"), fac.req("B"), fac.req("D"), fac.req("E")]
            ),
        ]
    )
    req = RequirementAnd(
        [
            fac.req("A"),
            RequirementAnd(
                [
                    fac.req("B"),
                    RequirementOr(
                        [
                            fac.req("C"),
                            RequirementAnd([fac.req("D"), fac.req("E")]),
                        ],
                    ),
                ],
            ),
        ]
    )
    result = converter.convert_db(req)
    assert str(result) == str(expected)
    assert result == expected

    result2 = converter.convert_db(req)
    assert result2 == expected
    assert result2 is not expected


def test_convert_remove_static(fac: ResourceFactory) -> None:
    blank_resource_db = fac.database
    res_a = fac.req("A")
    res_b = fac.req("B")
    res_c = ResourceRequirement.create(blank_resource_db.get_item("Ammo"), 3, False)
    req = RequirementAnd([res_a, res_b, res_c])

    static1 = blank_resource_db.create_resource_collection()
    static1.set_resource(fac.res("B"), 1)
    static1.set_resource(blank_resource_db.get_item("Ammo"), 2)
    converter1 = GraphRequirementConverter(blank_resource_db, fake_graph, static1, 1.0)

    result1 = converter1.convert_db(req)
    assert str(result1) == "After A and Missile ≥ 3"

    static2 = blank_resource_db.create_resource_collection()
    static2.set_resource(fac.res("A"), 0)
    static2.set_resource(fac.res("B"), 1)
    converter2 = GraphRequirementConverter(blank_resource_db, fake_graph, static2, 1.0)

    result2 = converter2.convert_db(req)
    assert str(result2) == "Impossible"


def test_convert_remove_static_with_damage(echoes_resource_database: ResourceDatabase) -> None:
    db = echoes_resource_database
    requirement = RequirementOr(
        [
            ResourceRequirement.create(db.get_damage("DarkWorld1"), 20, False),
            RequirementAnd(
                [
                    ResourceRequirement.simple(db.get_item("MorphBall")),
                    ResourceRequirement.create(db.get_damage("DarkWorld1"), 15, False),
                ]
            ),
        ]
    )

    static = db.create_resource_collection()
    static.set_resource(db.get_item("MorphBall"), 1)
    converter = GraphRequirementConverter(echoes_resource_database, fake_graph, static, 1.0)

    result = converter._internal_convert(requirement)
    assert isinstance(result, GraphRequirementSet)

    assert str(result) == "(Dark World Damage ≥ 20) or (Dark World Damage ≥ 15)"
    result.optimize_alternatives()
    assert str(result) == "Dark World Damage ≥ 15"


def test_convert_node_reference(converter: GraphRequirementConverter) -> None:
    ni = NodeIdentifier.create("Intro", "Starting Area", "Spawn Point")
    req = NodeRequirement(ni)

    result = converter.convert_db(req)
    assert str(result) == "Intro/Starting Area/Spawn Point"


def test_convert_template(converter: GraphRequirementConverter) -> None:
    req = RequirementAnd(
        [
            RequirementTemplate("Can Jump"),
            RequirementTemplate("Can Jump"),
        ]
    )

    result = converter.convert_db(req)
    assert str(result) == "(Jump) or (Double Jump)"


def test_isolate(prime1_resource_database: ResourceDatabase) -> None:
    req = RequirementAnd(
        [
            RequirementOr(
                [
                    RequirementAnd(
                        [
                            ResourceRequirement.create(prime1_resource_database.get_damage("Damage"), 22, False),
                            ResourceRequirement.simple(prime1_resource_database.get_item("X-Ray")),
                        ]
                    ),
                    ResourceRequirement.create(prime1_resource_database.get_damage("Damage"), 135, False),
                ]
            ),
            ResourceRequirement.simple(prime1_resource_database.get_item("Charge")),
            ResourceRequirement.simple(prime1_resource_database.get_item("SpaceJump")),
            ResourceRequirement.create(prime1_resource_database.get_item("Plasma"), 1, True),
        ]
    )

    converter = GraphRequirementConverter(
        prime1_resource_database, fake_graph, prime1_resource_database.create_resource_collection(), 1.0
    )

    result = converter._internal_convert(req)
    assert str(result) == (
        "(Charge Beam and Space Jump Boots and X-Ray Visor and No Plasma Beam and Normal Damage ≥ 22) or "
        "(Charge Beam and Space Jump Boots and No Plasma Beam and Normal Damage ≥ 135)"
    )

    collection = prime1_resource_database.create_resource_collection()

    isolated1 = result.isolate_damage_requirements(collection)
    assert str(isolated1) == "Impossible"

    collection.set_resource(prime1_resource_database.get_item("Charge"), 1)
    collection.set_resource(prime1_resource_database.get_item("SpaceJump"), 1)
    isolated2 = result.isolate_damage_requirements(collection)
    assert str(isolated2) == "Normal Damage ≥ 135"

    collection.set_resource(prime1_resource_database.get_item("Plasma"), 1)
    isolated3 = result.isolate_damage_requirements(collection)
    assert str(isolated3) == "Impossible"
