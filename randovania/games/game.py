from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from random import Random
from typing import Callable, Iterable, Optional, Type

from randovania import get_file_path
from randovania.bitpacking.bitpacking import BitPackEnum

if typing.TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.base_patches_factory import BasePatchesFactory
    from randovania.generator.item_pool import PoolResults
    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.gui.game_details.game_details_tab import GameDetailsTab
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
    from randovania.patching.patcher import Patcher
    from randovania.resolver.bootstrap import Bootstrap


@dataclass(frozen=True)
class GamePresetDescriber:
    expected_items: set[str] = frozenset()
    """Items most presets will start with. Only displayed when shuffled."""

    unexpected_items: Callable[[MajorItemsConfiguration], set[str]] = lambda config: frozenset()
    """Items not expected to be shuffled.
    Includes `expected_items` as well as configurable items such as progressive items."""

    format_params: Optional[Callable[[BaseConfiguration], dict[str, list[str]]]] = None
    """Function providing any game-specific information to display in presets such as the goal."""


@dataclass(frozen=True)
class GameLayout:
    configuration: Type[BaseConfiguration]
    """Logic and gameplay settings such as elevator shuffling."""

    cosmetic_patches: Type[BaseCosmeticPatches]
    """Cosmetic settings such as item icons on maps."""

    preset_describer: GamePresetDescriber = GamePresetDescriber()
    """(Optional) Contains game-specific preset descriptions, used by the preset screen and Discord bot."""

    get_ingame_hash: Callable[[bytes], Optional[str]] = lambda h: None
    """(Optional) Takes a layout hash bytes and produces a string representing how the game will represent the hash in-game. Only override if the game cannot display arbitrary text on the title screen."""


@dataclass(frozen=True)
class GameGui:
    tab_provider: Callable[[PresetEditor, WindowManager], Iterable[PresetTab]]
    """Provides a set of tabs for configuring the game's logic and gameplay settings."""

    cosmetic_dialog: Type[BaseCosmeticPatchesDialog]
    """Dialog box for editing the game's cosmetic settings."""

    input_file_text: Optional[tuple[str, str, str]] = None
    """Three strings used to describe the input file for the game."""

    progressive_item_gui_tuples: Iterable[tuple[str, tuple[str, ...]]] = frozenset()
    """(Optional) A list of tuples mapping a progressive item's long name to a tuple of item long names replaced by the progressive item."""

    spoiler_visualizer: tuple[Type[GameDetailsTab], ...] = tuple()


@dataclass(frozen=True)
class GameGenerator:
    item_pool_creator: Callable[[PoolResults, BaseConfiguration, ResourceDatabase, GamePatches, Random], None]
    """Extends the base item pools with any specific item pools such as Artifacts."""

    bootstrap: Bootstrap
    """Modifies the resource database and starting resources before generation."""

    base_patches_factory: BasePatchesFactory
    """Creates base patches, such as elevator or configurable node assignments."""


@dataclass(frozen=True)
class GameData:
    """Contains all game-specific behavior as required by Randovania."""

    short_name: str
    """Short name, used throughout the GUI where space is limited."""

    long_name: str
    """Full name, used throughout the GUI where space is not an issue."""

    experimental: bool
    """Controls whether the "Experimental Games" setting must be enabled in order to see the game in Randovania.
    Default to True until given approval."""

    presets: Iterable[dict[str, str]]
    """List of at least one dict mapping the key "path" to a path to the given preset."""

    faq: Iterable[tuple[str, str]]
    """List of question to markdown-formatted response of FAQ entries."""

    layout: GameLayout
    """Contains game-specific settings available for presets."""

    gui: Callable[[], GameGui]
    """Contains game-specific GUI windows."""

    generator: GameGenerator
    """Contains game-specific generation data."""

    patcher: Optional[Patcher] = None
    """(Optional) The class responsible for patching a game and building a new .iso."""

    permalink_reference_preset: Optional[str] = None
    """(Optional) Name of the preset used as reference to encode permalinks of this game.
    If unset, the first of the list is used."""


class RandovaniaGame(BitPackEnum, Enum):
    METROID_PRIME = "prime1"
    METROID_PRIME_ECHOES = "prime2"
    METROID_PRIME_CORRUPTION = "prime3"
    SUPER_METROID = "super_metroid"
    METROID_DREAD = "dread"
    CAVE_STORY = "cave_story"
    DELTARUNE = "deltarune"

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
        elif self == RandovaniaGame.CAVE_STORY:
            import randovania.games.cave_story.game_data as game_module
        elif self == RandovaniaGame.DELTARUNE:
            import randovania.games.deltarune.game_data as game_module
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
