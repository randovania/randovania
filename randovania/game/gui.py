from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.gui.dialog.game_export_dialog import GameExportDialog
    from randovania.gui.game_details.game_details_tab import GameDetailsTab
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.gui.widgets.base_game_tab_widget import BaseGameTabWidget
    from randovania.interface_common.preset_editor import PresetEditor

"""Type alias for progressive items"""
ProgressiveItemTuples = Iterable[tuple[str, tuple[str, ...]]]


@dataclass(frozen=True)
class GameGui:
    game_tab: type[BaseGameTabWidget]
    """Provides a widget used by the main window to display help, faq and other details about this game."""

    tab_provider: Callable[[PresetEditor, WindowManager], Iterable[type[PresetTab]]]
    """Provides a set of tabs for configuring the game's logic and gameplay settings."""

    cosmetic_dialog: type[BaseCosmeticPatchesDialog] | None
    """Dialog box for editing the game's cosmetic settings."""

    export_dialog: type[GameExportDialog]
    """Dialog box for asking the user for whatever is needed to modify the game, like input and output paths."""

    progressive_item_gui_tuples: ProgressiveItemTuples = frozenset()
    """(Optional) A list of tuples mapping a progressive item's long name to a tuple of item long
    names replaced by the progressive item."""

    spoiler_visualizer: tuple[type[GameDetailsTab], ...] = ()
    """Tuple of specializations of GameDetailsTab for providing extra details when visualizing a LayoutDescription."""
