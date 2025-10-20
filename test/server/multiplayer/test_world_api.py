from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, PropertyMock, call

import peewee
import pytest
from frozendict import frozendict

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupModel, StartingPickupBehavior
from randovania.game_description.resources.inventory import Inventory
from randovania.network_common import error, remote_inventory, signals
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.world_sync import (
    ServerSyncRequest,
    ServerSyncResponse,
    ServerWorldResponse,
    ServerWorldSync,
)
from randovania.server import database
from randovania.server.multiplayer import world_api

if TYPE_CHECKING:
    import pytest_mock
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    ("progression", "start_case", "result"),
    [
        (  # normal
            [("Power", 1)],
            StartingPickupBehavior.MUST_BE_STARTING,
            (
                "C?ypIwY9x9y^)o&8#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rr"
                "mqu35FxlB#nOvG!<^@M(Ze?<5V<1U%Wo;lsVRU6@Z*qBTEyNQ5I=4BvGO@I?G_tY~G`cdjfdL?~00"
            ),
        ),
        (  # negative
            [("Missile", -5)],
            StartingPickupBehavior.CAN_BE_STARTING,
            (
                "C?ypIwY9x9y^)o&8#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rr"
                "mqu35FxlB#nOvG!<^@M(Ze?<5V<1U%Wo;lsVRU6@Z*qBTEyNQ5I=4BvGO@I?G_tY~G`cdjfl&GZVgL"
            ),
        ),
        (  # progressive
            [("DarkSuit", 1), ("LightSuit", 1)],
            StartingPickupBehavior.CAN_NEVER_BE_STARTING,
            (
                "C?ypIwY9x9y^)o&8#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rr"
                "mqu35FxlB#nOvG!<^@M(Ze?<5V<1U%Wo;lsVRU6@Z*qBTEyNQ5I=4BvGO@I?G_tY~G`cdjf*TH?Sbz"
            ),
        ),
    ],
)
async def test_emit_world_pickups_update_one_action(
    mock_sa,
    two_player_session,
    generic_pickup_category,
    default_generator_params,
    echoes_resource_database,
    mocker,
    progression,
    start_case,
    result,
):
    # Setup
    mock_emit = mock_sa.sio.emit

    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock
    )
    mock_get_resource_database: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_resource_database", autospec=True
    )
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True
    )

    mock_sa.get_current_user.return_value = database.User.get_by_id(1234)

    w1 = database.World.get_by_id(1)

    progression = tuple((echoes_resource_database.get_item(item), amount) for item, amount in progression)
    pickup = PickupEntry(
        "A",
        PickupModel(echoes_resource_database.game_enum, "AmmoModel"),
        generic_pickup_category,
        frozenset((generic_pickup_category,)),
        progression=progression,
        start_case=start_case,
        generator_params=default_generator_params,
    )
    mock_get_pickup_target.return_value = PickupTarget(pickup=pickup, player=0)
    mock_get_resource_database.return_value = echoes_resource_database

    # Run
    await world_api.emit_world_pickups_update(mock_sa, w1)

    # # Uncomment this to encode the data once again and get the new bytefield if it changed for some reason
    # from randovania.server.multiplayer.world_api import _base64_encode_pickup
    # new_data = _base64_encode_pickup(pickup, echoes_resource_database)
    # assert new_data == b""

    # Assert
    mock_get_resource_database.assert_called_once_with(mock_session_description.return_value, 0)
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 1, 0)
    mock_emit.assert_awaited_once_with(
        "world_pickups_update",
        {
            "game": "prime2",
            "pickups": [
                {
                    "provider_name": "World 2",
                    "pickup": result,
                    "coop_location": None,
                }
            ],
            "world": "1179c986-758a-4170-9b07-fe4541d78db0",
        },
        room="world-1179c986-758a-4170-9b07-fe4541d78db0",
    )


