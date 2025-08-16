from __future__ import annotations

from randovania.game_description.resources.resource_collection import ResourceCollection


def test_remove_resource_exists(echoes_game_description):
    m = echoes_game_description.resource_database.get_item("Missile")
    beam = echoes_game_description.resource_database.get_item("Light")
    col = ResourceCollection.from_dict(
        echoes_game_description,
        {
            m: 10,
            beam: 1,
        },
    )
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}


def test_remove_resource_missing(echoes_game_description):
    m = echoes_game_description.resource_database.get_item("Missile")
    beam = echoes_game_description.resource_database.get_item("Light")
    col = ResourceCollection.from_dict(
        echoes_game_description,
        {
            beam: 1,
        },
    )
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}
