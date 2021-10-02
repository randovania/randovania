import dataclasses
import uuid
import pytest
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.node import PickupNode
from randovania.gui.preset_settings.location_pool_row_widget import LocationPoolRowWidget
from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset

@pytest.fixture()
def pickup_node():
    return PickupNode(
        pickup_index=PickupIndex(1), 
        major_location=True,
        name="Pickup (Ultra Beam)",
        heal=False,
        location=None,
        index=0
    )


def test_location_pool_row_initial_state(pickup_node, skip_qtbot):
    # Setup & Run
    widget = LocationPoolRowWidget(pickup_node, "Fancy name for a pickup")
    skip_qtbot.addWidget(widget)

    # Assert
    assert widget.label_location_name.text() == "Fancy name for a pickup"


def test_location_pool_row_actions(skip_qtbot):
    # Setup
    widget = LocationPoolRowWidget(pickup_node, "Fancy name for a pickup")
    skip_qtbot.addWidget(widget)

    signal_received = False
    def edit_closure():
        nonlocal signal_received
        signal_received = True
    widget.changed.connect(edit_closure)

    # Run & Assert
    assert not signal_received
    widget.set_can_have_progression(True)
    assert signal_received
    assert widget.radio_shuffled.isChecked()



def test_location_pool_row_disabled_on_major_minor_split(customized_preset, echoes_game_description, skip_qtbot):
    # Setup
    preset_editor = PresetEditor(customized_preset)

    location_pool_tab = PresetLocationPool(preset_editor, echoes_game_description)

    # Get the first major location in the list, and the first non-major one
    # Then, put it in a state which will have to be changed in the case where
    # major/minor split is enabled.
    first_major: LocationPoolRowWidget = None
    first_non_major: LocationPoolRowWidget = None
    for row_widget in location_pool_tab._row_widget_for_node.values():
        if first_major is None and row_widget.node.major_location:
            first_major = row_widget
        elif first_non_major is None and not row_widget.node.major_location:
            first_non_major = row_widget
        if first_major is not None and first_non_major is not None:
            break
    first_major.radio_shuffled_no_progression.setChecked(True)

    # Run & Assert
    assert first_major.isEnabled()
    assert first_non_major.isEnabled()
    assert not first_major.radio_shuffled.isChecked()

    location_pool_tab.check_major_minor.setChecked(True)

    assert first_major.isEnabled()
    assert not first_non_major.isEnabled()
    assert first_major.radio_shuffled.isChecked()