def test_add_pickup_to_inventory_success(dread_spider_pickup):
    inventory = remote_inventory.inventory_to_encoded_remote(Inventory.empty())
    new_inventory = world_api._add_pickup_to_inventory(inventory, dread_spider_pickup, RandovaniaGame.METROID_DREAD)

    assert remote_inventory.decode_remote_inventory(new_inventory) == {
        "Magnet": 1,
    }


def test_add_pickup_to_inventory_bad(dread_spider_pickup):
    inventory = b"THIS_IS_NOT_A_PROPER_INVENTORY"
    new_inventory = world_api._add_pickup_to_inventory(inventory, dread_spider_pickup, RandovaniaGame.METROID_DREAD)

    assert new_inventory == inventory


@pytest.mark.parametrize("has_pickup", [True, False])
async def test_game_session_collect_pickup_for_self(
    has_pickup: bool,
    mock_sa,
    two_player_session,
    generic_pickup_category,
    default_generator_params,
    echoes_resource_database,
    mocker,
):
    # Setup
    mock_sa.get_current_user.return_value = database.User.get_by_id(1234)

    mock_sa.sio.emit = AsyncMock()

    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock
    )
    mock_get_resource_database: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_resource_database", autospec=True
    )
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True
    )

    w1 = database.World.get_by_id(1)

    if has_pickup:
        pickup = PickupEntry(
            "A",
            1,
            generic_pickup_category,
            frozenset((generic_pickup_category,)),
            progression=((echoes_resource_database.item[0], 1),),
            generator_params=default_generator_params,
        )
        mock_get_resource_database.return_value = echoes_resource_database
        mock_get_pickup_target.return_value = PickupTarget(pickup, 0)
    else:
        mock_get_pickup_target.return_value = None

    # Run
    result = await world_api.collect_locations(mock_sa, w1, (0,))

    # Assert
    assert result == set()
    mock_sa.sio.emit.assert_not_awaited()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.WorldAction.get(provider=w1, location=0)


@pytest.mark.parametrize(
    ("locations_to_collect", "exists"),
    [
        ((0,), ()),
        ((0,), (0,)),
        ((0, 1), ()),
        ((0, 1), (0,)),
        ((0, 1), (0, 1)),
    ],
)
async def test_collect_locations_other(
    mock_sa,
    two_player_session,
    echoes_resource_database,
    locations_to_collect: tuple[int, ...],
    exists: tuple[int, ...],
    mocker: pytest_mock.MockerFixture,
):
    mock_get_pickup_target = mocker.patch("randovania.server.multiplayer.world_api._get_pickup_target", autospec=True)
    mock_add_pickup_to_inventory = mocker.patch(
        "randovania.server.multiplayer.world_api._add_pickup_to_inventory", autospec=True, return_value=b"bar"
    )
    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock
    )
    mock_emit_session_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_actions_update", autospec=True
    )

    mock_sa.get_current_user.return_value = database.User.get_by_id(1234)
    mock_get_pickup_target.return_value = PickupTarget(MagicMock(), 1)

    w1 = database.World.get_by_id(1)
    w2 = database.World.get_by_id(2)
    assoc = database.WorldUserAssociation.get_by_instances(world=w2, user=1235)
    assoc.inventory = b"boo"
    assoc.save()

    for existing_id in exists:
        database.WorldAction.create(
            provider=w1,
            location=existing_id,
            session=two_player_session,
            receiver=w2,
        )

    # Run
    result = await world_api.collect_locations(mock_sa, w1, locations_to_collect)

    # Assert
    mock_get_pickup_target.assert_has_calls(
        [call(mock_session_description.return_value, 0, location) for location in locations_to_collect]
    )
    for location in locations_to_collect:
        database.WorldAction.get(provider=w1, location=location)

    new_locs = [loc for loc in locations_to_collect if loc not in exists]
    mock_add_pickup_to_inventory.assert_has_calls(
        [
            call(
                inv,
                mock_get_pickup_target.return_value.pickup,
                mock_session_description.return_value.get_preset.return_value.game,
            )
            for inv, _ in zip([b"boo", b"bar"], new_locs, strict=False)
        ]
    )
    mock_emit_session_update.assert_not_called()
    if exists == locations_to_collect:
        assert result == set()
    else:
        assert result == {w2}


