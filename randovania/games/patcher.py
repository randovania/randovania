from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List

from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.layout.layout_description import LayoutDescription


class Patcher(ABC):
    @property
    @abstractmethod
    def is_busy(self) -> bool:
        """
        Checks if the patcher is busy right now
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def export_can_be_aborted(self) -> bool:
        """
        Checks if patch_game can be aborted
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def uses_input_file_directly(self) -> bool:
        """
        Does this patcher uses the input file directly?
        """
        raise NotImplementedError()

    def has_internal_copy(self, game_files_path: Path) -> bool:
        """
        Checks if the internal storage has an usable copy of the game
        """
        raise NotImplementedError()

    def delete_internal_copy(self, game_files_path: Path):
        """
        Deletes any copy of the game in the internal storage.
        """
        raise NotImplementedError()

    def default_output_file(self, seed_hash: str) -> str:
        """
        Provides a output file name with the given seed hash.
        :param seed_hash:
        :return:
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def valid_input_file_types(self) -> List[str]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def valid_output_file_types(self) -> List[str]:
        raise NotImplementedError()

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: BaseCosmeticPatches) -> dict:
        """
        Creates a JSON serializable dict that can be used to patch the game.
        Intended to be ran on the server for multiworld.
        :return:
        """
        raise NotImplementedError()

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   internal_copies_path: Path, progress_update: ProgressUpdateCallable):
        """
        Invokes the necessary tools to patch the game.
        :param input_file: Vanilla copy of the game. Required if uses_input_file_directly or has_internal_copy is False.
        :param output_file: Where a modified copy of the game is placed.
        :param patch_data: Data created by create_patch_data.
        :param internal_copies_path: Path to where all internal copies are stored.
        :param progress_update: Pushes updates as slow operations are done.
        :return: None
        """
        raise NotImplementedError()
