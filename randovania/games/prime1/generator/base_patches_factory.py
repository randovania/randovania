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

        nic = NodeIdentifier.create
        power_weak = game.dock_weakness_database.get_by_weakness("door", "Normal Door")

        if configuration.main_plaza_door and configuration.dock_rando.mode == DockRandoMode.VANILLA:
            dock_weakness.append(
                (nic("Chozo Ruins", "Main Plaza", "Door from Plaza Access"), power_weak),
            )
        
        if configuration.blue_save_doors:
            save_doors = [
                nic("Chozo Ruins", "Save Station 1", "Door to Ruined Nursery"),
                nic("Chozo Ruins", "Save Station 2", "Door to Gathering Hall"),
                nic("Chozo Ruins", "Save Station 3", "Door to Reflecting Pool"),
                nic("Magmoor Caverns", "Save Station Magmoor A", "Door to Burning Trail"),
                nic("Magmoor Caverns", "Save Station Magmoor B", "Door to Transport to Phendrana Drifts South"),
                nic("Phazon Mines", "Save Station Mines A", "Door to Main Quarry"),
                nic("Phazon Mines", "Save Station Mines B", "Door to Central Dynamo"),
                nic("Phazon Mines", "Save Station Mines C", "Door to Metroid Quarantine B"),
                nic("Phendrana Drifts", "Save Station A", "Door to Ruined Courtyard"),
                nic("Phendrana Drifts", "Save Station B", "Door to Phendrana Shorelines"),
                nic("Phendrana Drifts", "Save Station C", "Door to Frost Cave"),
                nic("Phendrana Drifts", "Save Station D", "Door to Observatory"),
                nic("Tallon Overworld", "Savestation", "Door to Reactor Access"),
            ]
            save_doors = [game.world_list.node_by_identifier(identifier) for identifier in save_doors]
            
            # FIXME: including the dock connection may break when logical entrance rando is introduced
            save_doors.extend([parent.get_dock_connection_for(node) for node in save_doors])
            
            dock_weakness.extend((
                (node.identifier, power_weak)
                for node in save_doors
            ))

        return parent.assign_dock_weakness((
            (game.world_list.node_by_identifier(identifier), target)
            for identifier, target in dock_weakness
        ))
