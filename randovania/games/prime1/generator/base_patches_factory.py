from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.generator.base_patches_factory import PrimeTrilogyBasePatchesFactory
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode


class PrimeBasePatchesFactory(PrimeTrilogyBasePatchesFactory):
    def create_base_patches(self,
                            configuration: BaseConfiguration,
                            rng: Random,
                            game: GameDescription,
                            is_multiworld: bool,
                            player_index: int,
                            rng_required: bool = True
                            ) -> GamePatches:
        assert isinstance(configuration, PrimeConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)

        dock_weakness = []
        if configuration.main_plaza_door and configuration.dock_rando.mode == DockRandoMode.VANILLA:
            nic = NodeIdentifier.create
            power_weak = game.dock_weakness_database.get_by_weakness("door", "Normal Door")

            dock_weakness.append(
                (nic("Chozo Ruins", "Main Plaza", "Door from Plaza Access"), power_weak),
            )

        return parent.assign_dock_weakness((
            (game.world_list.node_by_identifier(identifier), target)
            for identifier, target in dock_weakness
        ))
