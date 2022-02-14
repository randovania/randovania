from unittest.mock import MagicMock, call

import randovania.generator.item_pool.ammo
import randovania.generator.item_pool.pickup_creator
from randovania.layout.base.ammo_configuration import AmmoConfiguration


def test_add_ammo(echoes_resource_database, mocker):
    # Setup
    mock_create_ammo_expansion: MagicMock = mocker.patch(
        "randovania.generator.item_pool.ammo.create_ammo_expansion", autospec=True)

    ammo1 = MagicMock()
    ammo2 = MagicMock()
    state1 = MagicMock()
    state2 = MagicMock()

    ammo_configuration = AmmoConfiguration({
        ammo1: state1,
        ammo2: state2,
    })

    # Run
    results = list(randovania.generator.item_pool.ammo.add_ammo(echoes_resource_database, ammo_configuration))

    # Assert
    assert results == [mock_create_ammo_expansion.return_value, mock_create_ammo_expansion.return_value]
    mock_create_ammo_expansion.assert_has_calls([
        call(ammo1, state1.ammo_count, state1.requires_major_item, echoes_resource_database),
        call(ammo2, state2.ammo_count, state2.requires_major_item, echoes_resource_database),
    ])
