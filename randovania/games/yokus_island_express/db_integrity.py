from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.game_description import GameDescription


def check_starting_locations(game: GameDescription) -> Iterator[str]:
    """The exporter sends a start node as its area's level and the node's ball spawner."""
    for region in game.region_list.regions:
        for area in region.areas:
            for node in area.nodes:
                if not node.valid_starting_location:
                    continue
                if not isinstance(area.extra.get("level"), str):
                    yield f"{node.identifier.as_string} is a starting location, but its area has no 'level' extra"
                spawner = node.extra.get("spawner")
                if not isinstance(spawner, int) or isinstance(spawner, bool) or spawner < -1:
                    yield (
                        f"{node.identifier.as_string} is a starting location, but has no 'spawner' extra: the object "
                        "id of a ball_spawner or special_checkpoint, or -1 for the level's default spawner"
                    )


def find_yoku_db_errors(game: GameDescription) -> Iterator[str]:
    yield from check_starting_locations(game)
