from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import importlib
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional, Set, Type, TYPE_CHECKING
from randovania import get_file_path

from randovania.bitpacking.bitpacking import BitPackEnum

if TYPE_CHECKING:
    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.gui.lib.preset_describer import _format_params_base
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.item_pool import PoolResults
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.base.major_items_configuration import MajorItemsConfiguration

@dataclass(frozen=True)
class GameLayout:
    configuration: Optional[Type[BaseConfiguration]] = None
    cosmetic_patches: Optional[Type[BaseCosmeticPatches]] = None

@dataclass(frozen=True)
class GamePresetDescriber:
    expected_items: Set[str] = frozenset()
    unexpected_items: Callable[[MajorItemsConfiguration], Set[str]] = lambda config: frozenset()
    format_params: Optional[Callable[[BaseConfiguration], None]] = None

def no_tab_provider(preset, window):
    raise NotImplementedError()

@dataclass(frozen=True)
class GameGui:
    tab_provider: Callable[[PresetEditor, WindowManager], Iterable[PresetTab]] = no_tab_provider
    cosmetic_dialog: Optional[Type[BaseCosmeticPatchesDialog]] = None
    preset_describer: GamePresetDescriber = GamePresetDescriber()

def no_item_pool_creator(results, configuration, db):
    pass

@dataclass(frozen=True)
class GameGenerator:
    item_pool_creator: Callable[[PoolResults, BaseConfiguration, ResourceDatabase], None] = no_tab_provider

@dataclass(frozen=True)
class GameData:
    """Contains all game-specific behavior as required by Randovania."""

    short_name: str
    """Short name, used throughout the GUI where space is limited."""

    long_name: str
    """Full name, used throughout the GUI where space is not an issue."""

    experimental: bool
    """Controls whether the "Experimental Games" setting must be enabled in order to see the game in Randovania. Default to True until given approval."""

    presets: Iterable[Dict[str, str]]
    """List of dicts mapping the key "path" to a path to the given preset."""

    layout: GameLayout = GameLayout()
    """"""

    gui: GameGui = GameGui()
    """"""

    generator: GameGenerator = GameGenerator()
    """"""


class RandovaniaGame(BitPackEnum, Enum):
    METROID_PRIME = "prime1"
    METROID_PRIME_ECHOES = "prime2"
    METROID_PRIME_CORRUPTION = "prime3"
    SUPER_METROID = "super_metroid"

    @property
    def data(self) -> GameData:
        return importlib.import_module('.'+self.value, "randovania.games").game_data
    
    @property
    def data_path(self) -> Path:
        return get_file_path().joinpath("games", self.value)