async def test_world_sync(mock_sa, solo_two_world_session, mocker: MockerFixture, mock_emit_session_update):
    mock_leave_room = mock_sa.sio.leave_room
    mock_emit = mock_sa.sio.emit
    mock_emit_pickups = mocker.patch("randovania.server.multiplayer.world_api.emit_world_pickups_update")
    mock_emit_actions = mocker.patch("randovania.server.multiplayer.session_common.emit_session_actions_update")
    mock_emit_inventory = mocker.patch("randovania.server.multiplayer.world_api.emit_inventory_update")
    mock_emit_session_audit_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_audit_update"
    )

    user = database.User.get_by_id(1234)
    mock_sa.get_current_user.return_value = user

    w1 = database.World.get_by_id(1)
    w2 = database.World.get_by_id(2)
    session = database.MultiplayerSession.get_by_id(solo_two_world_session.id)

    request = ServerSyncRequest(
        worlds=frozendict(
            {
                w1.uuid: ServerWorldSync(
                    status=GameConnectionStatus.InGame,
                    collected_locations=(5,),
                    inventory=b"foo",
                    request_details=True,
                    has_been_beaten=True,
                ),
                w2.uuid: ServerWorldSync(
                    status=GameConnectionStatus.Disconnected,
                    collected_locations=(15,),
                    inventory=None,
                    request_details=False,
                    has_been_beaten=False,
                ),
                uuid.UUID("a0cf12f7-8a0e-47ed-9a82-cabfc8b912c2"): ServerWorldSync(
                    status=GameConnectionStatus.TitleScreen,
                    collected_locations=(60,),
                    inventory=None,
                    request_details=False,
                    has_been_beaten=False,
                ),
            }
        )
    )

    # Run
    result = await world_api.world_sync(mock_sa, "TheSid", request)

    # Assert
    assert result == ServerSyncResponse(
        worlds=frozendict(
            {
                w1.uuid: ServerWorldResponse(
                    world_name=w1.name,
                    session_id=session.id,
                    session_name=session.name,
                ),
            }
        ),
        errors=frozendict(
            {
                uuid.UUID("a0cf12f7-8a0e-47ed-9a82-cabfc8b912c2"): error.WorldDoesNotExistError(),
            }
        ),
    )

    a1 = database.WorldUserAssociation.get_by_instances(world=w1, user=1234)
    assert a1.connection_state == GameConnectionStatus.InGame
    assert a1.inventory == b"foo"
    a2 = database.WorldUserAssociation.get_by_instances(world=w2, user=1234)
    assert a2.connection_state == GameConnectionStatus.Disconnected
    assert a2.inventory is None

    finished_w1 = database.World.get_by_id(1)  # w1: not beaten -> beaten
    assert not w1.beaten
    assert finished_w1.beaten
    finished_w2 = database.World.get_by_id(2)  # w2: not beaten -> not beaten
    assert not w2.beaten
    assert not finished_w2.beaten

    mock_sa.store_world_in_session.assert_awaited_once_with("TheSid", w1)
    mock_sa.ensure_in_room.assert_awaited_once_with("TheSid", "world-1179c986-758a-4170-9b07-fe4541d78db0")
    mock_leave_room.assert_awaited_once_with("TheSid", "world-6b5ac1a1-d250-4f05-a5fb-ae37e8a92165")
    mock_emit_pickups.assert_has_awaits([call(mock_sa, w1), call(mock_sa, w2)], any_order=True)
    mock_emit_session_update.assert_awaited_once_with(mock_sa, session)
    mock_emit_actions.assert_awaited_once_with(mock_sa, session)
    mock_emit_inventory.assert_awaited_once_with(mock_sa, w1, 1234, b"foo")
    mock_emit_session_audit_update.assert_awaited_once_with(mock_sa, session)
    mock_emit.assert_not_called()


