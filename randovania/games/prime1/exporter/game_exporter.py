from __future__ import annotations

import copy
import dataclasses
import json
import os
from pathlib import Path
from textwrap import wrap
from typing import TYPE_CHECKING

from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams, input_hash_for_file
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.pickup.pickup_entry import PickupModel
from randovania.games.common.prime_family.exporter import good_hashes
from randovania.games.prime1.layout.prime_configuration import RoomRandoMode
from randovania.lib.status_update_lib import DynamicSplitProgressUpdate
from randovania.patching.patchers.exceptions import UnableToExportError

if TYPE_CHECKING:
    from randovania.game_description.db.dock import DockType
    from randovania.game_description.db.region import Region
    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class PrimeGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path
    echoes_input_path: Path
    asset_cache_path: Path
    use_echoes_models: bool
    cache_path: Path

    def calculate_input_hash(self) -> dict[str, str | None]:
        return {
            "prime1_iso": input_hash_for_file(self.input_path),
            "prime2_iso": input_hash_for_file(self.echoes_input_path),
        }


def adjust_model_names(patch_data: dict, assets_meta: dict, use_external_assets: bool):
    model_list = []
    if use_external_assets:
        bad_models = {
            "prime2_MissileLauncher",
            "prime2_MissileExpansionPrime1",
            "prime2_CoinChest",
        }
        model_list = list(set(assets_meta["items"]) - bad_models)

    for level in patch_data["levelData"].values():
        for room in level.get("rooms", {}).values():
            for pickup in room.get("pickups", []):
                model = PickupModel.from_json(pickup.pop("model"))
                original_model = PickupModel.from_json(pickup.pop("original_model"))

                converted_model_name = f"{original_model.game.value}_{original_model.name}"
                if converted_model_name not in model_list:
                    converted_model_name = model.name

                pickup["model"] = converted_model_name


def create_map_using_matplotlib(room_connections: list[tuple[str, str]], filepath: Path):
    import logging

    import networkx
    import numpy

    for name in ["matplotlib", "matplotlib.font", "matplotlib.pyplot"]:
        logger = logging.getLogger(name)
        logger.setLevel(logging.CRITICAL)
        logger.disabled = True

    import matplotlib

    matplotlib._log.disabled = True
    from matplotlib import pyplot

    # model this world's connections as a graph
    graph = networkx.DiGraph()
    graph.add_edges_from(room_connections)

    # render the graph to png
    pos = networkx.spring_layout(graph, k=1.2 / numpy.sqrt(len(graph.nodes())), iterations=100, seed=0)
    pyplot.figure(3, figsize=(22, 22))
    networkx.draw(graph, pos=pos, node_size=800)
    networkx.draw_networkx_labels(graph, pos=pos, font_weight="bold", font_size=4)
    pyplot.savefig(filepath, bbox_inches="tight", dpi=220)

    # reset for next graph
    pyplot.clf()


def make_one_map(filepath: Path, level_data: dict, region: Region, dock_types_to_ignore: list[DockType]):
    from randovania.game_description.db.dock_node import DockNode

    def wrap_text(text):
        return "\n".join(wrap(text, 18))

    # make list of all edges between rooms
    room_connections = []

    # add edges which were not shuffled
    disabled_doors = set()

    for area in region.areas:
        dock_nodes = [node for node in area.nodes if isinstance(node, DockNode)]
        for node in dock_nodes:
            if node.dock_type in dock_types_to_ignore:
                continue

            src_name = area.name
            src_dock_num = node.extra["dock_index"]

            if node.default_dock_weakness.name == "Permanently Locked":
                disabled_doors.add((src_name, src_dock_num))

            if node.extra["nonstandard"]:
                dst_name = node.default_connection.area_identifier.area
                room_connections.append((wrap_text(src_name), wrap_text(dst_name)))

    # add edges which were shuffled
    for room_name in level_data[region.name]["rooms"].keys():
        room = level_data[region.name]["rooms"][room_name]
        if "doors" not in room.keys():
            continue

        for dock_num in room["doors"]:
            if "destination" not in room["doors"][dock_num].keys():
                continue

            if (room_name, int(dock_num)) in disabled_doors:
                continue

            dst_room_name = room["doors"][dock_num]["destination"]["roomName"]
            room_connections.append((wrap_text(room_name), wrap_text(dst_room_name)))

    create_map_using_matplotlib(room_connections, filepath)


