from __future__ import annotations

import copy
import dataclasses

from randovania.game_description.db.region_list import RegionList
from randovania.game_description.game_description import GameDescription


def remove_inactive_layers(game: GameDescription, active_layers: set[str]) -> GameDescription:
    if unknown_layers := active_layers - set(game.layers):
        raise ValueError(f"Unknown layers: {unknown_layers}")

    regions = []

    for region in game.region_list.regions:
        areas = []
        for area in region.areas:
            nodes = copy.copy(area.nodes)
            connections = {node: copy.copy(connection) for node, connection in area.connections.items()}
            for node in area.nodes:
                if set(node.layers).isdisjoint(active_layers):
                    nodes.remove(node)
                    connections.pop(node, None)
                    for connection in connections.values():
                        connection.pop(node, None)

            areas.append(
                dataclasses.replace(
                    area.duplicate(),
                    nodes=nodes,
                    connections=connections,
                )
            )

        regions.append(dataclasses.replace(region, areas=areas))

    return GameDescription(
        game=game.game,
        resource_database=game.resource_database,
        layers=game.layers,
        dock_weakness_database=game.dock_weakness_database,
        hint_feature_database=game.hint_feature_database,
        region_list=RegionList(regions, game.region_list.flatten_to_set_on_patch),
        victory_condition=game.victory_condition,
        starting_location=game.starting_location,
        minimal_logic=game.minimal_logic,
    )
