import pytest

from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.dread.layout.dread_damage_state import DreadDamageState


@pytest.mark.parametrize(
    ("immediate_parts", "damage", "item", "count", "energy"),
    [
        (True, 0, "ETank", 1, 199),
        (True, 50, "ETank", 1, 199),
        (True, 0, "EFragment", 1, 124),
        (True, 50, "EFragment", 1, 74),
        (False, 0, "EFragment", 1, 99),
        (False, 0, "EFragment", 4, 199),
        (False, 0, "EFragment", 5, 199),
        (False, 50, "EFragment", 1, 49),
        (False, 50, "EFragment", 4, 199),
        (False, 50, "EFragment", 5, 199),
    ],
)
def test_apply_collected_resource_difference(dread_game_description, immediate_parts, damage, item, count, energy):
    energy_tank_item = dread_game_description.get_resource_database_view().get_item("ETank")
    energy_part_item = dread_game_description.get_resource_database_view().get_item("EFragment")
    state: DreadDamageState = DreadDamageState(
        starting_energy=99,
        energy_per_tank=100,
        energy_tank=energy_tank_item,
        use_immediate_energy_parts=immediate_parts,
        energy_part_item=energy_part_item,
    )

    state_after_damage = state.apply_damage(damage)

    old_resources: ResourceCollection = ResourceCollection.with_database(dread_game_description.resource_database)
    new_resources = old_resources.duplicate()
    new_resources.add_resource_gain([(dread_game_description.get_resource_database_view().get_item(item), count)])

    new_state = state_after_damage.apply_collected_resource_difference(new_resources, old_resources)

    assert new_state.health_for_damage_requirements() == energy
