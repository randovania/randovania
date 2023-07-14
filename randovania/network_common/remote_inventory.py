from __future__ import annotations

import construct

from randovania.bitpacking import construct_pack
from randovania.game_description.resources.item_resource_info import Inventory, InventoryItem

OldRemoteInventory = dict[str, InventoryItem]
RemoteInventory = dict[str, int]


def inventory_to_encoded_remote(inventory: Inventory) -> bytes:
    return construct_pack.encode(
        {item.short_name: item_state.capacity
         for item, item_state in inventory.items()},
        RemoteInventory
    )


def decode_remote_inventory(data: bytes) -> RemoteInventory | construct.ConstructError:
    try:
        inventory = construct_pack.decode(data, RemoteInventory)

    except construct.ConstructError as e:
        try:
            old_inventory = construct_pack.decode(data, OldRemoteInventory)
        except construct.ConstructError:
            return e

        inventory = {
            name: it.capacity
            for name, it in old_inventory.items()
        }

    return inventory
