from unittest.mock import MagicMock
from mock import AsyncMock

import pytest

from randovania.game_connection.connection_base import InventoryItem
from randovania.game_connection.connector.prime1_remote_connector import Prime1RemoteConnector
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.patcher.prime1_dol_patches import Prime1DolVersion
from randovania.games.prime1.patcher.prime1_dol_versions import ALL_VERSIONS


@pytest.fixture(name="version")
def prime1_version():
    from randovania.games.prime1.patcher import prime1_dol_versions
    return prime1_dol_versions.ALL_VERSIONS[0]


@pytest.fixture(name="connector")
def remote_connector(version: Prime1DolVersion):
    connector = Prime1RemoteConnector(version, DolphinExecutor())
    return connector


@pytest.mark.parametrize("artifact", [False, True])
async def test_patches_for_pickup(connector: Prime1RemoteConnector, mocker, artifact: bool, generic_pickup_category,
                                  default_generator_params):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.patching.prime.all_prime_dol_patches.adjust_item_amount_and_capacity_patch")
    mock_increment_capacity: MagicMock = mocker.patch(
        "randovania.patching.prime.all_prime_dol_patches.increment_item_capacity_patch")
    mock_artifact_layer: MagicMock = mocker.patch(
        "randovania.games.prime1.patcher.prime1_dol_patches.set_artifact_layer_active_patch")

    db = connector.game.resource_database
    if artifact:
        extra = (db.get_item("Strength"), 1)
    else:
        extra = (db.energy_tank, db.energy_tank.max_capacity)

    pickup = PickupEntry("Pickup", 0, generic_pickup_category, generic_pickup_category, progression=tuple(),
                         generator_params=default_generator_params,
                         extra_resources=(
                             extra,
                         ))
    inventory = {
        db.multiworld_magic_item: InventoryItem(0, 0),
        db.energy_tank: InventoryItem(1, 1),
    }

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
    used_patch.assert_called_once_with(connector.version.powerup_functions,
                                       RandovaniaGame.METROID_PRIME,
                                       extra[0].extra["item_id"],
                                       extra[1])
    unused_patch.assert_not_called()

    assert patches == expected_patches
    assert message == "Received Pickup from Someone."

@pytest.mark.parametrize("has_cooldown", [False, True])
@pytest.mark.parametrize("has_patches", [False, True])
async def test_multiworld_interaction_missing_remote_pickups(has_cooldown: bool, has_patches: bool):
    connector = PrimeRemoteConnector(ALL_VERSIONS[0], AsyncMock())

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