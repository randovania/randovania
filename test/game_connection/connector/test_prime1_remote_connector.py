import pytest
from mock import MagicMock

from randovania.game_connection.connection_base import InventoryItem
from randovania.game_connection.connector.prime1_remote_connector import Prime1RemoteConnector
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.games.game import RandovaniaGame
from randovania.games.prime.prime1_dol_patches import Prime1DolVersion


@pytest.fixture(name="version")
def prime1_version():
    from randovania.games.prime import prime1_dol_versions
    return prime1_dol_versions.ALL_VERSIONS[0]


@pytest.fixture(name="connector")
def remote_connector(version: Prime1DolVersion):
    connector = Prime1RemoteConnector(version)
    return connector


@pytest.mark.parametrize("artifact", [False, True])
@pytest.mark.asyncio
async def test_patches_for_pickup(connector: Prime1RemoteConnector, mocker, artifact: bool, generic_item_category):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.adjust_item_amount_and_capacity_patch")
    mock_increment_capacity: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.increment_item_capacity_patch")
    mock_artifact_layer: MagicMock = mocker.patch(
        "randovania.games.prime.prime1_dol_patches.set_artifact_layer_active_patch")

    db = connector.game.resource_database
    if artifact:
        extra = (db.get_item(30), 1)
    else:
        extra = (db.energy_tank, db.energy_tank.max_capacity)

    pickup = PickupEntry("Pickup", 0, generic_item_category, generic_item_category, progression=tuple(),
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
                                       extra[0].index,
                                       extra[1])
    unused_patch.assert_not_called()

    assert patches == expected_patches
    assert message == "Received Pickup from Someone."
