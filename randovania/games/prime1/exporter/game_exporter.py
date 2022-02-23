import copy
import dataclasses
import json
import os
import shutil
from pathlib import Path

import py_randomprime

from randovania.dol_patching import assembler
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.game_description.resources.pickup_entry import PickupModel
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import Options
from randovania.lib import status_update_lib
from randovania.patching.patchers.gamecube import iso_packager
from randovania.patching.prime import all_prime_dol_patches, asset_conversion
from randovania.games.prime1.exporter.patch_data_factory import _MODEL_MAPPING, _STARTING_ITEM_NAME_TO_INDEX


@dataclasses.dataclass(frozen=True)
class PrimeGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path
    echoes_input_path: Path
    echoes_contents_path: Path
    echoes_backup_path: Path
    use_echoes_models: bool


def adjust_model_names(patch_data: dict, assets_meta: dict, use_external_assets: bool):

    bad_models = ["prime2_MissileLauncher", "prime2_MissileExpansionPrime1"]
    if use_external_assets:
        model_list = [str(i) for i in assets_meta["items"].keys()]
        for m in bad_models:
            if m in model_list:
                model_list.remove(m)
    else:
        model_list = []

    for level in patch_data["levelData"].values():
        for room in level["rooms"].values():
            for pickup in room["pickups"]:
                model = PickupModel.from_json(pickup.pop("model"))
                if model.game == RandovaniaGame.METROID_PRIME:
                    converted_model_name = model.name
                else:
                    converted_model_name = "{}_{}".format(model.game.value, model.name)

                if converted_model_name not in model_list and model.game != RandovaniaGame.METROID_PRIME:
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

    def export_game(self, patch_data: dict, export_params: GameExportParams, options: Options,
                    progress_update: status_update_lib.ProgressUpdateCallable) -> None:
        assert isinstance(export_params, PrimeGameExportParams)

        input_file = export_params.input_path
        output_file = export_params.output_path

        symbols = py_randomprime.symbols_for_file(input_file)

        use_external_assets = export_params.use_echoes_models

        updaters = status_update_lib.split_progress_update(progress_update, 3)

        # Deal with echoes
        if export_params.use_echoes_models and export_params.echoes_input_path is not None:
            unpack_updaters = status_update_lib.split_progress_update(updaters[0], 2)
            echoes_contents_path = export_params.echoes_contents_path
            echoes_backup_path = export_params.echoes_backup_path
            shutil.rmtree(echoes_contents_path, ignore_errors=True)
            shutil.rmtree(echoes_backup_path, ignore_errors=True)
            iso_packager.unpack_iso(
                iso=export_params.echoes_input_path,
                game_files_path=echoes_contents_path,
                progress_update=unpack_updaters[0],
            )

            from randovania.games.prime2.patcher import claris_randomizer
            claris_randomizer.create_pak_backups(
                echoes_contents_path,
                echoes_backup_path,
                unpack_updaters[1]
            )

        new_config = copy.copy(patch_data)
        has_spoiler = new_config.pop("hasSpoiler")
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

        if use_external_assets:
            assets_path = options.internal_copies_path.joinpath(
                RandovaniaGame.METROID_PRIME.value,
                f"{RandovaniaGame.METROID_PRIME_ECHOES.value}_models")
            assets_meta = asset_conversion.convert_prime2_pickups(assets_path, updaters[1])
            new_config["externAssetsDir"] = os.fspath(assets_path)
        else:
            assets_meta = {}

        # Replace models
        adjust_model_names(new_config, assets_meta, use_external_assets)

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        if has_spoiler:
            output_file.with_name(f"{output_file.stem}-patcher.json").write_text(patch_as_str)

        os.environ["RUST_BACKTRACE"] = "1"

        try:
            py_randomprime.patch_iso_raw(
                patch_as_str,
                py_randomprime.ProgressNotifier(lambda percent, msg: updaters[2](msg, percent)),
            )
        except BaseException as e:
            if isinstance(e, Exception):
                raise
            else:
                raise RuntimeError(f"randomprime panic: {e}") from e
