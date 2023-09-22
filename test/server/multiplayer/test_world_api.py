from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, PropertyMock, call

import peewee
import pytest
from frozendict import frozendict

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.inventory import Inventory
from randovania.games.game import RandovaniaGame
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
    ("progression", "result"),
    [
        (  # normal
            [("Power", 1)],
            (
                "C?ypIwY9x9y^)o&8#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rr"
                "mqu378#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rrmqu35fPr8"
            ),
        ),
        (  # negative
            [("Missile", -5)],
            (
                "C?ypIwY9x9y^)o&8#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rr"
                "mqu378#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rrmqu35sC@#!"
            ),
        ),
        (  # progressive
            [("DarkSuit", 1), ("LightSuit", 1)],
            (
                "C?ypIwY9x9y^)o&8#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rr"
                "mqu378#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rrmqu364TnIm"
            ),
        ),
    ],
)
def test_emit_world_pickups_update_one_action(
    flask_app,
    two_player_session,
    generic_pickup_category,
    default_generator_params,
    echoes_resource_database,
    mocker,
    progression,
    result,
):
    # Setup
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock
    )
    mock_get_resource_database: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_resource_database", autospec=True
    )
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True
    )

    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)

    w1 = database.World.get_by_id(1)

    progression = tuple((echoes_resource_database.get_item(item), amount) for item, amount in progression)
    pickup = PickupEntry(
        "A",
        PickupModel(echoes_resource_database.game_enum, "AmmoModel"),
        generic_pickup_category,
        generic_pickup_category,
        progression=progression,
        generator_params=default_generator_params,
    )
    mock_get_pickup_target.return_value = PickupTarget(pickup=pickup, player=0)
    mock_get_resource_database.return_value = echoes_resource_database

    # Run
    world_api.emit_world_pickups_update(sa, w1)

    # Uncomment this to encode the data once again and get the new bytefield if it changed for some reason
    # from randovania.server.multiplayer.world_api import _base64_encode_pickup
    # new_data = _base64_encode_pickup(pickup, echoes_resource_database)
    # assert new_data == b""

    # Assert
    mock_get_resource_database.assert_called_once_with(mock_session_description.return_value, 0)
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 1, 0)
    mock_emit.assert_called_once_with(
        "world_pickups_update",
        {
            "game": "prime2",
            "pickups": [{"provider_name": "World 2", "pickup": result}],
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


def test_game_session_collect_pickup_for_self(
    flask_app, two_player_session, generic_pickup_category, default_generator_params, echoes_resource_database, mocker
):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)

    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")
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

    pickup = PickupEntry(
        "A",
        1,
        generic_pickup_category,
        generic_pickup_category,
        progression=((echoes_resource_database.item[0], 1),),
        generator_params=default_generator_params,
    )
    mock_get_resource_database.return_value = echoes_resource_database
    mock_get_pickup_target.return_value = PickupTarget(pickup, 0)

    # Run
    with flask_app.test_request_context():
        result = world_api.collect_locations(sa, w1, (0,))

    # Assert
    assert result == set()
    mock_emit.assert_not_called()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.WorldAction.get(provider=w1, location=0)


def test_game_session_collect_pickup_etm(flask_app, two_player_session, echoes_resource_database, mocker):
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)

    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")
    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock
    )
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True
    )

    mock_get_pickup_target.return_value = None
    w1 = database.World.get_by_id(1)

    # Run
    with flask_app.test_request_context():
        result = world_api.collect_locations(sa, w1, (0,))

    # Assert
    assert result == set()
    mock_emit.assert_not_called()
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
def test_collect_locations_other(
    flask_app,
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

    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)
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
    with flask_app.test_request_context():
        result = world_api.collect_locations(sa, w1, locations_to_collect)

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


def test_world_sync(flask_app, solo_two_world_session, mocker: MockerFixture, mock_emit_session_update):
    mock_leave_room = mocker.patch("flask_socketio.leave_room")
    mock_emit = mocker.patch("flask_socketio.emit")
    mock_emit_pickups = mocker.patch("randovania.server.multiplayer.world_api.emit_world_pickups_update")
    mock_emit_actions = mocker.patch("randovania.server.multiplayer.session_common.emit_session_actions_update")
    mock_emit_inventory = mocker.patch("randovania.server.multiplayer.world_api.emit_inventory_update")

    sa = MagicMock()
    user = database.User.get_by_id(1234)
    sa.get_current_user.return_value = user

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
                ),
                w2.uuid: ServerWorldSync(
                    status=GameConnectionStatus.Disconnected,
                    collected_locations=(15,),
                    inventory=None,
                    request_details=False,
                ),
                uuid.UUID("a0cf12f7-8a0e-47ed-9a82-cabfc8b912c2"): ServerWorldSync(
                    status=GameConnectionStatus.TitleScreen,
                    collected_locations=(60,),
                    inventory=None,
                    request_details=False,
                ),
            }
        )
    )

    # Run
    with flask_app.test_request_context():
        result = world_api.world_sync(sa, request)

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

    sa.store_world_in_session.assert_called_once_with(w1)
    sa.ensure_in_room.assert_called_once_with("world-1179c986-758a-4170-9b07-fe4541d78db0")
    mock_leave_room.assert_called_once_with("world-6b5ac1a1-d250-4f05-a5fb-ae37e8a92165")
    mock_emit_pickups.assert_has_calls([call(sa, w1), call(sa, w2)], any_order=True)
    mock_emit_session_update.assert_called_once_with(session)
    mock_emit_actions.assert_called_once_with(session)
    mock_emit_inventory.assert_called_once_with(sa, w1, 1234, b"foo")
    mock_emit.assert_not_called()


def test_report_disconnect(mock_emit_session_update, solo_two_world_session):
    log = MagicMock()
    session_dict = {"user-id": 1234, "worlds": [1]}
    a1 = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    a1.connection_state = GameConnectionStatus.InGame
    a1.save()

    # Run
    world_api.report_disconnect(MagicMock(), session_dict, log)

    # Assert
    a1 = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    assert a1.connection_state == GameConnectionStatus.Disconnected
    mock_emit_session_update.assert_called_once_with(database.MultiplayerSession.get_by_id(1))


def test_emit_inventory_room(solo_two_world_session):
    sa = MagicMock()
    sa.is_room_not_empty.return_value = True

    world = database.World.get_by_id(1)

    # Run
    world_api.emit_inventory_update(sa, world, 1234, b"foo")

    # Assert
    sa.sio.emit.assert_called_once_with(
        signals.WORLD_BINARY_INVENTORY,
        (str(world.uuid), 1234, b"foo"),
        to=f"multiplayer-{world.uuid}-1234-inventory",
        namespace="/",
        include_self=True,
    )
