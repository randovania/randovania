from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.pseudoregalia.layout.pseudoregalia_configuration import PseudoregaliaConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration

key_regions = [
    "Tower Remains",
    "Empty Bailey",
    "Sansa Keep",
    "The Underbelly",
    "Twilight Theatre",
]


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, PseudoregaliaConfiguration)

    keys = [
        create_generated_pickup(
            "Major Key",
            game.resource_database,
            game.get_pickup_database(),
            region=region,
            region_short=region.replace(" ", ""),
        )
        for region in key_regions
    ]
    keys_to_shuffle = keys[: configuration.required_keys]
    starting_keys = keys[configuration.required_keys :]

    results.extend_with(PoolResults(keys_to_shuffle, {}, starting_keys))
