CURRENT_DATABASE_VERSION = 2


def _migrate_v1(data: dict) -> dict:

    for world in data["worlds"]:
        new_areas = {}

        if world.get("extra") is None:
            world["extra"] = {}

        world["extra"]["asset_id"] = world.pop("asset_id")
        if (dark_name := world.pop("dark_name")) is not None:
            world["extra"]["dark_name"] = dark_name

        for area in world["areas"]:
            area_name = area.pop("name")
            if area_name in new_areas:
                raise ValueError("Name conflict in {}: {}".format(world["name"], area_name))

            if area.get("extra") is None:
                area["extra"] = {}

            area["extra"]["asset_id"] = area.pop("asset_id")
            if dark_name is not None:
                area["extra"]["in_dark_aether"] = area.pop("in_dark_aether")

            new_nodes = {}
            for node in area["nodes"]:
                node_name = node.pop("name")

                if node_name in new_nodes:
                    raise ValueError("Name conflict in {} - {}: {}".format(world["name"], area_name, node_name))

                new_nodes[node_name] = node

            area["nodes"] = new_nodes
            new_areas[area_name] = area

        world["areas"] = new_areas

    return data


_MIGRATIONS = {
    1: _migrate_v1,
}


def migrate_to_current(data: dict) -> dict:
    schema_version = data.get("schema_version", 1)

    while schema_version < CURRENT_DATABASE_VERSION:
        data = _MIGRATIONS[schema_version](data)
        schema_version += 1
        data["schema_version"] = schema_version

    return data
