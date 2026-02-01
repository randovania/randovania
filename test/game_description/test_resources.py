from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_type import ResourceType
from randovania.graph.graph_requirement import create_requirement_list
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase


def test_pickup_index_equality():
    assert PickupIndex(1) == PickupIndex(1)


def test_pickup_index_has():
    d = {PickupIndex(1): True}
    assert PickupIndex(1) in d


def test_resource_type_from_index():
    # Run
    result = ResourceType.from_index(0)

    # Assert
    assert result == ResourceType.ITEM


def test_resources_for_unsatisfied_damage_as_interesting(echoes_resource_database: ResourceDatabase):
    db = echoes_resource_database
    req = ResourceRequirement.create(
        db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1"),
        100,
        False,
    )

    damage_state = EnergyTankDamageState(
        99,
        100,
        db.energy_tank,
        [],
    )

    interesting_resources = calculate_interesting_resources(
        frozenset([create_requirement_list(db, [req])]), db.create_resource_collection(), db, damage_state
    )
    d_suit = db.get_item_by_display_name("Dark Suit")
    l_suit = db.get_item_by_display_name("Light Suit")
    e_tank = db.get_item_by_display_name("Energy Tank")

    assert d_suit in interesting_resources
    assert l_suit in interesting_resources
    assert e_tank in interesting_resources


def test_resources_for_satisfied_damage_as_interesting(echoes_resource_database):
    db = echoes_resource_database
    req = ResourceRequirement.create(
        db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1"),
        5,
        False,
    )

    damage_state = EnergyTankDamageState(
        99,
        100,
        db.energy_tank,
        [],
    )
    interesting_resources = calculate_interesting_resources(
        frozenset([create_requirement_list(db, [req])]), db.create_resource_collection(), db, damage_state
    )
    d_suit = db.get_item_by_display_name("Dark Suit")
    l_suit = db.get_item_by_display_name("Light Suit")
    e_tank = db.get_item_by_display_name("Energy Tank")

    assert d_suit in interesting_resources
    assert l_suit in interesting_resources
    assert e_tank in interesting_resources
