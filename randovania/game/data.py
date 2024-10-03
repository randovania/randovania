from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from randovania.game.web_info import GameWebInfo

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.game.development_state import DevelopmentState
    from randovania.game.generator import GameGenerator
    from randovania.game.gui import GameGui
    from randovania.game.layout import GameLayout
    from randovania.game_description.game_description import GameDescription
    from randovania.interface_common.options import PerGameOptions


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

    hash_words: list[str]
    """Contains a list of hash words, which are used as a human readable way to identify generated games"""

    options: Callable[[], type[PerGameOptions]]
    """Contains game-specific persisted values."""

    gui: Callable[[], GameGui]
    """Contains game-specific GUI windows."""

    generator: Callable[[], GameGenerator]
    """Contains game-specific generation data."""

    patch_data_factory: Callable[[], type[PatchDataFactory]]

    exporter: Callable[[], GameExporter]
    """Capable of exporting everything needed to play the randomized game."""

    defaults_available_in_game_sessions: bool = False
    """If this game is allowed by default in online game sessions."""

    permalink_reference_preset: str | None = None
    """(Optional) Name of the preset used as reference to encode permalinks of this game.
    If unset, the first of the list is used."""

    multiple_start_nodes_per_area: bool = False
    """If this game allows multiple start nodes per area."""

    web_info: GameWebInfo = GameWebInfo()
    """Contains a handful of fields displayed primarily on the website."""

    logic_db_integrity: Callable[[GameDescription], Iterator[str]] = lambda game: iter(())
    """A function checking for game specific database integrity errors."""
