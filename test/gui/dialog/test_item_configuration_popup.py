from __future__ import annotations

from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.standard_pickup_widget import StandardPickupWidget
from randovania.layout.base.standard_pickup_state import StandardPickupState, StandardPickupStateCase


def test_state_no_changes(skip_qtbot, echoes_pickup_database, echoes_resource_database):
    item = [item for item in echoes_pickup_database.standard_pickups.values() if not item.must_be_starting][0]
    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_pickups=0,
        included_ammo=(),
    )

    # Run
    popup = StandardPickupWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)

    # Assert
    assert popup.state == state


def test_state_change_to_starting(skip_qtbot, echoes_pickup_database, echoes_resource_database):
    item = [item for item in echoes_pickup_database.standard_pickups.values() if not item.must_be_starting][0]
    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_pickups=0,
        included_ammo=(),
    )

    # Run
    popup = StandardPickupWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)
    set_combo_with_value(popup.state_case_combo, StandardPickupStateCase.STARTING_ITEM)

    # Assert
    assert popup.case == StandardPickupStateCase.STARTING_ITEM
    assert popup.state == StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=1,
        priority=1.0,
        included_ammo=(),
    )


def test_state_change_to_shuffled(skip_qtbot, echoes_pickup_database, echoes_resource_database):
    item = echoes_pickup_database.standard_pickups["Progressive Suit"]
    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_pickups=0,
        included_ammo=(),
    )

    # Run
    popup = StandardPickupWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)

    # Initial State
    assert popup.state == state
    assert popup.case == StandardPickupStateCase.CUSTOM

    # After Changing
    set_combo_with_value(popup.state_case_combo, StandardPickupStateCase.SHUFFLED)
    assert popup.state == StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=2,
        num_included_in_starting_pickups=0,
        included_ammo=(),
    )
    assert popup.case == StandardPickupStateCase.SHUFFLED


def test_state_must_be_starting(skip_qtbot, echoes_pickup_database, echoes_resource_database):
    item = [item for item in echoes_pickup_database.standard_pickups.values() if item.must_be_starting][0]
    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_pickups=0,
        included_ammo=(),
    )

    # Run
    popup = StandardPickupWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)

    # Assert
    assert popup.state == StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=1,
        included_ammo=(),
    )
