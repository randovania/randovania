from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration

BASE_WALLET_SIZE = 100
WALLET_UPGRADE_SIZE = 50
MAXIMUM_STARTING_FRUIT = 600
"""The biggest wallet: 100 fruit, plus 50 for each of the 10 Wallet Upgrades."""

BEACON_COUNT = 8


@dataclasses.dataclass(frozen=True)
class YokuConfiguration(BaseConfiguration):
    starting_fruit: int = dataclasses.field(metadata={"min": 0, "max": MAXIMUM_STARTING_FRUIT, "precision": 1})
    required_beacons: int = dataclasses.field(metadata={"min": 0, "max": BEACON_COUNT, "precision": 1})

    @property
    def maximum_starting_fruit(self) -> int:
        """What the starting wallet holds: the base wallet plus the starting Wallet Upgrades."""
        wallet = self.standard_pickup_configuration.get_pickup_with_name("Wallet Upgrade")
        upgrades = self.standard_pickup_configuration.pickups_state[wallet].num_included_in_starting_pickups
        return min(BASE_WALLET_SIZE + WALLET_UPGRADE_SIZE * upgrades, MAXIMUM_STARTING_FRUIT)

    @property
    def effective_starting_fruit(self) -> int:
        """`starting_fruit`, cut down to what the starting wallet holds."""
        return min(self.starting_fruit, self.maximum_starting_fruit)

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.YOKUS_ISLAND_EXPRESS
