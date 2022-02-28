from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from pathlib import Path
from random import Random
from typing import Callable, Iterable, Optional, Type

import randovania
from randovania.bitpacking.bitpacking import BitPackEnum

if typing.TYPE_CHECKING:
    from PySide2 import QtWidgets

    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import BasePatchDataFactory
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.base_patches_factory import BasePatchesFactory
    from randovania.generator.hint_distributor import HintDistributor
    from randovania.generator.item_pool import PoolResults
    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.gui.dialog.game_export_dialog import GameExportDialog
    from randovania.gui.game_details.game_details_tab import GameDetailsTab
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.options import PerGameOptions
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.layout.preset_describer import GamePresetDescriber
    from randovania.resolver.bootstrap import Bootstrap


@dataclass(frozen=True)
class GameLayout:
    configuration: Type[BaseConfiguration]
    """Logic and gameplay settings such as elevator shuffling."""

    cosmetic_patches: Type[BaseCosmeticPatches]
    """Cosmetic settings such as item icons on maps."""

    preset_describer: GamePresetDescriber
    """Contains game-specific preset descriptions, used by the preset screen and Discord bot."""

    get_ingame_hash: Callable[[bytes], Optional[str]] = lambda h: None
    """(Optional) Takes a layout hash bytes and produces a string representing how the game 
    will represent the hash in-game. Only override if the game cannot display arbitrary text on the title screen."""


@dataclass(frozen=True)
class GameGui:
    tab_provider: Callable[[PresetEditor, WindowManager], Iterable[PresetTab]]
    """Provides a set of tabs for configuring the game's logic and gameplay settings."""

    cosmetic_dialog: Type[BaseCosmeticPatchesDialog]
    """Dialog box for editing the game's cosmetic settings."""

    export_dialog: Type[GameExportDialog]
    """Dialog box for asking the user for whatever is needed to modify the game, like input and output paths."""

    progressive_item_gui_tuples: Iterable[tuple[str, tuple[str, ...]]] = frozenset()
    """(Optional) A list of tuples mapping a progressive item's long name to a tuple of item long
    names replaced by the progressive item."""

    spoiler_visualizer: tuple[Type[GameDetailsTab], ...] = tuple()
    """Tuple of specializations of GameDetailsTab for providing extra details when visualizing a LayoutDescription."""

    help_widget: Optional[Callable[[], QtWidgets.QWidget]] = None
    """(Optional) Provides a widget used by the main window to display help, faq and other details about this game."""


@dataclass(frozen=True)
class GameGenerator:
    item_pool_creator: Callable[[PoolResults, BaseConfiguration, ResourceDatabase, GamePatches, Random], None]
    """Extends the base item pools with any specific item pools such as Artifacts."""

    bootstrap: Bootstrap
    """Modifies the resource database and starting resources before generation."""

    base_patches_factory: BasePatchesFactory
    """Creates base patches, such as elevator or configurable node assignments."""

    hint_distributor: Optional[HintDistributor] = None
    """(Optional) """


class DevelopmentState(Enum):
    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    DEVELOPMENT = "development"

    @property
    def is_stable(self):
        return self == DevelopmentState.STABLE

    def can_view(self, allow_experimental: bool) -> bool:
        if self.is_stable:
            return True

        if not allow_experimental:
            return False

        return self == DevelopmentState.EXPERIMENTAL or randovania.is_dev_version()


@dataclass(frozen=True)
class GameData:
    """Contains all game-specific behavior as required by Randovania."""

    short_name: str
    """Short name, used throughout the GUI where space is limited."""

    long_name: str
    """Full name, used throughout the GUI where space is not an issue."""

    development_state: DevelopmentState
    """Controls how mature the game is considered to be. Various part of the UI display different games depending on
    the development state.
    Games start in DEVELOPMENT, change to EXPERIMENTAL when somewhat usable and move to STABLE when given approval."""

    presets: Iterable[dict[str, str]]
    """List of at least one dict mapping the key "path" to a path to the given preset."""

    faq: Iterable[tuple[str, str]]
    """List of question to markdown-formatted response of FAQ entries."""

    layout: GameLayout
    """Contains game-specific settings available for presets."""

    options: Callable[[], Type[PerGameOptions]]
    """Contains game-specific persisted values."""

    gui: Callable[[], GameGui]
    """Contains game-specific GUI windows."""

    generator: Callable[[], GameGenerator]
    """Contains game-specific generation data."""

    patch_data_factory: Callable[[], Type[BasePatchDataFactory]]

    exporter: Callable[[], GameExporter]
    """Capable of exporting everything needed to play the randomized game."""

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
    BLANK = "blank"

    @property
    def data(self) -> GameData:
        if self == RandovaniaGame.BLANK:
            import randovania.games.blank.game_data as game_module
        elif self == RandovaniaGame.METROID_PRIME:
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
        else:
            raise ValueError(f"Missing import for game: {self.value}")
        return game_module.game_data

    @property
    def data_path(self) -> Path:
        return randovania.get_file_path().joinpath("games", self.value)

    @property
    def short_name(self) -> str:
        return self.data.short_name

    @property
    def long_name(self) -> str:
        return self.data.long_name

    @classmethod
    def all_games(cls) -> Iterable[RandovaniaGame]:
        yield from cls

    @classmethod
    def sorted_all_games(cls) -> list[RandovaniaGame]:
        return sorted(cls.all_games(), key=lambda g: g.long_name)

    @cached_property
    def options(self) -> Type[PerGameOptions]:
        return self.data.options()

    @cached_property
    def gui(self) -> GameGui:
        return self.data.gui()

    @cached_property
    def generator(self) -> GameGenerator:
        return self.data.generator()

    @cached_property
    def patch_data_factory(self) -> Type[BasePatchDataFactory]:
        return self.data.patch_data_factory()

    @cached_property
    def exporter(self) -> GameExporter:
        return self.data.exporter()
