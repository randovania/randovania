from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional, Set, Type, TYPE_CHECKING
from randovania import get_file_path

from randovania.bitpacking.bitpacking import BitPackEnum

if TYPE_CHECKING:
    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.item_pool import PoolResults
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
    from randovania.patching.patcher import Patcher


@dataclass(frozen=True)
class GamePresetDescriber:
    expected_items: Set[str] = frozenset()
    """Items most presets will start with. Only displayed when shuffled."""

    unexpected_items: Callable[[MajorItemsConfiguration], Set[str]] = lambda config: frozenset()
    """Items not expected to be shuffled. Includes `expected_items` as well as configurable items such as progressive items."""

    format_params: Optional[Callable[[BaseConfiguration], None]] = None
    """Function providing any game-specific information to display in presets such as the goal."""


@dataclass(frozen=True)
class GameLayout:
    configuration: Type[BaseConfiguration]
    """Logic and gameplay settings such as elevator shuffling."""

    cosmetic_patches: Type[BaseCosmeticPatches]
    """Cosmetic settings such as item icons on maps."""

    preset_describer: GamePresetDescriber = GamePresetDescriber()
    """(Optional) Contains game-specific preset descriptions, used by the preset screen and Discord bot."""


@dataclass(frozen=True)
class GameGui:
    tab_provider: Callable[[PresetEditor, WindowManager], Iterable[PresetTab]]
    """Provides a set of tabs for configuring the game's logic and gameplay settings."""

    cosmetic_dialog: Type[BaseCosmeticPatchesDialog]
    """Dialog box for editing the game's cosmetic settings."""


@dataclass(frozen=True)
class GameGenerator:
    item_pool_creator: Callable[[PoolResults, BaseConfiguration, ResourceDatabase], None]
    """Extends the base item pools with any specific item pools such as Artifacts."""


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
    """List of at least one dict mapping the key "path" to a path to the given preset."""

    layout: GameLayout
    """Contains game-specific settings available for presets."""

    gui: Callable[[], GameGui]
    """Contains game-specific GUI windows."""

    generator: GameGenerator
    """Contains game-specific generation data."""

    patcher: Optional[Patcher] = None
    """(Optional) The class responsible for patching a game and building a new .iso."""


class RandovaniaGame(BitPackEnum, Enum):
    METROID_PRIME = "prime1"
    METROID_PRIME_ECHOES = "prime2"
    METROID_PRIME_CORRUPTION = "prime3"
    SUPER_METROID = "super_metroid"
    METROID_DREAD = "dread"

    @property
    def data(self) -> GameData:
        if self == RandovaniaGame.METROID_PRIME:
            import randovania.games.prime1.game_data as game_module
        elif self == RandovaniaGame.METROID_PRIME_ECHOES:
            import randovania.games.prime2.game_data as game_module
        elif self == RandovaniaGame.METROID_PRIME_CORRUPTION:
            import randovania.games.prime3.game_data as game_module
        elif self == RandovaniaGame.SUPER_METROID:
            import randovania.games.super_metroid.game_data as game_module
        elif self == RandovaniaGame.METROID_DREAD:
            import randovania.games.dread.game_data as game_module
        else:
            raise ValueError(f"Missing import for game: {self.value}")
        return game_module.game_data

    @property
    def data_path(self) -> Path:
        return get_file_path().joinpath("games", self.value)

    @property
    def short_name(self) -> str:
        return self.data.short_name

    @property
    def long_name(self) -> str:
        return self.data.long_name