class PrimeGameExporter(GameExporter):
    @property
    def can_start_new_export(self) -> bool:
        """
        Checks if the patcher is busy right now
        """
        return False

    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if patch_game can be aborted
        """
        return False

    def export_params_type(self) -> type[GameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return PrimeGameExportParams

    @monitoring.trace_function
    def make_room_rando_maps(self, directory: Path, base_filename: str, level_data: dict):
        game_description = default_database.game_description_for(RandovaniaGame.METROID_PRIME)
        rl = game_description.region_list
        dock_types_to_ignore = game_description.dock_weakness_database.all_teleporter_dock_types

        for region_name in level_data.keys():
            filepath = directory.with_name(f"{base_filename} {region_name}.png")
            make_one_map(filepath, level_data, rl.region_with_name(region_name), dock_types_to_ignore)

    def known_good_hashes(self) -> dict[str, tuple[str, ...]]:
        return {
            "prime1_iso": good_hashes.PRIME1_GC_ISOS,
            "prime2_iso": good_hashes.PRIME2_GC_ISOS,
        }

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        assert isinstance(export_params, PrimeGameExportParams)

        input_file = export_params.input_path
        output_file = export_params.output_path

        export_params.cache_path.mkdir(parents=True, exist_ok=True)
        cache_dir = os.fspath(export_params.cache_path)

        monitoring.set_tag("prime_output_format", output_file.suffix)

        import py_randomprime
        from open_prime_rando.dol_patching import all_prime_dol_patches
        from ppc_asm import assembler
        from Random_Enemy_Attributes.Random_Enemy_Attributes import PyRandom_Enemy_Attributes
        from retro_data_structures.game_check import Game as RDSGame

        symbols = py_randomprime.symbols_for_file(input_file)
        if symbols is None:
            raise UnableToExportError("Unsupported Metroid Prime version.")

        new_config = copy.copy(patch_data)
        has_spoiler = new_config.pop("hasSpoiler")
        room_rando_mode = new_config.pop("roomRandoMode")
        new_config["inputIso"] = os.fspath(input_file)
        new_config["outputIso"] = os.fspath(output_file)
        new_config["gameConfig"]["updateHintStateReplacement"] = list(
            assembler.assemble_instructions(
                symbols["UpdateHintState__13CStateManagerFf"],
                all_prime_dol_patches.remote_execution_patch(RDSGame.PRIME),
                symbols=symbols,
            )
        )
        new_config["preferences"]["cacheDir"] = cache_dir

        random_enemy_attributes = new_config.pop("randEnemyAttributes")
        random_enemy_attributes_seed = new_config.pop("seed")

        monitoring.set_tag("prime_room_rando_mode", room_rando_mode)
        monitoring.set_tag("prime_random_enemy_attributes", random_enemy_attributes is not None)

        split_updater = DynamicSplitProgressUpdate(progress_update)
        asset_updater = None
        enemy_updater = None

        if export_params.use_echoes_models:
            asset_updater = split_updater.create_split()
        randomprime_updater = split_updater.create_split(weight=2.0)
        if random_enemy_attributes is not None:
            enemy_updater = split_updater.create_split()

        from randovania.patching.prime import asset_conversion

        assets_meta = {}
        if export_params.use_echoes_models:
            assets_path = export_params.asset_cache_path
            assets_meta = asset_conversion.convert_prime2_pickups(
                export_params.echoes_input_path, assets_path, asset_updater
            )
            new_config["externAssetsDir"] = os.fspath(assets_path)
        else:
            asset_conversion.delete_converted_assets(export_params.asset_cache_path)

        # Replace models
        adjust_model_names(new_config, assets_meta, export_params.use_echoes_models)

        patch_as_str = json.dumps(new_config, indent=4, separators=(",", ": "))
        if has_spoiler:
            output_file.with_name(f"{output_file.stem}-patcher.json").write_text(patch_as_str)
            if room_rando_mode != RoomRandoMode.NONE.value:
                self.make_room_rando_maps(output_file, f"{output_file.stem}", new_config["levelData"])

        os.environ["RUST_BACKTRACE"] = "1"

        try:
            with monitoring.trace_block("py_randomprime.patch_iso_raw"):
                py_randomprime.patch_iso_raw(
                    patch_as_str,
                    py_randomprime.ProgressNotifier(lambda percent, msg: randomprime_updater(msg, percent)),
                )
        except BaseException as e:
            if isinstance(e, Exception):
                raise
            else:
                raise RuntimeError(f"randomprime panic: {e}") from e

        if random_enemy_attributes is not None:
            enemy_updater("Randomizing enemy attributes", 0)
            with monitoring.trace_block("PyRandom_Enemy_Attributes"):
                PyRandom_Enemy_Attributes(
                    new_config["inputIso"],
                    new_config["outputIso"],
                    random_enemy_attributes_seed,
                    random_enemy_attributes["enemy_rando_range_scale_low"],
                    random_enemy_attributes["enemy_rando_range_scale_high"],
                    random_enemy_attributes["enemy_rando_range_health_low"],
                    random_enemy_attributes["enemy_rando_range_health_high"],
                    random_enemy_attributes["enemy_rando_range_speed_low"],
                    random_enemy_attributes["enemy_rando_range_speed_high"],
                    random_enemy_attributes["enemy_rando_range_damage_low"],
                    random_enemy_attributes["enemy_rando_range_damage_high"],
                    random_enemy_attributes["enemy_rando_range_knockback_low"],
                    random_enemy_attributes["enemy_rando_range_knockback_high"],
                    random_enemy_attributes["enemy_rando_diff_xyz"],
                )
            enemy_updater("Finished randomizing enemy attributes", 1)
