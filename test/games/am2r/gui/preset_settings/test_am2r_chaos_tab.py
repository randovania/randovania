from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from randovania.games.am2r.gui.preset_settings.am2r_chaos_tab import PresetAM2RChaos
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.interface_common.preset_editor import PresetEditor

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

    from randovania.game_description.game_description import GameDescription
    from randovania.interface_common.preset_manager import PresetManager


def test_darkness_spins(
    skip_qtbot: QtBot, am2r_game_description: GameDescription, preset_manager: PresetManager
) -> None:
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, AM2RConfiguration)

    tab = PresetAM2RChaos(PresetEditor(preset, options), am2r_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert tab.darkness_min_spin.minimum() == 0
    assert tab.darkness_min_spin.maximum() == 4
    assert tab.darkness_max_spin.minimum() == 0
    assert tab.darkness_max_spin.maximum() == 4

    tab.darkness_min_spin.setValue(2)

    assert tab.darkness_min_spin.minimum() == 0
    assert tab.darkness_min_spin.maximum() == 4
    assert tab.darkness_max_spin.minimum() == 2
    assert tab.darkness_max_spin.maximum() == 4

    tab.darkness_max_spin.setValue(3)

    assert tab.darkness_min_spin.minimum() == 0
    assert tab.darkness_min_spin.maximum() == 3
    assert tab.darkness_max_spin.minimum() == 2
    assert tab.darkness_max_spin.maximum() == 4


def test_sliders(skip_qtbot: QtBot, am2r_game_description: GameDescription, preset_manager: PresetManager) -> None:
    game = am2r_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, AM2RConfiguration)

    tab = PresetAM2RChaos(PresetEditor(preset, options), am2r_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert tab.darkness_slider.value() == 0
    assert tab.submerged_water_slider.value() == 0
    assert tab.submerged_lava_slider.value() == 0
    assert tab.darkness_slider_label.text() == "0.0%"
    assert tab.submerged_water_slider_label.text() == "0.0%"
    assert tab.submerged_lava_slider_label.text() == "0.0%"
    assert tab.darkness_slider.maximum() == 1000
    assert tab.submerged_water_slider.maximum() == 1000
    assert tab.submerged_lava_slider.maximum() == 1000
    assert tab.darkness_slider.isEnabled()
    assert tab.submerged_water_slider.isEnabled()
    assert tab.submerged_lava_slider.isEnabled()

    tab.darkness_slider.setValue(459)

    assert tab.darkness_slider.value() == 459
    assert tab.submerged_water_slider.value() == 0
    assert tab.submerged_lava_slider.value() == 0
    assert tab.darkness_slider_label.text() == "45.9%"
    assert tab.submerged_water_slider_label.text() == "0.0%"
    assert tab.submerged_lava_slider_label.text() == "0.0%"
    assert tab.darkness_slider.maximum() == 1000
    assert tab.submerged_water_slider.maximum() == 1000
    assert tab.submerged_lava_slider.maximum() == 1000
    assert tab.darkness_slider.isEnabled()
    assert tab.submerged_water_slider.isEnabled()
    assert tab.submerged_lava_slider.isEnabled()

    tab.submerged_water_slider.setValue(314)

    assert tab.darkness_slider.value() == 459
    assert tab.submerged_water_slider.value() == 314
    assert tab.submerged_lava_slider.value() == 0
    assert tab.darkness_slider_label.text() == "45.9%"
    assert tab.submerged_water_slider_label.text() == "31.4%"
    assert tab.submerged_lava_slider_label.text() == "0.0%"
    assert tab.darkness_slider.maximum() == 1000
    assert tab.submerged_water_slider.maximum() == 1000
    assert tab.submerged_lava_slider.maximum() == 686
    assert tab.darkness_slider.isEnabled()
    assert tab.submerged_water_slider.isEnabled()
    assert tab.submerged_lava_slider.isEnabled()

    tab.submerged_lava_slider.setValue(271)

    assert tab.darkness_slider.value() == 459
    assert tab.submerged_water_slider.value() == 314
    assert tab.submerged_lava_slider.value() == 271
    assert tab.darkness_slider_label.text() == "45.9%"
    assert tab.submerged_water_slider_label.text() == "31.4%"
    assert tab.submerged_lava_slider_label.text() == "27.1%"
    assert tab.darkness_slider.maximum() == 1000
    assert tab.submerged_water_slider.maximum() == 729
    assert tab.submerged_lava_slider.maximum() == 686
    assert tab.darkness_slider.isEnabled()
    assert tab.submerged_water_slider.isEnabled()
    assert tab.submerged_lava_slider.isEnabled()

    tab.submerged_lava_slider.setValue(0)
    tab.submerged_water_slider.setValue(1000)

    assert tab.darkness_slider.value() == 459
    assert tab.submerged_water_slider.value() == 1000
    assert tab.submerged_lava_slider.value() == 0
    assert tab.darkness_slider_label.text() == "45.9%"
    assert tab.submerged_water_slider_label.text() == "100.0%"
    assert tab.submerged_lava_slider_label.text() == "0.0%"
    assert tab.darkness_slider.maximum() == 1000
    assert tab.submerged_water_slider.maximum() == 1000
    assert tab.submerged_lava_slider.maximum() == 0
    assert tab.darkness_slider.isEnabled()
    assert tab.submerged_water_slider.isEnabled()
    assert not tab.submerged_lava_slider.isEnabled()

    tab.submerged_water_slider.setValue(0)
    tab.submerged_lava_slider.setValue(1000)

    assert tab.darkness_slider.value() == 459
    assert tab.submerged_water_slider.value() == 0
    assert tab.submerged_lava_slider.value() == 1000
    assert tab.darkness_slider_label.text() == "45.9%"
    assert tab.submerged_water_slider_label.text() == "0.0%"
    assert tab.submerged_lava_slider_label.text() == "100.0%"
    assert tab.darkness_slider.maximum() == 1000
    assert tab.submerged_water_slider.maximum() == 0
    assert tab.submerged_lava_slider.maximum() == 1000
    assert tab.darkness_slider.isEnabled()
    assert not tab.submerged_water_slider.isEnabled()
    assert tab.submerged_lava_slider.isEnabled()
