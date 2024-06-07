from __future__ import annotations

import dataclasses
from random import Random
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.generator import generator, reach_lib
from randovania.generator.filler import pickup_list
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.resolver.state import State, StateGameData

if TYPE_CHECKING:
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_info import ResourceInfo


def test_requirement_lists_without_satisfied_resources(
    echoes_game_description, default_echoes_preset, echoes_game_patches
):
    # Setup
    def item(name):
        return search.find_resource_info_with_long_name(echoes_game_description.resource_database.item, name)

    state = echoes_game_description.game.generator.bootstrap.calculate_starting_state(
        echoes_game_description, echoes_game_patches, default_echoes_preset.configuration
    )
    state.resources.add_resource_gain(
        [
            (item("Seeker Launcher"), 1),
            (item("Space Jump Boots"), 1),
        ]
    )
    uncollected_resources: set[ResourceInfo] = set()
    possible_sets = [
        RequirementSet(
            [
                RequirementList(
                    [
                        ResourceRequirement.simple(item("Dark Visor")),
                        ResourceRequirement.create(item("Missile"), 5, False),
                        ResourceRequirement.simple(item("Seeker Launcher")),
                    ]
                ),
                RequirementList(
                    [
                        ResourceRequirement.simple(item("Screw Attack")),
                        ResourceRequirement.simple(item("Space Jump Boots")),
                    ]
                ),
                RequirementList(
                    [
                        ResourceRequirement.simple(item("Power Bomb")),
                        ResourceRequirement.simple(item("Boost Ball")),
                    ]
                ),
            ]
        ),
        RequirementSet(
            [
                RequirementList(
                    [
                        ResourceRequirement.simple(item("Power Bomb")),
                        ResourceRequirement.simple(item("Boost Ball")),
                    ]
                ),
                RequirementList(
                    [
                        ResourceRequirement.simple(item("Spider Ball")),
                        ResourceRequirement.simple(item("Boost Ball")),
                    ]
                ),
            ]
        ),
    ]

    # Run
    result = pickup_list._requirement_lists_without_satisfied_resources(state, possible_sets, uncollected_resources)

    # Assert
    assert result == {
        RequirementList(
            [
                ResourceRequirement.simple(item("Dark Visor")),
                ResourceRequirement.create(item("Missile"), 5, False),
            ]
        ),
        RequirementList(
            [
                ResourceRequirement.simple(item("Screw Attack")),
            ]
        ),
        RequirementList(
            [
                ResourceRequirement.simple(item("Power Bomb")),
                ResourceRequirement.simple(item("Boost Ball")),
            ]
        ),
        RequirementList(
            [
                ResourceRequirement.simple(item("Spider Ball")),
                ResourceRequirement.simple(item("Boost Ball")),
            ]
        ),
    }


def test_get_pickups_that_solves_unreachable(echoes_game_description, mocker):
    def item(name):
        return search.find_resource_info_with_long_name(echoes_game_description.resource_database.item, name)

    mock_req_lists: MagicMock = mocker.patch(
        "randovania.generator.filler.pickup_list._requirement_lists_without_satisfied_resources"
    )

    collection = ResourceCollection.with_database(echoes_game_description.resource_database)
    pickups_left: list[PickupEntry] = []
    reach = MagicMock()
    reach.state.node_context.return_value = NodeContext(
        MagicMock(), collection, echoes_game_description.resource_database, echoes_game_description.region_list
    )
    reach.state.resources = collection
    reach.state.energy = 100
    possible_set = MagicMock()
    reach.unreachable_nodes_with_requirements.return_value = {"foo": possible_set}
    resource = MagicMock()
    uncollected_resource_node = MagicMock()
    uncollected_resource_node.resource_gain_on_collect.return_value = [(resource, 1)]
    uncollected_resource_nodes: list[ResourceNode] = [uncollected_resource_node]

    mock_req_lists.return_value = {
        RequirementList(
            [
                ResourceRequirement.simple(item("Dark Visor")),
                ResourceRequirement.create(item("Missile"), 5, False),
            ]
        ),
        RequirementList(
            [
                ResourceRequirement.simple(item("Screw Attack")),
            ]
        ),
        RequirementList(
            [
                ResourceRequirement.simple(item("Power Bomb")),
                ResourceRequirement.simple(item("Boost Ball")),
            ]
        ),
        RequirementList(
            [
                ResourceRequirement.simple(item("Spider Ball")),
                ResourceRequirement.simple(item("Boost Ball")),
            ]
        ),
    }

    # Run
    result = pickup_list.get_pickups_that_solves_unreachable(pickups_left, reach, uncollected_resource_nodes, False)

    # Assert
    mock_req_lists.assert_called_once_with(
        reach.state, [possible_set, reach.game.victory_condition_as_set.return_value], {resource}
    )
    assert result == ()


