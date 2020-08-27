import json
from unittest.mock import MagicMock, PropertyMock, patch

import peewee
import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.server import game_session, database


def test_setup_app():
    game_session.setup_app(MagicMock())


def test_list_game_sessions(clean_database):
    # Setup
    database.GameSession.create(name="Debug", num_teams=1)
    database.GameSession.create(name="Other", num_teams=2)
    # Run
    result = game_session.list_game_sessions(MagicMock())
    # Assert
    assert result == [
        {'has_password': False, 'id': 1, 'in_game': False, 'name': 'Debug', 'num_players': 0},
        {'has_password': False, 'id': 2, 'in_game': False, 'name': 'Other', 'num_players': 0},
    ]


def test_create_game_session(clean_database, preset_manager):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    result = game_session.create_game_session(sio, "My Room")

    # Assert
    session = database.GameSession.get(1)
    assert session.name == "My Room"
    assert result == {
        'id': 1,
        'in_game': False,
        'name': 'My Room',
        'num_teams': 1,
        'players': [{'admin': True, 'id': 1234, 'name': 'The Name', 'row': 0, 'team': 0}],
        'presets': [preset_manager.default_preset.as_json],
        'seed_hash': None,
        'spoiler': None,
        'word_hash': None
    }


@patch("randovania.server.game_session._emit_session_update", autospec=True)
def test_join_game_session(mock_emit_session_update: MagicMock,
                           clean_database):
    # Setup
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    session = database.GameSession.create(name="The Session", password=None, num_teams=1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user2, session=session, row=0, team=0, admin=True)

    # Run
    result = game_session.join_game_session(sio, 1, None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert result == {
        'id': 1,
        'in_game': False,
        'name': 'The Session',
        'num_teams': 1,
        'players': [
            {'admin': True, 'id': 1235, 'name': 'Other Name', 'row': 0, 'team': 0},
            {'admin': False, 'id': 1234, 'name': 'The Name', 'row': 0, 'team': None},
        ],
        'presets': [{}],
        'seed_hash': None,
        'spoiler': None,
        'word_hash': None
    }


def test_game_session_request_pickups_missing_membership(clean_database):
    with pytest.raises(peewee.DoesNotExist):
        game_session.game_session_request_pickups(MagicMock(), 1)


def test_game_session_request_pickups_not_in_game(flask_app, clean_database):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    session = database.GameSession.create(name="Debug", num_teams=1)
    database.GameSessionMembership.create(
        user=user, session=session,
        row=0, team=0, admin=False)

    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    result = game_session.game_session_request_pickups(sio, 1)

    # Assert
    assert result == []


@pytest.fixture(name="two_player_session")
def two_player_session_fixture(clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")

    session = database.GameSession.create(id=1, name="Debug", in_game=True, num_teams=1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")

    database.GameSessionMembership.create(user=user1, session=session, row=0, team=0, admin=False)
    database.GameSessionMembership.create(user=user2, session=session, row=1, team=0, admin=False)
    database.GameSessionTeamAction.create(session=session, team=0,
                                          provider_row=1, provider_location_index=0, receiver_row=0)

    return session


@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.game_session._get_resource_database", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_request_pickups_one_action(mock_session_description: PropertyMock,
                                                 mock_get_resource_database: MagicMock,
                                                 mock_get_pickup_target: MagicMock,
                                                 flask_app, two_player_session, echoes_resource_database):
    # Setup
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    pickup = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY,
                         (
                             ConditionalResources(None, None, ((echoes_resource_database.item[0], 1),)),
                         ))
    mock_get_pickup_target.return_value = PickupTarget(pickup=pickup, player=0)
    mock_get_resource_database.return_value = echoes_resource_database

    # Run
    result = game_session.game_session_request_pickups(sio, 1)

    # Assert
    mock_get_resource_database.assert_called_once_with(mock_session_description.return_value, 0)
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 1, 0)
    assert result == [{'message': 'Received A from Other Name', 'pickup': '0pth(AO'}]


@patch("flask_socketio.emit", autospec=True)
@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.game_session._get_resource_database", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_collect_pickup_for_self(mock_session_description: PropertyMock,
                                              mock_get_resource_database: MagicMock,
                                              mock_get_pickup_target: MagicMock,
                                              mock_emit: MagicMock,
                                              flask_app, two_player_session, echoes_resource_database):
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    pickup = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY,
                         (
                             ConditionalResources(None, None, ((echoes_resource_database.item[0], 1),)),
                         ))
    mock_get_resource_database.return_value = echoes_resource_database
    mock_get_pickup_target.return_value = PickupTarget(pickup, 0)

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_collect_pickup(sio, 1, 0)

    # Assert
    assert result == "0pth(AO"
    mock_emit.assert_not_called()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.GameSessionTeamAction.get(session=two_player_session, team=0, provider_row=0,
                                           provider_location_index=0)


