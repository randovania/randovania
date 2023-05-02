from unittest.mock import MagicMock, call

import randovania.generator.pickup_pool.ammo_pickup
import randovania.generator.pickup_pool.pickup_creator
from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration


def test_add_ammo(echoes_resource_database, mocker):
    # Setup
    mock_create_ammo_pickup: MagicMock = mocker.patch(
        "randovania.generator.pickup_pool.ammo_pickup.create_ammo_pickup", autospec=True)

    ammo1 = MagicMock()
    ammo2 = MagicMock()
    state1 = MagicMock()
    state2 = MagicMock()

    ammo_configuration = AmmoPickupConfiguration({
        ammo1: state1,
        ammo2: state2,
    })

    # Run
    results = list(randovania.generator.pickup_pool.ammo_pickup.add_ammo_pickups(echoes_resource_database, ammo_configuration))

    # Assert
    assert results == [mock_create_ammo_pickup.return_value, mock_create_ammo_pickup.return_value]
    mock_create_ammo_pickup.assert_has_calls([
        call(ammo1, state1.ammo_count, state1.requires_main_item, echoes_resource_database),
        call(ammo2, state2.ammo_count, state2.requires_main_item, echoes_resource_database),
    ])
