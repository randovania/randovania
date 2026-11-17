from collections.abc import Iterator

from randovania.game_description.game_description import GameDescription
from randovania.game_description.integrity_check import (
    check_for_items_to_be_replaced_by_templates,
    check_for_resources_to_use_together,
)

# Short name resource -> recommended template name
use_templates_over_items = {
    "Boost": "Can Use Boost Ball",
    "Spider": "Can Use Spider Ball",
    "Bombs": "Can Use Bombs",
    "PowerBomb": "Can Use Power Bombs",
}

# short name resource -> Tuple(short name resources)
combined_resources = {
    "Boost": ("MorphBall",),
    "Spider": ("MorphBall",),
    "Bombs": ("MorphBall",),
    "PowerBomb": ("MorphBall",),
}


def check_for_existing_world_coords(game: GameDescription) -> Iterator[str]:
    for region, area, source_node in game.node_iterator():
        # TODO: Impact crater and frigate aren't filled in yet hence ignored.
        # Credits doesn't have coordinates.
        if region.name in ["Impact Crater", "Frigate Orpheon", "End of Game"]:
            continue
        # These can spawn anywhere in the room and don't have set coordinates.
        if "items_every_room" in source_node.layers:
            continue
        # Ignore automatically generated nodes
        if source_node.is_derived_node:
            continue

        if "world_position" not in source_node.extra:
            yield (
                f"{source_node.full_name()} is missing the 'world_position' extra field which describes "
                f"internal world coordinates (X, Y, Z). You can get them from PrimeWorldEditor."
            )
        elif len(source_node.extra["world_position"]) != 3:
            yield (
                f"The world_position of {source_node.full_name()} are incorrect. You need 3 entries"
                f" for X, Y and Z respectively."
            )


def find_prime_db_errors(game: GameDescription) -> Iterator[str]:
    yield from check_for_items_to_be_replaced_by_templates(game, use_templates_over_items)
    yield from check_for_resources_to_use_together(game, combined_resources)
    yield from check_for_existing_world_coords(game)
