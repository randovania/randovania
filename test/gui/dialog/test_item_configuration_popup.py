from randovania.gui.lib.signal_handling import set_combo_with_value
from randovania.gui.preset_settings.item_configuration_widget import ItemConfigurationWidget
from randovania.layout.base.major_item_state import MajorItemState, MajorItemStateCase


def test_state_no_changes(skip_qtbot, echoes_pickup_database, echoes_resource_database):
    item = [item for item in echoes_pickup_database.standard_pickups.values() if not item.must_be_starting][0]
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_items=0,
        included_ammo=(),
    )

    # Run
    popup = ItemConfigurationWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)

    # Assert
    assert popup.state == state


def test_state_change_to_starting(skip_qtbot, echoes_pickup_database, echoes_resource_database):
    item = [item for item in echoes_pickup_database.standard_pickups.values() if not item.must_be_starting][0]
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_items=0,
        included_ammo=(),
    )

    # Run
    popup = ItemConfigurationWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)
    set_combo_with_value(popup.state_case_combo, MajorItemStateCase.STARTING_ITEM)

    # Assert
    assert popup.state == MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=1,
        priority=1.0,
        included_ammo=(),
    )


def test_state_must_be_starting(skip_qtbot, echoes_pickup_database, echoes_resource_database):
    item = [item for item in echoes_pickup_database.standard_pickups.values() if item.must_be_starting][0]
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_items=0,
        included_ammo=(),
    )

    # Run
    popup = ItemConfigurationWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)

    # Assert
    assert popup.state == MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=1,
        included_ammo=(),
    )
