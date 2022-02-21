import copy
import dataclasses
import json
import os
import shutil
from pathlib import Path

import py_randomprime

from randovania.dol_patching import assembler
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import Options
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
    use_echoes_models: bool


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

    def export_game(self, patch_data: dict, export_params: GameExportParams,
                    progress_update: status_update_lib.ProgressUpdateCallable) -> None:
        assert isinstance(export_params, PrimeGameExportParams)

        input_file = export_params.input_path
        output_file = export_params.output_path

        symbols = py_randomprime.symbols_for_file(input_file)

        use_external_assets = export_params.use_echoes_models

        updaters = status_update_lib.split_progress_update(progress_update, 3)

        #Deal with echoes
        if export_params.use_echoes_models and export_params.echoes_input_path is not None:
            echoes_contents_path = export_params.echoes_contents_path
            shutil.rmtree(echoes_contents_path, ignore_errors=True)
            iso_packager.unpack_iso(
                iso=export_params.echoes_input_path,
                game_files_path=echoes_contents_path,
                progress_update=updaters[0],
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
            assets_path = Options.with_default_data_dir().internal_copies_path.joinpath(
                RandovaniaGame.METROID_PRIME.value,
                f"{RandovaniaGame.METROID_PRIME_ECHOES.value}_models")
            assets_meta = asset_conversion.convert_prime2_pickups(assets_path, updaters[1])
            new_config["externAssetsDir"] = os.fspath(assets_path)

        # Replace models
        for level in new_config["levelData"].values():
            for room in level["rooms"].values():
                for pickup in room["pickups"]:
                    model = pickup.pop("model")
                    if model["game"] == RandovaniaGame.METROID_PRIME.value:
                        pickup['model'] = model["name"]
                    elif model["game"] == RandovaniaGame.METROID_PRIME_ECHOES.value:
                        converted_model_name = "{}_{}".format(model["game"], model["name"])
                        if assets_meta is not None and use_external_assets:
                            if converted_model_name in assets_meta["items"]:
                                pickup['model'] = converted_model_name
                            else:  # This model wasn't converted
                                pickup['model'] = _MODEL_MAPPING.get((model["game"], model["name"]), "Nothing")
                        else:  # Not using external assets
                            pickup['model'] = _MODEL_MAPPING.get((model["game"], model["name"]), "Nothing")
                    else:  # Not Prime or Echoes item
                        pickup['model'] = _MODEL_MAPPING.get((model["game"], model["name"]), "Nothing")

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
