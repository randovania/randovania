from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6 import QtWidgets

    from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.gui.preset_settings.preset_tab import PresetTab
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


def create_dialog_for_cosmetic_patches(
    parent: QtWidgets.QWidget,
    initial_patches: BaseCosmeticPatches,
) -> BaseCosmeticPatchesDialog:
    game = initial_patches.game()
    dialog_class = game.gui.cosmetic_dialog
    return dialog_class(parent, initial_patches)


def preset_editor_tabs_for(editor: PresetEditor, window_manager: WindowManager) -> Iterable[type[PresetTab]]:
    return editor.game.gui.tab_provider(editor, window_manager)