def test_pickups_to_solve_list_multiple(echoes_game_description, echoes_pickup_database, echoes_game_patches):
    # Setup
    db = echoes_game_description.resource_database
    missile_expansion = pickup_creator.create_ammo_pickup(
        echoes_pickup_database.ammo_pickups["Missile Expansion"],
        [5],
        False,
        db,
    )
    pool = [missile_expansion] * 5

    requirement = RequirementList(
        [
            ResourceRequirement.create(db.get_item("Missile"), 10, False),
        ]
    )

    resources = ResourceCollection.with_database(db)
    resources.set_resource(db.get_item("MissileLauncher"), 1)
    resources.set_resource(db.get_item("Missile"), 5)

    state = State(
        resources,
        (),
        99,
        MagicMock(),
        echoes_game_patches,
        None,
        StateGameData(
            db,
            echoes_game_description.region_list,
            100,
            99,
        ),
    )

    # Run
    result = pickup_list.pickups_to_solve_list(pool, requirement, state)

    # Assert
    assert result == [missile_expansion]


@pytest.mark.parametrize("has_light_beam", [False, True])
async def test_get_pickups_that_solves_unreachable_quad(
    small_echoes_game_description, echoes_pickup_database, default_echoes_preset, mocker, has_light_beam
):
    # Setup
    mocker.patch(
        "randovania.game_description.default_database.game_description_for", return_value=small_echoes_game_description
    )
    mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.check_item_pool",
        autospec=True,
    )

    config = default_echoes_preset.configuration
    config = dataclasses.replace(
        config,
        starting_location=StartingLocationList.with_elements(
            [NodeIdentifier.create("Temple Grounds", "Fake Quad Arena", "Before Quadraxis")],
            small_echoes_game_description.game,
        ),
        standard_pickup_configuration=config.standard_pickup_configuration.replace_state_for_pickup(
            config.standard_pickup_configuration.get_pickup_with_name("Missile Launcher"),
            StandardPickupState(
                num_included_in_starting_pickups=1,
                included_ammo=(5,),
            ),
        ),
    )
    pool = await generator.create_player_pool(Random(0), config, 0, 1, "World 1", MagicMock())
    new_game, state = pool.game_generator.bootstrap.logic_bootstrap(
        config,
        pool.game,
        pool.patches,
    )
    pickups_to_add = []
    if has_light_beam:
        pickups_to_add.append(next(p for p in pool.pickups if p.name == "Light Beam"))
    state = state.assign_pickups_resources(pickups_to_add)

    reach = reach_lib.advance_reach_with_possible_unsafe_resources(
        reach_lib.reach_with_all_safe_resources(new_game, state)
    )

    # Run
    result = pickup_list.get_pickups_that_solves_unreachable(pool.pickups, reach, [], False)
    r2 = sorted(sorted(a.name for a in it) for it in result)
    base = ["Boost Ball", "Echo Visor"]
    bomb = "Morph Ball Bomb"
    tanks = ["Energy Tank"] * 7
    missiles = ["Missile Expansion"] * 12

    if has_light_beam:
        assert r2 == [
            [*base, *tanks, bomb, "Progressive Suit", "Progressive Suit", "Spider Ball"],
            [*base, *tanks, bomb, "Progressive Suit", "Spider Ball"],
        ]
    else:
        assert r2 == [
            [*base, *tanks, "Light Beam", bomb, "Progressive Suit", "Progressive Suit", "Spider Ball"],
            [*base, *tanks, "Light Beam", bomb, "Progressive Suit", "Spider Ball"],
            [*base, *tanks, *missiles, bomb, "Progressive Suit", "Progressive Suit", "Spider Ball", "Super Missile"],
            [*base, *tanks, *missiles, bomb, "Progressive Suit", "Spider Ball", "Super Missile"],
        ]
