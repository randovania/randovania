from randovania.game_description.resources import PickupEntry
from randovania.resolver import item_pool


def test_remove_pickup_entry_from_list():
    # Setup
    items = (
        PickupEntry("World", "Room", "Item A", {}, ""),
        PickupEntry("World", "Room", "Item B", {}, ""),
        PickupEntry("World", "Room", "Item A", {}, ""),
        PickupEntry("World", "Room", "Item C", {}, ""),
    )

    # Run
    filtered_item_pool = item_pool.remove_pickup_entry_from_list(
        items,
        PickupEntry("World", "Room", "Item A", {}, "")
    )

    # Assert
    assert filtered_item_pool == (
        PickupEntry("World", "Room", "Item B", {}, ""),
        PickupEntry("World", "Room", "Item A", {}, ""),
        PickupEntry("World", "Room", "Item C", {}, ""),
    )

