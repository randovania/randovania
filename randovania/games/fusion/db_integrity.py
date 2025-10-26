from collections.abc import Iterator

from randovania.game_description.game_description import GameDescription
from randovania.game_description.integrity_check import (
    check_for_items_to_be_replaced_by_templates,
    check_for_resources_to_use_together,
)

# Short name resource -> recommended template name
use_templates_over_items = {
    "MorphBallBombData": "Can Use Bombs",
    "PowerBombs": "Can Use Power Bombs",
}

# short name resource -> Tuple(short name resources)
combined_resources = {
    "MissileData": ("Missiles",),
    "SuperMissileData": ("Missiles",),
    "IceMissileData": ("Missiles",),
    "DiffusionMissileData": ("Missiles",),
    "ShinesparkTrick": ("SpeedBooster",),
    "JBJ": ("MorphBall", "MorphBallBombData"),
    "MidAirMorph": ("MorphBall",),
    "CanSWJ": ("WallJump",),
}


def check_for_starts_in_rooms_with_multiple_states(game: GameDescription) -> Iterator[str]:
    allow_list = [("Main Deck", "Docking Bay Hangar")]

    for region in game.region_list.regions:
        for area in region.areas:
            has_start_node = area.has_start_node()
            if not has_start_node:
                continue

            if len(area.extra["room_id"]) <= 1:
                continue

            if (region.name, area.name) in allow_list:
                continue

            yield (
                f"{region.name}/{area.name} has Start Nodes! It is not recommended to do so, due to it having "
                f"multiple rooms to indicate different states. Either remove the starting Nodes, or if it's "
                f"impossible to hit the different room states in normal gameplay, add it to the Allow-List of "
                f"Fusion's integrity test."
            )


def find_fusion_db_errors(game: GameDescription) -> Iterator[str]:
    yield from check_for_items_to_be_replaced_by_templates(game, use_templates_over_items)
    yield from check_for_resources_to_use_together(game, combined_resources)
    yield from check_for_starts_in_rooms_with_multiple_states(game)
