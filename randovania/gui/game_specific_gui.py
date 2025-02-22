from __future__ import annotations

import dataclasses
import itertools
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania import monitoring
from randovania.gui.lib import async_dialog
from randovania.gui.preset_settings.customize_description_tab import PresetCustomizeDescription

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game.game_enum import RandovaniaGame
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.options import Options
    from randovania.interface_common.preset_editor import PresetEditor


async def customize_cosmetic_patcher_button(
    parent: QtWidgets.QWidget,
    game: RandovaniaGame,
    options: Options,
    monitoring_label: str,
) -> None:
    """
    Creates the appropriate dialog for editing the CosmeticPatches stored in Options for the given game.
    Should not be called for games that don't have a cosmetic patches dialog.
    :return:
    """
    monitoring.metrics.incr(monitoring_label, tags={"game": game.short_name})
    per_game_options = options.options_for_game(game)

    assert game.gui.cosmetic_dialog is not None
    dialog = game.gui.cosmetic_dialog(parent, per_game_options.cosmetic_patches)
    result = await async_dialog.execute_dialog(dialog)

    if result == QtWidgets.QDialog.DialogCode.Accepted:
        with options as options_editor:
            options_editor.set_options_for_game(
                game,
                dataclasses.replace(per_game_options, cosmetic_patches=dialog.cosmetic_patches),
            )


def preset_editor_tabs_for(editor: PresetEditor, window_manager: WindowManager) -> Iterable[type[PresetTab]]:
    return itertools.chain(editor.game.gui.tab_provider(editor, window_manager), {PresetCustomizeDescription})
