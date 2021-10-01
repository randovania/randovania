import pytest
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.node import PickupNode
from randovania.gui.preset_settings.location_pool_row_widget import LocationPoolRowWidget

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