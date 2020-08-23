import pytest
from PySide2.QtCore import Qt

from randovania.game_connection.connection_backend import ConnectionStatus
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.gui.debug_backend_window import DebugBackendWindow, iterate_enum


@pytest.fixture(name="backend")
def debug_backend_window(skip_qtbot):
    return DebugBackendWindow()


@pytest.fixture(name="pickup")
def _pickup() -> PickupEntry:
    return PickupEntry(
        name="Pickup",
        model_index=0,
        item_category=ItemCategory.MOVEMENT,
        resources=(
            ConditionalResources(None, None, ()),
        ),
    )


@pytest.mark.parametrize("expected_status", iterate_enum(ConnectionStatus))
def test_current_status(backend, expected_status):
    all_status = list(iterate_enum(ConnectionStatus))

    backend.current_status_combo.setCurrentIndex(all_status.index(expected_status))
    assert backend.current_status == expected_status


@pytest.mark.asyncio
async def test_display_message(backend):
    message = "Foo"
    await backend.display_message(message)
    assert backend.messages_list.findItems(message, Qt.MatchFlag.MatchExactly)


@pytest.mark.asyncio
async def test_empty_get_inventory(backend):
    assert await backend.get_inventory() == {}


def test_send_pickup(backend, pickup):
    backend.send_pickup(pickup)
    assert backend.inventory_label.text() == "Pickup x1"


def test_set_permanent_pickups(backend, pickup):
    backend.set_permanent_pickups([pickup])
    assert backend.inventory_label.text() == "Pickup x1"


@pytest.mark.asyncio
async def test_setup_locations_combo(backend):
    await backend._setup_locations_combo()
    assert backend.collect_location_combo.count() > 100


def test_clear(backend):
    backend.clear()
    assert backend.messages_list.count() == 0
    assert backend.inventory_label.text() == ""
