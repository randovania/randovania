from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING, Self

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock_node import DockNode
from randovania.games.prime2.generator.teleporter_distributor import get_teleporter_connections_echoes
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement, TranslatorConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory, MissingRng, weaknesses_for_unlocked_saves
from randovania.generator.teleporter_distributor import get_dock_connections_assignment_for_teleporter
from randovania.layout.lib.teleporters import TeleporterConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches


@dataclasses.dataclass(frozen=True)
class WorldEntrances:
    front: AreaIdentifier
    left: AreaIdentifier
    right: AreaIdentifier

    @classmethod
    def create(cls, world: str, front: str, left: str, right: str) -> Self:
        return cls(
            front=AreaIdentifier(world, front),
            left=AreaIdentifier(world, left),
            right=AreaIdentifier(world, right),
        )


WORLDS = [
    WorldEntrances.create(
        "Great Temple",
        front="Temple Transport A",  # Sanc
        left="Temple Transport B",  # Agon
        right="Temple Transport C",  # Torvus
    ),
    WorldEntrances.create(
        "Agon Wastes",
        front="Transport to Temple Grounds",
        left="Transport to Sanctuary Fortress",
        right="Transport to Torvus Bog",
    ),
    WorldEntrances.create(
        "Torvus Bog",
        front="Transport to Temple Grounds",
        left="Transport to Agon Wastes",
        right="Transport to Sanctuary Fortress",
    ),
    WorldEntrances.create(
        "Sanctuary Fortress",
        front="Transport to Temple Grounds",
        left="Transport to Torvus Bog",
        right="Transport to Agon Wastes",
    ),
]


class SharedEchoesBasePatches:
    """Shared logic between Echoes and EchoesOPR"""

    @staticmethod
    def unlock_save_doors(blue_save_doors: bool, game: GameDatabaseView, initial_patches: GamePatches) -> GamePatches:
        """Apply patches to unlock save doors, if the option is set."""

        dock_weakness: list[tuple[DockNode, DockWeakness]] = []

        if blue_save_doors:
            dock_weakness.extend(
                weaknesses_for_unlocked_saves(
                    game,
                    unlocked_weakness=game.get_dock_weakness("door", "Normal Door (Forced)"),
                    target_dock_type=game.find_dock_type_by_short_name("door"),
                    area_filter=lambda area: area.extra.get("unlocked_save_station") is True,
                )
            )

        return initial_patches.assign_dock_weakness(dock_weakness)

    @staticmethod
    def teleporter_assignment(
        teleporter_config: TeleporterConfiguration, game: GameDatabaseView, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        """Assign teleporter targets."""

        teleporter_connection = get_teleporter_connections_echoes(teleporter_config, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(teleporter_config, game, teleporter_connection)

        yield from dock_assignment

    @staticmethod
    def translator_gates(translator_config: TranslatorConfiguration, rng: Random) -> dict[str, str]:
        """Create specific patches for translator gates."""

        all_choices = list(LayoutTranslatorRequirement)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM_WITH_REMOVED)
        without_removed = copy.copy(all_choices)
        without_removed.remove(LayoutTranslatorRequirement.REMOVED)
        random_requirements = {LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED}

        translator_gates = {}

        for identifier, requirement in translator_config.translator_requirement.items():
            if requirement in random_requirements:
                if rng is None:
                    raise MissingRng("Translator")

                requirement = rng.choice(
                    all_choices if requirement == LayoutTranslatorRequirement.RANDOM_WITH_REMOVED else without_removed
                )

            translator_gates[identifier.as_string] = requirement.value

        return translator_gates


class EchoesBasePatchesFactory(BasePatchesFactory[EchoesConfiguration]):
    def assign_static_dock_weakness(
        self, configuration: EchoesConfiguration, game: GameDatabaseView, initial_patches: GamePatches
    ) -> GamePatches:
        parent = super().assign_static_dock_weakness(configuration, game, initial_patches)
        return SharedEchoesBasePatches.unlock_save_doors(configuration.blue_save_doors, game, parent)

    def dock_connections_assignment(
        self, configuration: EchoesConfiguration, game: GameDatabaseView, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        yield from super().dock_connections_assignment(configuration, game, rng)
        yield from SharedEchoesBasePatches.teleporter_assignment(configuration.teleporters, game, rng)

    def create_game_specific(self, configuration: EchoesConfiguration, game: GameDescription, rng: Random) -> dict:
        return {
            "translator_gates": SharedEchoesBasePatches.translator_gates(configuration.translator_configuration, rng),
        }
