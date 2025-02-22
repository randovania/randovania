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


def find_prime_db_errors(game: GameDescription) -> Iterator[str]:
    yield from check_for_items_to_be_replaced_by_templates(game, use_templates_over_items)
    yield from check_for_resources_to_use_together(game, combined_resources)
