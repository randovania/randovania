import copy
import json
import os
import typing
from pathlib import Path
from random import Random
from typing import Optional, List, Union

import randovania
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import PickupNode, TeleporterNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.deltarune.layout.deltarune_configuration import deltaruneConfiguration
from randovania.games.deltarune.layout.deltarune_cosmetic_patches import deltaruneCosmeticPatches
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.patching.patcher import Patcher
from randovania.patching.prime.patcher_file_lib import pickup_exporter, item_names, guaranteed_item_hint, hint_lib, \
    credits_spoiler

def deltarune_pickup_details_to_patcher(detail: pickup_exporter.ExportedPickupDetails,
                                     rng: Random) -> dict:

    pickup_type = -1
    count = 0

    for resource, quantity in detail.conditional_resources[0].resources:
        if resource.extra["item_id"] >= 1000:
            continue
        pickup_type = resource.extra["item_id"]
        count = quantity
        break

class PatcherMaker(Patcher):

    _busy: bool = False

    @property
    def is_busy(self) -> bool:
        """
        Checks if the patcher is busy right now
        """
        return self._busy

    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if patch_game can be aborted
        """
        return False

    @property
    def uses_input_file_directly(self) -> bool:
        """
        Does this patcher uses the input file directly?
        """
        return True
        
    def has_internal_copy(self, game_files_path: Path) -> bool:
        return False

    def delete_internal_copy(self, game_files_path: Path):
        pass
        
    def default_output_file(self, seed_hash: str) -> str:
        return "Deltarune Randomizer - {}".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return ["txt"]

    @property
    def valid_output_file_types(self) -> List[str]:
        return ["txt"]

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: deltaruneCosmeticPatches):
        patches = description.all_patches[players_config.player_index]
        db = default_database.game_description_for(RandovaniaGame.DELTARUNE)
        configuration = description.get_preset(players_config.player_index).configuration
        assert isinstance(configuration, deltaruneConfiguration)
        rng = Random(description.get_seed_for_player(players_config.player_index))


        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(db.resource_database),
                                      players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            patches,
            useless_target,
            db.world_list,
            rng,
            configuration.pickup_model_style,
            configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(db, pickup_exporter.GenericAcquiredMemo(), players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        world_data = {}


        for world in db.world_list.worlds:

            world_data[world.name] = {
                "transports": {},
                "rooms": {}
            }
            for area in world.areas:
                pickup_indices = sorted(node.pickup_index for node in area.nodes if isinstance(node, PickupNode))
                if pickup_indices:
                    world_data[world.name]["rooms"][area.name] = {
                        "pickups": [
                            deltarune_pickup_details_to_patcher(pickup_list[index.index],
                                                             rng)
                            for index in pickup_indices
                        ],
                    }
                for node in area.nodes:
                    if not isinstance(node, TeleporterNode) or not node.editable:
                        continue

                    identifier = db.world_list.identifier_for_node(node)
                    target = _name_for_location(db.world_list, patches.elevator_connection[identifier])

                    source_name = prime1_elevators.RANDOM_PRIME_CUSTOM_NAMES[(
                        identifier.area_location.world_name,
                        identifier.area_location.area_name,
                    )]
                    world_data[world.name]["transports"][source_name] = target

        starting_memo = None
        extra_starting = item_names.additional_starting_items(configuration, db.resource_database,
                                                              patches.starting_items)
        if extra_starting:
            starting_memo = ", ".join(extra_starting)



        # Tweaks
        ctwk_config = {}


        starting_room = _name_for_location(db.world_list, patches.starting_location)

        starting_items = {
            name: _starting_items_value_for(db.resource_database, patches.starting_items, index)
            for name, index in _STARTING_ITEM_NAME_TO_INDEX.items()
        }

        return {
            "seed": description.get_seed_for_player(players_config.player_index),
            "preferences": {
            },
            "gameConfig": {
                "shufflePickupPosition": configuration.shuffle_item_pos,
                "shufflePickupPosAllRooms": configuration.items_every_room,
                "startingRoom": starting_room,

                "startingItems": starting_items,

            },
            "tweaks": ctwk_config,
            "levelData": world_data,
            "hasSpoiler": description.has_spoiler,

            # TODO
            # "externAssetsDir": path_to_converted_assets,
        }

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   internal_copies_path: Path, progress_update: ProgressUpdateCallable):
        if input_file is None:
            raise ValueError("Missing input file")

        new_config = copy.copy(patch_data)
        has_spoiler = new_config.pop("hasSpoiler")
        new_config["input"] = os.fspath(input_file)
        new_config["output"] = os.fspath(output_file)

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        if has_spoiler:
            output_file.with_name(f"{output_file.stem}-patcher.json").write_text(patch_as_str)

        os.environ["RUST_BACKTRACE"] = "1"

        try:
            output_file.with_name(f"{output_file.stem}.json").write_text(patch_as_str)
        except BaseException as e:
            if isinstance(e, Exception):
                raise
            else:
                raise RuntimeError(f"randomprime panic: {e}") from e

