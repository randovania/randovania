import copy
import dataclasses
import json
import os
from pathlib import Path
from textwrap import wrap

import py_randomprime

from randovania.dol_patching import assembler
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.game_description.resources.pickup_entry import PickupModel
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_configuration import RoomRandoMode
from randovania.lib import status_update_lib
from randovania.patching.patchers.gamecube import iso_packager
from randovania.patching.prime import all_prime_dol_patches, asset_conversion
from randovania.games.prime1.exporter.patch_data_factory import _MODEL_MAPPING


@dataclasses.dataclass(frozen=True)
class PrimeGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path
    echoes_input_path: Path
    echoes_contents_path: Path
    echoes_backup_path: Path
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

        def make_one_map(filepath, world):
            room_connections = list()
            for room_name in world["rooms"].keys():
                room = world["rooms"][room_name]
                if "doors" not in room.keys():
                    continue
                for dock_num in room["doors"]:
                    if "destination" not in room["doors"][dock_num].keys():
                        continue

                    dst_room_name = room["doors"][dock_num]["destination"]["roomName"]
                    room_name = '\n'.join(wrap(room_name, 18))
                    dst_room_name = '\n'.join(wrap(dst_room_name, 18))
                    room_connections.append((room_name, dst_room_name))

            import networkx
            from matplotlib import pyplot
            import numpy

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
            make_one_map(filepath, level_data[world_name])

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
                [
                    *all_prime_dol_patches.remote_execution_patch_start(),
                    *all_prime_dol_patches.remote_execution_patch_end(),
                ],
                symbols=symbols)
        )
        new_config["preferences"]["cacheDir"] = cache_dir

        assets_meta = {}
        updaters = [progress_update]
        if export_params.use_echoes_models:
            assets_path = export_params.asset_cache_path
            asset_conversion_progress = None
            if asset_conversion.get_asset_cache_version(assets_path) != asset_conversion.ECHOES_MODELS_VERSION:
                updaters = status_update_lib.split_progress_update(progress_update, 3)
                asset_conversion_progress = updaters[1]
                from randovania.games.prime2.exporter.game_exporter import extract_and_backup_iso
                extract_and_backup_iso(export_params.echoes_input_path, export_params.echoes_contents_path,
                                       export_params.echoes_backup_path, updaters[0])
            assets_meta = asset_conversion.convert_prime2_pickups(assets_path, asset_conversion_progress)
            new_config["externAssetsDir"] = os.fspath(assets_path)

        # Replace models
        adjust_model_names(new_config, assets_meta, export_params.use_echoes_models)

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        if has_spoiler:
            output_file.with_name(f"{output_file.stem}-patcher.json").write_text(patch_as_str)
            if room_rando_mode != RoomRandoMode.NONE:
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
