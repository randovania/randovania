from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout import HuntersConfiguration
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.generator.base_patches_factory import BasePatchesFactory, MissingRng

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_description import GameDescription


class HuntersBasePatchesFactory(BasePatchesFactory[HuntersConfiguration]):
    def create_game_specific(self, configuration: HuntersConfiguration, game: GameDescription, rng: Random) -> dict:
        all_choices = list(LayoutForceFieldRequirement)
        all_choices.remove(LayoutForceFieldRequirement.RANDOM)
        without_removed = copy(all_choices)

        force_fields: dict = {}

        for identifier, requirement in configuration.force_field_configuration.force_field_requirement.items():
            if requirement == LayoutForceFieldRequirement.RANDOM:
                if rng is None:
                    raise MissingRng("Force Field")

                requirement = rng.choice(without_removed)

            force_fields[identifier.as_string] = requirement.value

        return {
            "force_fields": force_fields,
        }
