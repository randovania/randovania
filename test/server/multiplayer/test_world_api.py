import uuid
from unittest.mock import MagicMock, PropertyMock, call, ANY

import peewee
import pytest
from frozendict import frozendict
from pytest_mock import MockerFixture

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.world_sync import ServerSyncRequest, ServerWorldSync, ServerSyncResponse, \
    ServerWorldResponse
from randovania.server import database
from randovania.server.multiplayer import world_api


def test_emit_world_pickups_update_not_in_game(flask_app, clean_database, mocker):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    session = database.MultiplayerSession.create(name="Debug", creator=user)
    world = database.World.create(session=session, name="W1", preset="{}")
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    world_api.emit_world_pickups_update(sio, world)

    # Assert
    mock_emit.assert_not_called()


def test_emit_world_pickups_update_one_action(
        flask_app, two_player_session, generic_pickup_category,
        default_generator_params,
        echoes_resource_database, mocker
):
    # Setup
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock)
    mock_get_resource_database: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_resource_database", autospec=True)
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True
    )

    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    w1 = database.World.get_by_id(1)

    pickup = PickupEntry("A", PickupModel(echoes_resource_database.game_enum, "AmmoModel"),
                         generic_pickup_category, generic_pickup_category,
                         progression=((echoes_resource_database.item[0], 1),),
                         generator_params=default_generator_params)
    mock_get_pickup_target.return_value = PickupTarget(pickup=pickup, player=0)
    mock_get_resource_database.return_value = echoes_resource_database

    # Run
    world_api.emit_world_pickups_update(sio, w1)

    # # Uncomment this to encode the data once again and get the new bytefield if it changed for some reason
    # from randovania.server.game_session import _base64_encode_pickup
    # new_data = _base64_encode_pickup(pickup, echoes_resource_database)
    # assert new_data == b""

    # Assert
    mock_get_resource_database.assert_called_once_with(mock_session_description.return_value, 0)
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 1, 0)
    mock_emit.assert_called_once_with(
        "world_pickups_update",
        {
            "game": "prime2",
            "pickups": [{
                'provider_name': 'World 2',
                'pickup': ('C?gdGwY9x9y^)o&8#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rr'
                           'mqu378#^m=E0aqcz^Lr4%&tu=WC<>et)vKSE{v@0?oTa+xPo8@R_8YcRyLMqmR3Rrmqu35fdzm')
            }],
            "world": "1179c986-758a-4170-9b07-fe4541d78db0"
        },
        room=f"world-1179c986-758a-4170-9b07-fe4541d78db0"
    )


def test_game_session_collect_pickup_for_self(
        flask_app, two_player_session, generic_pickup_category,
        default_generator_params, echoes_resource_database, mocker
):
    # Setup
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")
    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock)
    mock_get_resource_database: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_resource_database", autospec=True)
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True
    )

    w1 = database.World.get_by_id(1)

    pickup = PickupEntry("A", 1, generic_pickup_category, generic_pickup_category,
                         progression=((echoes_resource_database.item[0], 1),),
                         generator_params=default_generator_params)
    mock_get_resource_database.return_value = echoes_resource_database
    mock_get_pickup_target.return_value = PickupTarget(pickup, 0)

    # Run
    with flask_app.test_request_context():
        result = world_api.collect_locations(sio, w1, (0,))

    # Assert
    assert result == set()
    mock_emit.assert_not_called()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.WorldAction.get(provider=w1, location=0)


def test_game_session_collect_pickup_etm(
        flask_app, two_player_session, echoes_resource_database, mocker
):
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")
    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock)
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True
    )

    mock_get_pickup_target.return_value = None
    w1 = database.World.get_by_id(1)

    # Run
    with flask_app.test_request_context():
        result = world_api.collect_locations(sio, w1, (0,))

    # Assert
    assert result == set()
    mock_emit.assert_not_called()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.WorldAction.get(provider=w1, location=0)


