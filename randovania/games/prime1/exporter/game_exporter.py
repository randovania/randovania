import copy
import dataclasses
import json
import os
import shutil
from pathlib import Path
from textwrap import wrap

import py_randomprime

from randovania.dol_patching import assembler
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.game_description.resources.pickup_entry import PickupModel
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_configuration import RoomRandoMode
from randovania.lib import status_update_lib
from randovania.patching.prime import all_prime_dol_patches, asset_conversion
from randovania.games.prime1.exporter.patch_data_factory import _MODEL_MAPPING


@dataclasses.dataclass(frozen=True)
class PrimeGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path
    echoes_input_path: Path
    asset_cache_path: Path
    use_echoes_models: bool
    cache_path: Path


def adjust_model_names(patch_data: dict, assets_meta: dict, use_external_assets: bool):

    model_list = []
    if use_external_assets:
        bad_models = {"prime2_MissileLauncher", "prime2_MissileExpansionPrime1"}
        model_list = list(set(assets_meta["items"]) - bad_models)

    for level in patch_data["levelData"].values():
        for room in level["rooms"].values():
            for pickup in room["pickups"]:
                model = PickupModel.from_json(pickup.pop("model"))
                if model.game == RandovaniaGame.METROID_PRIME:
                    converted_model_name = model.name
                else:
                    converted_model_name = "{}_{}".format(model.game.value, model.name)
                    if converted_model_name not in model_list:
                        converted_model_name = _MODEL_MAPPING.get((model.game, model.name), "Nothing")

                pickup['model'] = converted_model_name


class PrimeGameExporter(GameExporter):
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

    def make_room_rando_maps(self, directory: Path, base_filename: str, level_data: dict):
        def make_one_map(filepath, level_data, world_name):
            from randovania.game_description import default_database
            from randovania.game_description.world.dock_node import DockNode

            import networkx
            import numpy
            import logging

            for name in ["matplotlib", "matplotlib.font", "matplotlib.pyplot"]:
                logger = logging.getLogger(name)
                logger.setLevel(logging.CRITICAL)
                logger.disabled = True
            
            import matplotlib
            matplotlib._log.disabled = True
            from matplotlib import pyplot

            def wrap_text(text):
                return '\n'.join(wrap(text, 18))

            # make list of all edges between rooms
            room_connections = list()

            # add edges which were not shuffled
            disabled_doors = set()
            world = default_database.game_description_for(RandovaniaGame.METROID_PRIME).world_list.world_with_name(world_name)
            for area in world.areas:
                for node in area.nodes:
                    if not isinstance(node, DockNode):
                        continue

                    src_name = area.name                    
                    src_dock_num = node.extra["dock_index"]

                    if node.default_dock_weakness.name == "Permanently Locked":
                        disabled_doors.add((src_name, src_dock_num))

                    if node.extra["nonstandard"]:
                        dst_name = node.default_connection.area_identifier.area_name
                        room_connections.append((wrap_text(src_name), wrap_text(dst_name)))

            # add edges which were shuffled
            for room_name in level_data[world_name]["rooms"].keys():
                room = level_data[world_name]["rooms"][room_name]
                if "doors" not in room.keys():
                    continue
                for dock_num in room["doors"]:
                    if "destination" not in room["doors"][dock_num].keys():
                        continue

                    if (room_name, int(dock_num)) in disabled_doors:
                        continue

                    dst_room_name = room["doors"][dock_num]["destination"]["roomName"]
                    room_connections.append((wrap_text(room_name), wrap_text(dst_room_name)))

            # model this world's connections as a graph
            graph = networkx.DiGraph()
            graph.add_edges_from(room_connections)

            # render the graph to png
            pos = networkx.spring_layout(graph, k=1.2/numpy.sqrt(len(graph.nodes())), iterations=100, seed=0)
            pyplot.figure(3, figsize=(22, 22))
            networkx.draw(graph, pos=pos, node_size=800)
            networkx.draw_networkx_labels(graph, pos=pos, font_weight='bold', font_size=4)
            pyplot.savefig(filepath, bbox_inches='tight', dpi=220)

            # reset for next graph
            pyplot.clf()

        for world_name in level_data.keys():
            filepath = directory.with_name(f"{base_filename} {world_name}.png")
            make_one_map(filepath, level_data, world_name)

    def export_game(self, patch_data: dict, export_params: GameExportParams,
                    progress_update: status_update_lib.ProgressUpdateCallable) -> None:
        assert isinstance(export_params, PrimeGameExportParams)

        input_file = export_params.input_path
        output_file = export_params.output_path

        export_params.cache_path.mkdir(parents=True, exist_ok=True)
        cache_dir = os.fspath(export_params.cache_path)

        symbols = py_randomprime.symbols_for_file(input_file)

        new_config = copy.copy(patch_data)
        has_spoiler = new_config.pop("hasSpoiler")
        room_rando_mode = new_config.pop("roomRandoMode")
        new_config["inputIso"] = os.fspath(input_file)
        new_config["outputIso"] = os.fspath(output_file)
        new_config["gameConfig"]["updateHintStateReplacement"] = list(
            assembler.assemble_instructions(
                symbols["UpdateHintState__13CStateManagerFf"],
                all_prime_dol_patches.remote_execution_patch(),
                symbols=symbols)
        )
        new_config["preferences"]["cacheDir"] = cache_dir

        assets_meta = {}
        updaters = [progress_update]
        if export_params.use_echoes_models:
            updaters = status_update_lib.split_progress_update(progress_update, 2)
            assets_path = export_params.asset_cache_path
            assets_meta = asset_conversion.convert_prime2_pickups(export_params.echoes_input_path,
                                                                  assets_path, updaters[0])
            new_config["externAssetsDir"] = os.fspath(assets_path)
        else:
            asset_conversion.delete_converted_assets(export_params.asset_cache_path)

        # Replace models
        adjust_model_names(new_config, assets_meta, export_params.use_echoes_models)

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        if has_spoiler:
            output_file.with_name(f"{output_file.stem}-patcher.json").write_text(patch_as_str)
            if room_rando_mode != RoomRandoMode.NONE.value:
                self.make_room_rando_maps(output_file, f"{output_file.stem}", new_config["levelData"])

        os.environ["RUST_BACKTRACE"] = "1"

        try:
            py_randomprime.patch_iso_raw(
                patch_as_str,
                py_randomprime.ProgressNotifier(lambda percent, msg: updaters[-1](msg, percent)),
            )
        except BaseException as e:
            if isinstance(e, Exception):
                raise
            else:
                raise RuntimeError(f"randomprime panic: {e}") from e
