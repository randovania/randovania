from collections.abc import Iterator

from randovania.game_description.game_description import GameDescription
from randovania.game_description.integrity_check import (
    check_for_items_to_be_replaced_by_templates,
    check_for_resources_to_use_together,
)

# Short name resource -> recommended template name
use_templates_over_items = {
    "Bombs": "Can Use Bombs",
    "Spider Ball": "Can Use Spider Ball",
    "Spring Ball": "Can Use Spring Ball",
    "Power Bombs": "Can Use Power Bombs",
    "Walljump Boots": "Can Walljump",
    "Infinite Bomb Propulsion": "Can IBJ",
}

# short name resource -> Tuple(short name resources)
combined_resources = {
    "Walljump": ("Walljump Boots",),
    "IBJ": ("Infinite Bomb Propulsion", "Bombs", "Morph Ball"),
    "MidAirMorph": ("Morph Ball",),
    "Shinesparking": ("Speed Booster",),
    "MorphGlide": ("Morph Ball",),
    "ShortCharge": ("Speed Booster",),
    "DiagonalIBJ": ("Infinite Bomb Propulsion", "Bombs", "Morph Ball"),
    "Zip": ("Walljump Boots",),
    "ChargedBombJump": ("Charge Beam", "Bombs", "Morph Ball"),
    "MissileLessMetroids": ("Charge Beam",),
}


def find_am2r_db_errors(game: GameDescription) -> Iterator[str]:
    yield from check_for_items_to_be_replaced_by_templates(game, use_templates_over_items)
    yield from check_for_resources_to_use_together(game, combined_resources)
