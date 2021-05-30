from PySide2 import QtCore

from randovania.gui.preset_settings.item_configuration_widget import ItemConfigurationWidget
from randovania.layout.base.major_item_state import MajorItemState


def test_state_no_changes(skip_qtbot, echoes_item_database, echoes_resource_database):
    item = [item for item in echoes_item_database.major_items.values() if not item.required][0]
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
    item = [item for item in echoes_item_database.major_items.values() if not item.required][0]
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=1,
        num_included_in_starting_items=0,
        included_ammo=(),
    )

    # Run
    popup = ItemConfigurationWidget(None, item, state, echoes_resource_database)
    skip_qtbot.addWidget(popup)
    skip_qtbot.mouseClick(popup.starting_radio, QtCore.Qt.LeftButton)

    # Assert
    assert popup.state == MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=1,
        included_ammo=(),
    )


def test_state_required(skip_qtbot, echoes_item_database, echoes_resource_database):
    item = [item for item in echoes_item_database.major_items.values() if item.required][0]
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
