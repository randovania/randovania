from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from retro_data_structures.game_check import Game as RDSGame

from randovania.game_connection.connector.prime1_remote_connector import Prime1RemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperationException
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.pickup_index import PickupIndex

if TYPE_CHECKING:
    from open_prime_rando.dol_patching.prime1.dol_patches import Prime1DolVersion


@pytest.fixture(name="version")
def prime1_version():
    from open_prime_rando.dol_patching.prime1 import dol_versions

    return dol_versions.ALL_VERSIONS[0]


@pytest.fixture(name="connector")
def remote_connector(version: Prime1DolVersion):
    connector = Prime1RemoteConnector(version, AsyncMock())
    connector.executor.is_connected = MagicMock()
    connector.executor.disconnect = MagicMock()
    return connector


@pytest.mark.parametrize("artifact", [False, True])
async def test_patches_for_pickup(
    connector: Prime1RemoteConnector, mocker, artifact: bool, generic_pickup_category, default_generator_params
):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "open_prime_rando.dol_patching.all_prime_dol_patches.adjust_item_amount_and_capacity_patch"
    )
    mock_increment_capacity: MagicMock = mocker.patch(
        "open_prime_rando.dol_patching.all_prime_dol_patches.increment_item_capacity_patch"
    )
    mock_artifact_layer: MagicMock = mocker.patch(
        "open_prime_rando.dol_patching.prime1.dol_patches.set_artifact_layer_active_patch"
    )

    db = connector.game.resource_database
    if artifact:
        extra = (db.get_item("Strength"), 1)
    else:
        extra = (db.energy_tank, db.energy_tank.max_capacity)

    pickup = PickupEntry(
        "Pickup",
        0,
        generic_pickup_category,
        generic_pickup_category,
        progression=(),
        generator_params=default_generator_params,
        extra_resources=(extra,),
    )
    inventory = Inventory(
        {
            connector.multiworld_magic_item: InventoryItem(0, 0),
            db.energy_tank: InventoryItem(1, 1),
        }
    )

    # Run
    patches, message = await connector._patches_for_pickup("Someone", pickup, inventory)

    # Assert
    expected_patches = []

    if artifact:
        mock_artifact_layer.assert_called_once_with(connector.version, 2, True)
        expected_patches.append(mock_artifact_layer.return_value)
        used_patch, unused_patch = mock_increment_capacity, mock_item_patch
    else:
        mock_artifact_layer.assert_not_called()
        used_patch, unused_patch = mock_item_patch, mock_increment_capacity

    expected_patches.insert(0, used_patch.return_value)
    used_patch.assert_called_once_with(
        connector.version.powerup_functions, RDSGame.PRIME, extra[0].extra["item_id"], extra[1]
    )
    unused_patch.assert_not_called()

    assert patches == expected_patches
    assert message == "Received Pickup from Someone."


@pytest.mark.parametrize("has_cooldown", [False, True])
@pytest.mark.parametrize("has_patches", [False, True])
async def test_multiworld_interaction_missing_remote_pickups(has_cooldown: bool, has_patches: bool, version):
    connector = Prime1RemoteConnector(version, AsyncMock())

    # Setup
    if has_cooldown:
        initial_cooldown = 2.0
    else:
        initial_cooldown = 0.0
    connector.message_cooldown = initial_cooldown

    connector._patches_for_pickup = AsyncMock()
    connector._patches_for_pickup.return_value = ([[]], "")
    magic_item = MagicMock()
    magic_item.amount = 0
    magic_item.capacity = 0
    inventory = MagicMock()
    inventory.get = MagicMock()
    inventory.get.return_value = magic_item

    remote_pickups = [("", MagicMock())] if has_patches else []

    # Run
    await connector.receive_remote_pickups(inventory, remote_pickups)

    # Assert
    if has_patches and not has_cooldown:
        assert connector.message_cooldown == 4.0
    else:
        assert connector.message_cooldown == initial_cooldown


@pytest.mark.parametrize("depth", [0, 1])
async def test_multiworld_interaction(connector: Prime1RemoteConnector, depth: int):
    # Setup
    # depth 0: non-empty known_collected_locations with patch
    # depth 1: empty known_collected_locations and empty receive_remote_pickups

    location_collected = MagicMock()
    connector.PickupIndexCollected.connect(location_collected)

    connector.receive_remote_pickups = AsyncMock(return_value=([], False))
    connector.known_collected_locations = AsyncMock(return_value=[PickupIndex(2), PickupIndex(5)] if depth == 0 else [])

    # Run
    await connector._multiworld_interaction()

    # Assert
    connector.known_collected_locations.assert_awaited_once_with()

    if depth == 0:
        location_collected.assert_has_calls(
            [
                call(PickupIndex(2)),
                call(PickupIndex(5)),
            ]
        )
    else:
        location_collected.assert_not_called()

    if depth == 1:
        connector.receive_remote_pickups.assert_awaited_once_with(connector.last_inventory, connector.remote_pickups)
    else:
        connector.receive_remote_pickups.assert_not_awaited()


@pytest.mark.parametrize("failure_at", [None, 1, 2])
@pytest.mark.parametrize("depth", [0, 1, 2, 3])
async def test_interact_with_game(connector: Prime1RemoteConnector, depth: int, failure_at: int | None):
    # Setup
    connector.message_cooldown = 0.0
    connector.executor.is_connected.return_value = True
    connector.executor.disconnect = MagicMock()

    connector.get_inventory = AsyncMock()
    connector.current_game_status = AsyncMock(
        return_value=(
            depth <= 1,  # has pending op
            MagicMock() if depth > 0 else None,  # db
        )
    )

    should_disconnect = False
    if failure_at == 1:
        connector.get_inventory.side_effect = MemoryOperationException("error at _get_inventory")
        should_disconnect = depth > 0

    connector._send_next_pending_message = AsyncMock()
    connector._multiworld_interaction = AsyncMock(return_value=depth <= 2)
    if failure_at == 2:
        connector._multiworld_interaction.side_effect = MemoryOperationException("error at _check_for_collected_index")
        should_disconnect = depth > 1

    expected_depth = min(depth, failure_at) if failure_at is not None else depth
    if (failure_at or 999) <= depth:
        should_disconnect = True

    # Run
    await connector.update()

    # Assert
    connector.current_game_status.assert_awaited_once_with()

    if expected_depth > 0:
        connector.get_inventory.assert_awaited_once_with()
    else:
        connector.get_inventory.assert_not_awaited()

    if expected_depth > 1:
        connector._multiworld_interaction.assert_awaited_once_with()
    else:
        connector._multiworld_interaction.assert_not_awaited()

    if expected_depth > 2:
        connector._send_next_pending_message.assert_awaited_once_with()
    else:
        connector._send_next_pending_message.assert_not_awaited()

    if 0 < depth:
        assert connector._last_emitted_region is not None
    else:
        assert connector._last_emitted_region is None

    if should_disconnect:
        connector.executor.disconnect.assert_called_once_with()
    else:
        connector.executor.disconnect.assert_not_called()
