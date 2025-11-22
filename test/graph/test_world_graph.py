from __future__ import annotations

from randovania.graph import world_graph


def test_create_graph(
    blank_game_description,
    blank_game_patches,
) -> None:
    starting_resources = blank_game_description.resource_database.create_resource_collection()
    graph = world_graph.create_graph(
        blank_game_description,
        blank_game_patches,
        starting_resources,
        damage_multiplier=1.0,
        victory_condition=blank_game_description.victory_condition,
        flatten_to_set_on_patch=False,
    )

    assert len(graph.nodes) == 39
    assert graph.dangerous_resources == set()