@patch("flask_socketio.emit", autospec=True)
@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_collect_pickup_etm(mock_session_description: PropertyMock,
                                         mock_get_pickup_target: MagicMock,
                                         mock_emit: MagicMock,
                                         flask_app, two_player_session, echoes_resource_database):
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    mock_get_pickup_target.return_value = None

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_collect_pickup(sio, 1, 0)

    # Assert
    assert result is None
    mock_emit.assert_not_called()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.GameSessionTeamAction.get(session=two_player_session, team=0, provider_row=0,
                                           provider_location_index=0)


@pytest.mark.parametrize("already_exists", [False, True])
@patch("flask_socketio.emit", autospec=True)
@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_collect_pickup_other(mock_session_description: PropertyMock,
                                           mock_get_pickup_target: MagicMock,
                                           mock_emit: MagicMock,
                                           flask_app, two_player_session, echoes_resource_database,
                                           already_exists):
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)
    mock_get_pickup_target.return_value = PickupTarget(MagicMock(), 1)

    if already_exists:
        database.GameSessionTeamAction.create(session=two_player_session, team=0, provider_row=0,
                                              provider_location_index=0, receiver_row=0)

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_collect_pickup(sio, 1, 0)

    # Assert
    assert result is None
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    database.GameSessionTeamAction.get(session=two_player_session, team=0, provider_row=0,
                                       provider_location_index=0)
    if already_exists:
        mock_emit.assert_not_called()
    else:
        mock_emit.assert_called_once_with("game_has_update", {"session": 1, "team": 0, "row": 1, },
                                          room=f"game-session-1-1235")


@pytest.mark.parametrize("target_team", [1, 2, 3])
@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_player_switch_team(mock_emit_session_update: MagicMock,
                                               clean_database, flask_app,
                                               target_team: int):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=True, num_teams=3)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=0, team=0, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        if target_team < 3:
            game_session.game_session_admin_player(sio, 1, 1234, "switch_team", target_team)
        else:
            game_session.game_session_admin_player(sio, 1, 1234, "switch_to_new_team", None)

    # Assert
    membership = database.GameSessionMembership.get(user=user1, session=session, row=0)
    assert membership.team == target_team
    assert database.GameSession.get_by_id(1).num_teams == target_team + 1
    mock_emit_session_update.assert_called_once()


@pytest.mark.parametrize("offset", [-1, 1])
@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_player_move(mock_emit_session_update: MagicMock,
                                        clean_database, flask_app,
                                        offset: int):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=True, num_teams=1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionPreset.create(session=session, row=2, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=1, team=0, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_player(sio, 1, 1234, "move", offset)

    # Assert
    membership = database.GameSessionMembership.get(user=user1, session=session, team=0)
    assert membership.row == 1 + offset
    mock_emit_session_update.assert_called_once()


@patch("randovania.games.prime.patcher_file.create_patcher_file", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_admin_player_patcher_file(mock_layout_description: PropertyMock,
                                                mock_create_patcher_file: MagicMock,
                                                clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Brother")
    session = database.GameSession.create(id=1, name="Debug", in_game=True, num_teams=1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionPreset.create(session=session, row=2, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=2, team=0, admin=False)
    database.GameSessionMembership.create(user=user2, session=session, row=1, team=0, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    cosmetic = CosmeticPatches(open_map=False)

    # Run
    result = game_session.game_session_admin_player(sio, 1, 1234, "create_patcher_file", cosmetic.as_json)

    # Assert
    mock_create_patcher_file.assert_called_once_with(
        mock_layout_description.return_value,
        PlayersConfiguration(2, {
            0: "Player 1",
            1: "Brother",
            2: "The Name",
        }),
        cosmetic
    )
    assert result is mock_create_patcher_file.return_value


@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_session_create_row(mock_emit_session_update: MagicMock,
                                               clean_database, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False, num_teams=1)
    database.GameSessionMembership.create(user=user1, session=session, row=2, team=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    game_session.game_session_admin_session(sio, 1, "create_row", preset_manager.default_preset.as_json)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).num_rows == 1


@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_session_delete_row(mock_emit_session_update: MagicMock,
                                               clean_database, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False, num_teams=1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=2, team=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    game_session.game_session_admin_session(sio, 1, "delete_row", 1)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).num_rows == 1


@patch("randovania.layout.layout_description.LayoutDescription.from_json_dict")
@patch("randovania.server.game_session._emit_session_update", autospec=True)
def test_game_session_admin_session_change_layout_description(mock_emit_session_update: MagicMock,
                                                              mock_from_json_dict: MagicMock,
                                                              clean_database, preset_manager):
    preset_as_json = json.dumps(preset_manager.default_preset.as_json)
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False, num_teams=1)
    database.GameSessionPreset.create(session=session, row=0, preset=preset_as_json)
    database.GameSessionPreset.create(session=session, row=1, preset=preset_as_json)
    database.GameSessionMembership.create(user=user1, session=session, row=2, team=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    layout_description = mock_from_json_dict.return_value
    layout_description.as_json = "some_json_string"
    layout_description.permalink.presets = {i: preset_manager.default_preset for i in (0, 1)}

    # Run
    game_session.game_session_admin_session(sio, 1, "change_layout_description", "layout_description_json")

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).layout_description_json == '"some_json_string"'
