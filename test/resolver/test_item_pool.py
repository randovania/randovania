from randovania.game_description.resources import PickupEntry
from randovania.resolver import item_pool


def test_remove_pickup_entry_from_list():
    # Setup
    items = (
        PickupEntry("Item A", tuple(), "", 0),
        PickupEntry("Item B", tuple(), "", 0),
        PickupEntry("Item A", tuple(), "", 0),
        PickupEntry("Item C", tuple(), "", 0),
    )

    # Run
    filtered_item_pool = item_pool.remove_pickup_entry_from_list(
        items,
        PickupEntry("Item A", tuple(), "", 0)
    )

    # Assert
    assert filtered_item_pool == (
        PickupEntry("Item B", tuple(), "", 0),
        PickupEntry("Item A", tuple(), "", 0),
        PickupEntry("Item C", tuple(), "", 0),
    )
