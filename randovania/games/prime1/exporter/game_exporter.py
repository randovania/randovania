import copy
import dataclasses
import json
import os
from pathlib import Path

import py_randomprime

from randovania.dol_patching import assembler
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import status_update_lib
from randovania.patching.prime import all_prime_dol_patches


@dataclasses.dataclass(frozen=True)
class PrimeGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path
    cache_path: Path


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

        export_params.cache_path.mkdir(parents=True, exist_ok=True)
        cache_dir = os.fspath(export_params.cache_path)

        symbols = py_randomprime.symbols_for_file(input_file)

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
        new_config["preferences"]["cacheDir"] = cache_dir

        patch_as_str = json.dumps(new_config, indent=4, separators=(',', ': '))
        if has_spoiler:
            output_file.with_name(f"{output_file.stem}-patcher.json").write_text(patch_as_str)

        os.environ["RUST_BACKTRACE"] = "1"

        try:
            py_randomprime.patch_iso_raw(
                patch_as_str,
                py_randomprime.ProgressNotifier(lambda percent, msg: progress_update(msg, percent)),
            )
        except BaseException as e:
            if isinstance(e, Exception):
                raise
            else:
                raise RuntimeError(f"randomprime panic: {e}") from e
