from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.interface_common.status_update_lib import ProgressUpdateCallable
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
    def uses_input_file_directly(self) -> bool:
        """
        Does this patcher uses the input file directly?
        """
        raise NotImplementedError()

    def create_patch_data(self, description: LayoutDescription, players_config: PlayersConfiguration,
                          cosmetic_patches: CosmeticPatches) -> dict:
        raise NotImplementedError()

    def patch_game(self, input_file: Optional[Path], output_file: Path, patch_data: dict,
                   progress_update: ProgressUpdateCallable):
        raise NotImplementedError()
