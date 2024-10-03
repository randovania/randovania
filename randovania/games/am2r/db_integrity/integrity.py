import typing
from collections.abc import Iterator

from randovania.db_integrity.integrity import items_to_be_replaced_by_templates, resources_to_use_together
from randovania.game_description.db.node import NodeContext
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.layout.base.base_configuration import BaseConfiguration

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
    context = NodeContext(
        patches=GamePatches.create_from_game(game, 0, typing.cast(BaseConfiguration, None)),
        current_resources=ResourceCollection.with_database(game.resource_database),
        database=game.resource_database,
        node_provider=game.region_list,
    )

    yield from items_to_be_replaced_by_templates(game, context, use_templates_over_items)
    yield from resources_to_use_together(game, context, combined_resources)
