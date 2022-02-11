from randovania.gui.preset_settings.item_configuration_widget import ItemConfigurationWidget
from randovania.layout.base.major_item_state import MajorItemState, MajorItemStateCase


def test_state_no_changes(skip_qtbot, echoes_item_database, echoes_resource_database):
    item = [item for item in echoes_item_database.major_items.values() if not item.must_be_starting][0]
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


def test_state_change_to_starting(skip_qtbot, echoes_item_database, echoes_resource_database):
    item = [item for item in echoes_item_database.major_items.values() if not item.must_be_starting][0]
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_items=0,
        included_ammo=(),
    )

    # Run
    popup = ItemConfigurationWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)
    popup.state_case_combo.setCurrentIndex(popup.state_case_combo.findData(MajorItemStateCase.STARTING_ITEM))

    # Assert
    assert popup.state == MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=1,
        priority=1.0,
        included_ammo=(),
    )


def test_state_must_be_starting(skip_qtbot, echoes_item_database, echoes_resource_database):
    item = [item for item in echoes_item_database.major_items.values() if item.must_be_starting][0]
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
