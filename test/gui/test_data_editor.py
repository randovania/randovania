import pytest

from randovania.game_description.requirements import RequirementSet
from randovania.gui.data_editor import DataEditorWindow

pytestmark = pytest.mark.skipif(
    pytest.config.option.skip_gui_tests,
    reason="skipped due to --skip-gui-tests")


def test_apply_edit_connections_change(echoes_game_data,
                                       qtbot,
                                       ):
    # Setup
    window = DataEditorWindow(echoes_game_data, True)
    qtbot.addWidget(window)
    game = window.game_description

    landing_site = game.world_list.area_by_asset_id(1655756413)
    source = landing_site.node_with_name("Save Station")
    target = landing_site.node_with_name("Door to Service Access")

    # Run
    window.world_selector_box.setCurrentIndex(window.world_selector_box.findText("Temple Grounds"))
    window.area_selector_box.setCurrentIndex(window.area_selector_box.findText(landing_site.name))
    window._apply_edit_connections(source, target, RequirementSet.trivial())

    # Assert
    assert landing_site.connections[source][target] == RequirementSet.trivial()


def test_select_area_by_name(echoes_game_data,
                             qtbot,
                             ):
    # Setup
    window = DataEditorWindow(echoes_game_data, True)
    qtbot.addWidget(window)

    # Run
    window.focus_on_world("Torvus Bog")

    assert window.current_area.name != "Forgotten Bridge"
    window.focus_on_area("Forgotten Bridge")

    # Assert
    assert window.current_area.name == "Forgotten Bridge"
