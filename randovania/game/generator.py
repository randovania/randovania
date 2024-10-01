from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from randovania.generator.filler.weights import (
    DEFAULT_INDICES_WEIGHT_MULTIPLIER,
    DEFAULT_EVENTS_WEIGHT_MULTIPLIER,
    DEFAULT_HINTS_WEIGHT_MULTIPLIER,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.game_description import GameDescription
    from randovania.generator.base_patches_factory import BasePatchesFactory
    from randovania.generator.hint_distributor import HintDistributor
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.bootstrap import Bootstrap


@dataclass(frozen=True)
class GameGenerator:
    pickup_pool_creator: Callable[[PoolResults, BaseConfiguration, GameDescription], None]
    """Extends the base pickup pools with any specific item pools such as Artifacts."""

    bootstrap: Bootstrap
    """Modifies the resource database and starting resources before generation."""

    base_patches_factory: BasePatchesFactory
    # TODO Revise this text
    """Creates base patches, such as teleporter or configurable node assignments."""

    hint_distributor: HintDistributor
    """Use AllJokesDistributor if not using hints."""


    indices_weight: float = DEFAULT_INDICES_WEIGHT_MULTIPLIER
    """
    While weighting an action during generation, indicates the weight that will be added if
    the action unlocks Pickup nodes.
    """

    events_weight: float = DEFAULT_EVENTS_WEIGHT_MULTIPLIER
    """
    While weighting an action during generation, indicates the weight that will be added if
    the action unlocks Event nodes.
    """

    hints_weight: float = DEFAULT_HINTS_WEIGHT_MULTIPLIER
    """
    While weighting an action during generation, indicates the weight that will be added if
    the action unlocks Hint nodes.
    """
