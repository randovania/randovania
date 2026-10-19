from __future__ import annotations

from PySide6 import QtCore

from randovania.gui.widgets.resource_gain_list_view import ResourceGainListView


def test_items_round_trip(skip_qtbot, blank_resource_db):
    widget = ResourceGainListView()
    skip_qtbot.addWidget(widget)
    widget.create_model([*blank_resource_db.item, *blank_resource_db.event])
    granted = ((blank_resource_db.get_item("Ammo"), 5), (blank_resource_db.get_event("Boss"), 1))

    # Run
    widget.items = granted

    # Assert
    assert widget.isEnabled()
    assert widget.items == granted


def test_add_and_remove(skip_qtbot, blank_resource_db):
    widget = ResourceGainListView()
    skip_qtbot.addWidget(widget)
    resources = [blank_resource_db.get_item("Weapon"), blank_resource_db.get_item("Ammo")]
    widget.create_model(resources)
    widget.items = ((blank_resource_db.get_item("Weapon"), 1),)

    # Run
    skip_qtbot.mouseClick(widget.add_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert: new rows start with the first resource by long name, amount 1
    assert widget.items == (
        (blank_resource_db.get_item("Weapon"), 1),
        (blank_resource_db.get_item("Ammo"), 1),
    )

    # Run
    widget.table.selectRow(0)
    skip_qtbot.mouseClick(widget.remove_selected_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    assert widget.items == ((blank_resource_db.get_item("Ammo"), 1),)


def test_no_resources_disables(skip_qtbot):
    widget = ResourceGainListView()
    skip_qtbot.addWidget(widget)

    # Run
    widget.create_model([])
    skip_qtbot.mouseClick(widget.add_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    assert not widget.isEnabled()
    assert widget.items == ()
