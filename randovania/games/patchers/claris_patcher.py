import functools
import json
import shutil
from pathlib import Path
from typing import Optional, List

from randovania import get_data_path
from randovania.games.patcher import Patcher
from randovania.games.patchers import claris_randomizer, claris_patcher_file
from randovania.games.patchers.gamecube import banner_patcher, iso_packager
from randovania.interface_common import game_workdir
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.lib import status_update_lib


class ClarisPatcher(Patcher):
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

    @property
    def uses_input_file_directly(self) -> bool:
        """
        Does this patcher uses the input file directly?
        """
        return False

    def has_internal_copy(self, internal_copies_path: Path) -> bool:
        result = game_workdir.discover_game(internal_copies_path.joinpath("prime2", "contents"))
        if result is not None:
            game_id, _ = result
            if game_id.startswith("G2M"):
                return True
        return False

    def delete_internal_copy(self, internal_copies_path: Path):
        internal_copies_path = internal_copies_path.joinpath("prime2")
        if internal_copies_path.exists():
            shutil.rmtree(internal_copies_path)

    def default_output_file(self, seed_hash: str) -> str:
        return "Echoes Randomizer - {}".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return ["iso"]

    @property
    def valid_output_file_types(self) -> List[str]:
        return ["iso"]

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: EchoesCosmeticPatches):
        return claris_patcher_file.create_patcher_file(description, players_config, cosmetic_patches,
                                                       decode_randomizer_data())

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   internal_copies_path: Path, progress_update: status_update_lib.ProgressUpdateCallable):
        updaters = status_update_lib.split_progress_update(progress_update, 3)

        contents_files_path = internal_copies_path.joinpath("prime2", "contents")
        backup_files_path = internal_copies_path.joinpath("prime2", "vanilla")

        if input_file is not None:
            unpack_updaters = status_update_lib.split_progress_update(updaters[0], 2)
            self.delete_internal_copy(internal_copies_path)
            iso_packager.unpack_iso(
                iso=input_file,
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
                    updaters[0]
                )
            except FileNotFoundError:
                raise RuntimeError(
                    "Your internal copy is missing files.\nPlease press 'Delete internal copy' and select "
                    "a clean game ISO.")

        # Apply patcher
        banner_patcher.patch_game_name_and_id(
            contents_files_path,
            "Metroid Prime 2: Randomizer - {}".format(patch_data["shareable_hash"])
        )
        claris_randomizer.apply_patcher_file(
            contents_files_path,
            patch_data,
            updaters[1])

        # Pack ISO
        iso_packager.pack_iso(
            iso=output_file,
            game_files_path=contents_files_path,
            progress_update=updaters[2],
        )


@functools.lru_cache()
def decode_randomizer_data() -> dict:
    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")

    with randomizer_data_path.open() as randomizer_data_file:
        return json.load(randomizer_data_file)
