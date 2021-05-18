import functools
import json
from pathlib import Path
from typing import Optional

from randovania import get_data_path
from randovania.games.patcher import Patcher
from randovania.games.patchers import claris_randomizer, claris_patcher_file
from randovania.games.patchers.gamecube import banner_patcher, iso_packager
from randovania.interface_common import status_update_lib, simplified_patcher
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.options import Options
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_description import LayoutDescription


class ClarisPatcher(Patcher):
    _busy: bool = False

    def __init__(self, options: Options):
        self.options = options

    @property
    def is_busy(self) -> bool:
        """
        Checks if the patcher is busy right now
        """
        return self._busy

    @property
    def uses_input_file_directly(self) -> bool:
        """
        Does this patcher uses the input file directly?
        """
        return False

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: CosmeticPatches):
        return claris_patcher_file.create_patcher_file(description, players_config, cosmetic_patches)

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   progress_update: ProgressUpdateCallable):
        num_updaters = 2
        if input_file is not None:
            num_updaters += 1
        updaters = status_update_lib.split_progress_update(progress_update, num_updaters)

        game_files_path = self.options.game_files_path
        backup_files_path = self.options.backup_files_path

        if input_file is not None:
            simplified_patcher.delete_files_location(self.options)
            iso_packager.unpack_iso(
                iso=input_file,
                game_files_path=game_files_path,
                progress_update=updaters[0],
            )

        # Apply patcher
        banner_patcher.patch_game_name_and_id(
            game_files_path,
            "Metroid Prime 2: Randomizer - {}".format(patch_data["shareable_hash"])
        )
        claris_randomizer.apply_patcher_file(
            game_files_path,
            backup_files_path,
            patch_data,
            updaters[-2])

        # Pack ISO
        iso_packager.pack_iso(
            iso=output_file,
            game_files_path=game_files_path,
            progress_update=updaters[-1],
        )


@functools.lru_cache()
def decode_randomizer_data() -> dict:
    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")

    with randomizer_data_path.open() as randomizer_data_file:
        return json.load(randomizer_data_file)