@pytest.mark.parametrize("has_been_beaten", [True, False])
async def test_dont_change_has_beaten(
    mock_sa, solo_two_world_session, mocker: MockerFixture, mock_emit_session_update, has_been_beaten
):
    mock_emit = mock_sa.sio.emit
    mock_emit_pickups = mocker.patch("randovania.server.multiplayer.world_api.emit_world_pickups_update")
    mock_emit_actions = mocker.patch("randovania.server.multiplayer.session_common.emit_session_actions_update")
    mock_emit_inventory = mocker.patch("randovania.server.multiplayer.world_api.emit_inventory_update")
    mock_emit_session_audit_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_audit_update"
    )

    user = database.User.get_by_id(1234)
    mock_sa.get_current_user.return_value = user

    w1 = database.World.get_by_id(1)
    w1.beaten = True
    w1.save()
    session = database.MultiplayerSession.get_by_id(solo_two_world_session.id)

    request = ServerSyncRequest(
        worlds=frozendict(
            {
                w1.uuid: ServerWorldSync(
                    status=GameConnectionStatus.InGame,
                    collected_locations=(5,),
                    inventory=b"foo",
                    request_details=True,
                    has_been_beaten=has_been_beaten,
                )
            }
        )
    )

    # Run
    result = await world_api.world_sync(mock_sa, "TheSid", request)

    # Assert
    assert result == ServerSyncResponse(
        worlds=frozendict(
            {
                w1.uuid: ServerWorldResponse(
                    world_name=w1.name,
                    session_id=session.id,
                    session_name=session.name,
                ),
            }
        ),
        errors=frozendict(),
    )

    finished_w1 = database.World.get_by_id(1)  # w1: beaten status should not change
    assert w1.beaten
    assert finished_w1.beaten

    mock_sa.store_world_in_session.assert_awaited_once_with("TheSid", w1)
    mock_sa.ensure_in_room.assert_awaited_once_with("TheSid", "world-1179c986-758a-4170-9b07-fe4541d78db0")
    mock_emit_pickups.assert_has_awaits([call(mock_sa, w1)], any_order=True)
    mock_emit_session_update.assert_awaited_once_with(mock_sa, session)
    mock_emit_actions.assert_awaited_once_with(mock_sa, session)
    mock_emit_inventory.assert_awaited_once_with(mock_sa, w1, 1234, b"foo")
    mock_emit_session_audit_update.assert_not_awaited()
    mock_emit.assert_not_called()


async def test_report_disconnect(mock_sa, mock_emit_session_update, solo_two_world_session):
    session_dict = {"user-id": 1234, "worlds": [1]}
    a1 = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    a1.connection_state = GameConnectionStatus.InGame
    a1.save()

    # Run
    await world_api.report_disconnect(mock_sa, session_dict)

    # Assert
    a1 = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    assert a1.connection_state == GameConnectionStatus.Disconnected
    mock_emit_session_update.assert_awaited_once_with(mock_sa, database.MultiplayerSession.get_by_id(1))


async def test_emit_inventory_room(mock_sa, solo_two_world_session):
    mock_sa.is_room_not_empty.return_value = True

    world = database.World.get_by_id(1)

    # Run
    await world_api.emit_inventory_update(mock_sa, world, 1234, b"foo")

    # Assert
    mock_sa.sio.emit.assert_awaited_once_with(
        signals.WORLD_BINARY_INVENTORY,
        (str(world.uuid), 1234, b"foo"),
        namespace="/",
        to=f"multiplayer-{world.uuid}-1234-inventory",
    )
