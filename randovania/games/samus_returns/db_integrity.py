from collections.abc import Iterator

from randovania.game_description.game_description import GameDescription
from randovania.game_description.integrity_check import (
    check_for_items_to_be_replaced_by_templates,
    check_for_resources_to_use_together,
)

# Short name resource -> recommended template name
use_templates_over_items = {
    "Spring": "Use Spring Ball",
    "Spider": "Use Spider Ball",
    "Bomb": "Lay Bomb or Lay Any Bomb",
    "PBAmmo": "Lay Power Bomb or Lay Any Bomb",
}

# short name resource -> Tuple(short name resources)
combined_resources = {
    "Spider": ("Morph",),
    "Spring": ("Morph",),
    "Bomb": ("Morph",),
    "PBAmmo": ("Morph",),
    "IBJ": ("Morph", "Bomb"),
    "DBJ": ("Morph", "Bomb"),
    "UBJ": ("Morph", "Bomb"),
    "FrozenEnemy": ("Ice",),
    "SpiderClip": ("Morph", "Spider", "OoB"),
    "IceClip": ("Ice", "OoB"),
    "PhaseClip": ("Morph", "Phase", "OoB"),
    "MeleeClip": ("Morph", "OoB"),
    "UnmorphExtend": ("Morph",),
    "AirMorph": ("Morph",),
    "SpiderBoost": ("Morph", "Spider", "PBAmmo"),
    "Freeze": ("Ice",),
    "HazardRuns": ("Hazard",),
}


def find_msr_db_errors(game: GameDescription) -> Iterator[str]:
    yield from check_for_items_to_be_replaced_by_templates(game, use_templates_over_items)
    yield from check_for_resources_to_use_together(game, combined_resources)
