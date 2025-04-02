from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.gui.preset_settings.hints_tab import PresetHints
from randovania.interface_common.preset_editor import PresetEditor

if TYPE_CHECKING:
    from randovania.interface_common.preset_manager import PresetManager


@pytest.fixture(
    params=[
        (RandovaniaGame.METROID_PRIME, False, False, True),
        (RandovaniaGame.METROID_PRIME_ECHOES, True, True, True),
        (RandovaniaGame.CAVE_STORY, True, True, False),
    ]
)
def hints_tab_with_game(preset_manager, request) -> tuple[PresetHints, bool, bool, bool]:
    (game, has_random_hints, has_specific_location_hints, has_specific_pickup_hints) = request.param
    return (
        _hints_tab_for_game(preset_manager, game),
        has_random_hints,
        has_specific_location_hints,
        has_specific_pickup_hints,
    )


def _hints_tab_for_game(preset_manager: PresetManager, game: RandovaniaGame) -> PresetHints:
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    return PresetHints(editor, default_database.game_description_for(game), MagicMock())


@pytest.mark.parametrize("enable_random_hints", [True, False])
def test_on_preset_changed(enable_random_hints: bool, skip_qtbot, hints_tab_with_game):
    # Setup
    (hints_tab, has_random_hints, has_specific_location_hints, has_specific_pickup_hints) = hints_tab_with_game

    parent = QtWidgets.QWidget()
    hints_tab.setParent(parent)
    skip_qtbot.addWidget(parent)

    with hints_tab._editor as editor:
        editor.hint_configuration = dataclasses.replace(
            editor.hint_configuration,
            enable_random_hints=enable_random_hints,
        )

    # Run
    hints_tab.on_preset_changed(hints_tab._editor.create_custom_preset_with())

    # Assert
    if has_random_hints:
        assert hints_tab.resolver_hints_check.isEnabledTo(parent) == enable_random_hints

    assert hints_tab.random_hints_box.isVisibleTo(parent) == has_random_hints
    assert hints_tab.specific_location_hints_box.isVisibleTo(parent) == has_specific_location_hints
    assert hints_tab.specific_pickup_hints_box.isVisibleTo(parent) == has_specific_pickup_hints


def test_persist_enable_random_hints(skip_qtbot, preset_manager):
    hints_tab = _hints_tab_for_game(preset_manager, RandovaniaGame.METROID_PRIME_ECHOES)
    hints_tab._editor = MagicMock()

    parent = QtWidgets.QWidget()
    hints_tab.setParent(parent)
    skip_qtbot.addWidget(parent)

    # Run
    skip_qtbot.mouseClick(hints_tab.enable_random_hints_check, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    hints_tab._editor.__enter__.return_value.set_hint_configuration_field.assert_called_once_with(
        "enable_random_hints", True
    )


@pytest.mark.parametrize("experimental", [False, True])
@pytest.mark.parametrize("preview_mode", [False, True])
def test_hide_development_settings(experimental: bool, preview_mode: bool, skip_qtbot, preset_manager):
    hints_tab = _hints_tab_for_game(preset_manager, RandovaniaGame.METROID_PRIME_ECHOES)
    hints_tab._window_manager.is_preview_mode = preview_mode
    hints_tab._editor._options.experimental_settings = experimental

    parent = QtWidgets.QWidget()
    hints_tab.setParent(parent)
    skip_qtbot.addWidget(parent)

    # Run
    hints_tab.update_experimental_visibility()

    # Assert
    assert hints_tab.minimum_weight_widget.isVisibleTo(parent) == (experimental and preview_mode)
