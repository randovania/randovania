from randovania.game_description.resources.resource_info import ResourceCollection


def test_remove_resource_exists(echoes_resource_database):
    m = echoes_resource_database.get_item("Missile")
    beam = echoes_resource_database.get_item("Light")
    col = ResourceCollection.from_dict(echoes_resource_database, {
        m: 10,
        beam: 1,
    })
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}


def test_remove_resource_missing(echoes_resource_database):
    m = echoes_resource_database.get_item("Missile")
    beam = echoes_resource_database.get_item("Light")
    col = ResourceCollection.from_dict(echoes_resource_database, {
        beam: 1,
    })
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}
