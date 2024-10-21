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
    "MorphBallBombData": "Can Use Bombs",
    "PowerBombs": "Can Use Spider Ball",
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
}


def find_fusion_db_errors(game: GameDescription) -> Iterator[str]:
    context = NodeContext(
        patches=GamePatches.create_from_game(game, 0, typing.cast(BaseConfiguration, None)),
        current_resources=ResourceCollection.with_database(game.resource_database),
        database=game.resource_database,
        node_provider=game.region_list,
    )

    yield from items_to_be_replaced_by_templates(game, context, use_templates_over_items)
    yield from resources_to_use_together(game, context, combined_resources)
