import copy
import dataclasses
import functools
import shutil
from pathlib import Path

import mp2hudcolor
from ppc_asm import dol_file
from retro_data_structures.asset_manager import PathFileProvider

from open_prime_rando.dol_patching.echoes import dol_patcher
from randovania import get_data_path
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.games.prime2.exporter.patch_data_factory import adjust_model_name
from randovania.games.prime2.patcher import claris_randomizer
from randovania.lib import status_update_lib, json_lib
from randovania.patching.patchers.gamecube import banner_patcher, iso_packager


@dataclasses.dataclass(frozen=True)
class EchoesGameExportParams(GameExportParams):
    input_path: Path | None
    output_path: Path
    contents_files_path: Path
    asset_cache_path: Path
    backup_files_path: Path
    prime_path: Path | None
    use_prime_models: bool


class EchoesGameExporter(GameExporter):
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
        return True

    def _before_export(self):
        assert not self._busy
        self._busy = True

    def _after_export(self):
        self._busy = False

    def _do_export_game(self, patch_data: dict, export_params: GameExportParams,
                        progress_update: status_update_lib.ProgressUpdateCallable):
        assert isinstance(export_params, EchoesGameExportParams)
        new_patcher = patch_data.pop("new_patcher", None)

        # restore backups
        # convert prime models
        # claris patcher
        # open-prime-rando
        # menu mod
        # nod
        num_updaters = 3
        if new_patcher is not None:
            num_updaters += 1
        if patch_data["menu_mod"]:
            num_updaters += 1
        if export_params.use_prime_models:
            num_updaters += 1
        updaters = status_update_lib.split_progress_update(progress_update, num_updaters)

        contents_files_path = export_params.contents_files_path
        backup_files_path = export_params.backup_files_path

        backups_update = updaters.pop(0)
        if export_params.input_path is not None:
            unpack_updaters = status_update_lib.split_progress_update(backups_update, 2)
            shutil.rmtree(contents_files_path, ignore_errors=True)
            shutil.rmtree(backup_files_path, ignore_errors=True)
            iso_packager.unpack_iso(
                iso=export_params.input_path,
                game_files_path=contents_files_path,
                progress_update=unpack_updaters[0],
            )
            claris_randomizer.create_pak_backups(
                contents_files_path,
                backup_files_path,
                unpack_updaters[1]
            )
        else:
            try:
                claris_randomizer.restore_pak_backups(
                    contents_files_path,
                    backup_files_path,
                    backups_update
                )
            except FileNotFoundError:
                raise RuntimeError(
                    "Your internal copy is missing files.\nPlease press 'Delete internal copy' and select "
                    "a clean game ISO.")

        # Save patcher data
        json_lib.write_path(
            contents_files_path.joinpath("files", "patcher_data.json"),
            patch_data,
        )

        # Apply patcher
        banner_patcher.patch_game_name_and_id(
            contents_files_path,
            patch_data["banner_name"],
            patch_data["publisher_id"]
        )
        randomizer_data = copy.deepcopy(decode_randomizer_data())

        if export_params.use_prime_models:
            convert_update = updaters.pop(0)
            from randovania.patching.prime import asset_conversion
            assets_path = export_params.asset_cache_path
            asset_conversion.convert_prime1_pickups(
                export_params.prime_path, contents_files_path, assets_path,
                patch_data, randomizer_data, convert_update,
            )

        # Claris Rando
        claris_update = updaters.pop(0)
        adjust_model_name(patch_data, randomizer_data)

        claris_randomizer.apply_patcher_file(
            contents_files_path,
            patch_data,
            randomizer_data,
            claris_update)

        dol_patcher.apply_patches(
            dol_file.DolFile(contents_files_path.joinpath("sys/main.dol")),
            dol_patcher.EchoesDolPatchesData.from_json(patch_data["dol_patches"]),
        )

        # New Patcher
        if new_patcher is not None:
            opr_update = updaters.pop(0)
            import open_prime_rando.echoes_patcher
            open_prime_rando.echoes_patcher.patch_paks(
                PathFileProvider(contents_files_path),
                contents_files_path,
                new_patcher,
                opr_update
            )

        # Menu Mod
        if patch_data["menu_mod"]:
            menumod_update = updaters.pop(0)
            claris_randomizer.add_menu_mod_to_files(
                contents_files_path,
                menumod_update
            )

        # Change the color of the hud
        hud_color = patch_data["specific_patches"]["hud_color"]
        if hud_color:
            hud_color = [
                hud_color[0] / 255,
                hud_color[1] / 255,
                hud_color[2] / 255,
            ]
            ntwk_file = str(contents_files_path.joinpath("files", "Standard.ntwk"))
            mp2hudcolor.mp2hudcolor_c(ntwk_file, ntwk_file, hud_color[0], hud_color[1], hud_color[2])  # RGB 0.0-1.0

        # Pack ISO
        nod_update = updaters.pop(0)
        iso_packager.pack_iso(
            iso=export_params.output_path,
            game_files_path=contents_files_path,
            progress_update=nod_update,
        )


@functools.lru_cache
def decode_randomizer_data() -> dict:
    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")
    return json_lib.read_path(randomizer_data_path)