@pytest.mark.parametrize(("locations_to_collect", "exists"), [
    ((0,), ()),
    ((0,), (0,)),
    ((0, 1), ()),
    ((0, 1), (0,)),
    ((0, 1), (0, 1)),
])
def test_collect_locations_other(flask_app, two_player_session, echoes_resource_database,
                                           locations_to_collect, exists, mocker):
    mock_get_pickup_target: MagicMock = mocker.patch(
        "randovania.server.multiplayer.world_api._get_pickup_target", autospec=True)
    mock_session_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock)
    mock_emit_session_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_actions_update", autospec=True)

    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)
    mock_get_pickup_target.return_value = PickupTarget(MagicMock(), 1)

    w1 = database.World.get_by_id(1)
    w2 = database.World.get_by_id(2)

    for existing_id in exists:
        database.WorldAction.create(
            provider=w1, location=existing_id,
            session=two_player_session, receiver=w2,
        )

    # Run
    with flask_app.test_request_context():
        result = world_api.collect_locations(sio, w1, locations_to_collect)

    # Assert
    mock_get_pickup_target.assert_has_calls([
        call(mock_session_description.return_value, 0, location)
        for location in locations_to_collect
    ])
    for location in locations_to_collect:
        database.WorldAction.get(provider=w1, location=location)

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
    mock_emit_inventory = mocker.patch("randovania.server.multiplayer.session_common.emit_inventory_update")

    sio = MagicMock()
    user = database.User.get_by_id(1234)
    sio.get_current_user.return_value = user

    w1 = database.World.get_by_id(1)
    w2 = database.World.get_by_id(2)
    session = database.MultiplayerSession.get_by_id(solo_two_world_session.id)

    request = ServerSyncRequest(
        worlds=frozendict({
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
        })
    )

    # Run
    with flask_app.test_request_context():
        result = world_api.world_sync(sio, request)

    # Assert
    assert result == ServerSyncResponse(
        worlds=frozendict({
            w1.uuid: ServerWorldResponse(
                world_name=w1.name,
                session=session.create_list_entry(user),
            ),
        }),
        errors=frozendict({
            uuid.UUID("a0cf12f7-8a0e-47ed-9a82-cabfc8b912c2"): error.WorldDoesNotExistError(),
        }),
    )

    a1 = database.WorldUserAssociation.get_by_instances(world=w1, user=1234)
    assert a1.connection_state == GameConnectionStatus.InGame
    assert a1.inventory == b"foo"
    a2 = database.WorldUserAssociation.get_by_instances(world=w2, user=1234)
    assert a2.connection_state == GameConnectionStatus.Disconnected
    assert a2.inventory is None

    sio.store_world_in_session.assert_called_once_with(w1)
    sio.ensure_in_room.assert_called_once_with("world-1179c986-758a-4170-9b07-fe4541d78db0")
    mock_leave_room.assert_called_once_with("world-6b5ac1a1-d250-4f05-a5fb-ae37e8a92165")
    mock_emit_pickups.assert_has_calls([call(sio, w1), call(sio, w2)], any_order=True)
    mock_emit_session_update.assert_called_once_with(session)
    mock_emit_actions.assert_called_once_with(session)
    mock_emit_inventory.assert_called_once_with(a1)
    mock_emit.assert_not_called()


def test_report_disconnect(mock_emit_session_update, solo_two_world_session):
    log = MagicMock()
    session_dict = {
        "user-id": 1234,
        "worlds": [1]
    }
    a1 = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    a1.connection_state = GameConnectionStatus.InGame
    a1.save()

    # Run
    world_api.report_disconnect(MagicMock(), session_dict, log)

    # Assert
    a1 = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    assert a1.connection_state == GameConnectionStatus.Disconnected
    mock_emit_session_update.assert_called_once_with(database.MultiplayerSession.get_by_id(1))
