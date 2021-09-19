from unittest.mock import MagicMock

from PySide2.QtWidgets import QWidget

from randovania.games.game import RandovaniaGame
from randovania.gui.dialog import trick_usage_popup


def test_click_on_link(echoes_game_description,
                       skip_qtbot,
                       default_echoes_preset):
    # Setup
    main_window = QWidget()
    main_window.open_data_visualizer_at = MagicMock()
    skip_qtbot.add_widget(main_window)
    world_name = "World"
    area_name = "Area"

    # Run
    popup = trick_usage_popup.TrickUsagePopup(
        main_window,
        main_window,
        default_echoes_preset
    )
    popup._on_click_link_to_data_editor(f"data-editor://{world_name}/{area_name}")

    # Assert
    main_window.open_data_visualizer_at.assert_called_once_with(world_name, area_name,
                                                                game=RandovaniaGame.METROID_PRIME_ECHOES)
    assert popup.area_list_label.text() == ""
