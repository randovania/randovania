from __future__ import annotations

from randovania.game_description.resources.resource_collection import ResourceCollection


def test_remove_resource_exists(echoes_game_description):
    db = echoes_game_description.resource_database
    m = db.get_item("Missile")
    beam = db.get_item("Light")
    col = ResourceCollection.from_dict(
        db,
        {
            m: 10,
            beam: 1,
        },
    )
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}


def test_remove_resource_missing(echoes_game_description):
    db = echoes_game_description.resource_database
    m = db.get_item("Missile")
    beam = db.get_item("Light")
    col = ResourceCollection.from_dict(
        db,
        {
            beam: 1,
        },
    )
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}
