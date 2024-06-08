from __future__ import annotations

import contextlib
import dataclasses
import itertools
import json
import re
import uuid
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, PropertyMock, call

import peewee
import pytest

from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import InvalidLayoutDescription
from randovania.network_common import error
from randovania.network_common.admin_actions import SessionAdminGlobalAction, SessionAdminUserAction
from randovania.network_common.multiplayer_session import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database
from randovania.server.multiplayer import session_admin
from randovania.server.server_app import ServerApp

if TYPE_CHECKING:
    import pytest_mock


@pytest.mark.usefixtures("_mock_seed_hash")
def test_admin_player_kick_last(solo_two_world_session, flask_app, mocker, mock_audit):
    mock_emit = mocker.patch("flask_socketio.emit")

    user = database.User.get_by_id(1234)
    sa = MagicMock()
    sa.get_current_user.return_value = user

    session = database.MultiplayerSession.get_by_id(1)

    # Run
    with flask_app.test_request_context():
        session_admin.admin_player(sa, 1, 1234, SessionAdminUserAction.KICK.value)

    # Assert
    for table in [database.MultiplayerSession, database.World, database.MultiplayerMembership, database.WorldAction]:
        assert list(table.select()) == []
    assert database.User.get_by_id(1234) == user

    mock_emit.assert_called_once_with(
        "multiplayer_session_meta_update",
        {
            "id": 1,
            "name": "Debug",
            "visibility": "visible",
            "users_list": [],
            "worlds": [],
            "game_details": {"seed_hash": "XXXXXXXX", "spoiler": True, "word_hash": "Some Words"},
            "generation_in_progress": None,
            "allowed_games": ANY,
            "allow_coop": False,
            "allow_everyone_claim_world": False,
        },
        room="multiplayer-session-1",
        namespace="/",
    )
    mock_audit.assert_called_once_with(sa, session, "Left session")


def test_admin_player_kick_member(two_player_session, flask_app, mocker, mock_audit):
    mock_emit = mocker.patch("flask_socketio.emit")

    user = database.User.get_by_id(1234)
    sa = MagicMock()
    sa.get_current_user.return_value = user

    session = database.MultiplayerSession.get_by_id(1)

    # Run
    with flask_app.test_request_context():
        session_admin.admin_player(sa, 1, 1235, SessionAdminUserAction.KICK.value, None)

    # Assert
    assert database.User.get_by_id(1234) == user
    assert database.User.get_by_id(1235) is not None
    assert database.World.select().where(database.World.session == session).count() == 2
    assert database.MultiplayerMembership.select().where(database.MultiplayerMembership.session == session).count() == 1

    mock_emit.assert_called_once_with(
        "multiplayer_session_meta_update",
        {
            "id": 1,
            "name": "Debug",
            "visibility": "visible",
            "users_list": [
                {
                    "admin": True,
                    "id": 1234,
                    "name": "The Name",
                    "ready": False,
                    "worlds": {
                        "1179c986-758a-4170-9b07-fe4541d78db0": {
                            "connection_state": "disconnected",
                            "last_activity": "2021-09-01 10:20:00+00:00",
                        }
                    },
                }
            ],
            "worlds": [
                {"id": "1179c986-758a-4170-9b07-fe4541d78db0", "name": "World 1", "preset_raw": "{}"},
                {"id": "6b5ac1a1-d250-4f05-a5fb-ae37e8a92165", "name": "World 2", "preset_raw": "{}"},
            ],
            "game_details": None,
            "generation_in_progress": None,
            "allowed_games": ANY,
            "allow_coop": False,
            "allow_everyone_claim_world": False,
        },
        room="multiplayer-session-1",
        namespace="/",
    )
    mock_audit.assert_called_once_with(sa, session, "Kicked Other Name")


def test_admin_player_create_world_for(
    mock_emit_session_update: MagicMock, mock_audit, clean_database, flask_app, preset_manager
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        dev_features=RandovaniaGame.BLANK.value,
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        session_admin.admin_player(
            sa,
            1,
            1234,
            SessionAdminUserAction.CREATE_WORLD_FOR.value,
            "New World",
            preset_manager.default_preset.as_bytes(),
        )

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    worlds: list[database.World] = list(database.World.select())
    assert len(worlds) == 1
    assert worlds[0].name == "New World"
    mock_audit.assert_has_calls(
        [
            call(sa, session, "Created new world New World"),
            call(sa, session, "Associated new world New World for The Name"),
        ]
    )


def test_admin_player_claim(flask_app, two_player_session, mock_audit, mock_emit_session_update):
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)

    w3 = database.World.create(
        session=two_player_session,
        name="World 3",
        preset="{}",
        order=2,
        uuid=uuid.UUID("6b5ac1a1-d250-4f05-0000-ae37e8a92165"),
    )

    # Run
    with flask_app.test_request_context():
        session_admin.admin_player(sa, 1, 1234, SessionAdminUserAction.CLAIM.value, str(w3.uuid))

    assert database.WorldUserAssociation.get_by_ids(user_id=1234, world_uid=w3.uuid)
    mock_emit_session_update.assert_called_once_with(two_player_session)
    mock_audit.assert_called_once_with(sa, two_player_session, "Associated world World 3 for The Name")


def test_admin_player_unclaim(flask_app, two_player_session, mock_audit, mock_emit_session_update):
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)

    # Run
    with flask_app.test_request_context():
        session_admin.admin_player(
            sa, 1, 1234, SessionAdminUserAction.UNCLAIM.value, "1179c986-758a-4170-9b07-fe4541d78db0"
        )

    with pytest.raises(peewee.DoesNotExist):
        assert database.WorldUserAssociation.get_by_ids(
            user_id=1234, world_uid=uuid.UUID("1179c986-758a-4170-9b07-fe4541d78db0")
        )
    mock_emit_session_update.assert_called_once_with(two_player_session)
    mock_audit.assert_called_once_with(sa, two_player_session, "Unassociated world World 1 from The Name")


def test_admin_player_switch_admin(flask_app, two_player_session, mock_audit, mock_emit_session_update):
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)

    assert not database.MultiplayerMembership.get_by_ids(user_id=1235, session_id=1).admin

    # Run
    with flask_app.test_request_context():
        session_admin.admin_player(sa, 1, 1235, SessionAdminUserAction.SWITCH_ADMIN.value)

    assert database.MultiplayerMembership.get_by_ids(user_id=1235, session_id=1).admin
    mock_audit.assert_called_once_with(sa, two_player_session, "Made Other Name an admin")
    mock_emit_session_update.assert_called_once_with(two_player_session)


def test_admin_session_patcher_file(flask_app, mock_audit, mocker, two_player_session):
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1235)
    w2 = database.World.get_by_id(2)

    mock_layout_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock
    )
    game = mock_layout_description.return_value.get_preset.return_value.game
    game.data.layout.cosmetic_patches = EchoesCosmeticPatches

    cosmetic = EchoesCosmeticPatches(open_map=False)

    # Run
    with flask_app.test_request_context():
        result = session_admin.admin_session(
            sa, 1, SessionAdminGlobalAction.CREATE_PATCHER_FILE.value, str(w2.uuid), cosmetic.as_json
        )

    # Assert
    mock_layout_description.return_value.get_preset.assert_called_once_with(1)
    game.patch_data_factory.assert_called_once_with(
        mock_layout_description.return_value,
        PlayersConfiguration(
            1,
            {
                0: "World 1",
                1: "World 2",
            },
            {
                0: uuid.UUID("1179c986-758a-4170-9b07-fe4541d78db0"),
                1: uuid.UUID("6b5ac1a1-d250-4f05-a5fb-ae37e8a92165"),
            },
            two_player_session.name,
        ),
        cosmetic,
    )
    assert result is game.patch_data_factory.return_value.create_data.return_value
    mock_audit.assert_called_once_with(sa, two_player_session, "Exporting game named World 2")


def test_admin_session_patcher_file_not_associated(flask_app, two_player_session):
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)
    w2 = database.World.get_by_id(2)

    # Run
    with flask_app.test_request_context(), pytest.raises(error.NotAuthorizedForActionError):
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.CREATE_PATCHER_FILE.value, str(w2.uuid), {})


def test_admin_session_delete_session(mock_emit_session_update: MagicMock, flask_app, clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.DELETE_SESSION.value)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert list(database.MultiplayerSession.select()) == []


def test_admin_session_create_world(
    mock_emit_session_update: MagicMock, mock_audit, clean_database, flask_app, preset_manager
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        dev_features=RandovaniaGame.BLANK.value,
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(
            sa, 1, SessionAdminGlobalAction.CREATE_WORLD.value, "New World", preset_manager.default_preset.as_bytes()
        )

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    worlds: list[database.World] = list(database.World.select())
    assert len(worlds) == 1
    assert worlds[0].name == "New World"
    mock_audit.assert_called_once_with(sa, session, "Created new world New World")


@pytest.mark.parametrize("reason", ["bad_name", "already_exists", "wrong_preset"])
def test_admin_session_create_world_bad(
    mock_emit_session_update: MagicMock, mock_audit, clean_database, flask_app, preset_manager, reason, mocker
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    old_world = database.World.create(session=session, name="New World", preset="{}")

    allowed_games = [RandovaniaGame.BLANK]
    mocker.patch(
        "randovania.server.database.MultiplayerSession.allowed_games",
        return_value=allowed_games,
        new_callable=PropertyMock,
    )

    preset = preset_manager.default_preset
    if reason == "bad_name":
        new_name = "New####,World"
        match = "Invalid world name"
    elif reason == "already_exists":
        new_name = "New World"
        match = "World name already exists"
    else:
        new_name = "New World"
        match = "Blank Development Game not allowed"
        allowed_games.clear()

    # Run
    with flask_app.test_request_context(), pytest.raises(error.InvalidActionError, match=match):
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.CREATE_WORLD.value, new_name, preset.as_bytes())

    # Assert
    mock_emit_session_update.assert_not_called()
    assert list(database.World.select()) == [old_world]
    mock_audit.assert_not_called()


@pytest.mark.parametrize("association", ["no", "yes", "admin"])
def test_admin_session_change_world(
    mock_emit_session_update: MagicMock,
    mock_audit,
    blank_available_in_multi,
    clean_database,
    flask_app,
    preset_manager,
    association,
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    w1 = database.World.create(session=session, name="W1", preset="{}")
    database.World.create(session=session, name="W2", preset="{}")
    database.MultiplayerMembership.create(user=user1, session=session, admin=association == "admin")
    sa = MagicMock(spec=ServerApp)
    sa.get_current_user.return_value = user1

    if association == "no":
        context = pytest.raises(error.NotAuthorizedForActionError)
    elif not blank_available_in_multi:
        context = pytest.raises(
            error.InvalidActionError, match=re.escape("Invalid Action: Blank Development Game not allowed.")
        )
    else:
        context = contextlib.nullcontext()

    if association == "yes":
        database.WorldUserAssociation.create(world=w1, user=user1)

    # Make sure the preset is using the latest version
    preset_manager.default_preset.ensure_converted()

    # Run
    with flask_app.test_request_context(), context:
        session_admin.admin_session(
            sa, 1, SessionAdminGlobalAction.CHANGE_WORLD.value, str(w1.uuid), preset_manager.default_preset.as_bytes()
        )

    new_preset_row = database.World.get_by_id(w1.id)
    # Assert
    if association == "no" or not blank_available_in_multi:
        mock_emit_session_update.assert_not_called()
        assert new_preset_row.preset == "{}"
        mock_audit.assert_not_called()
    else:
        mock_emit_session_update.assert_called_once_with(session)
        assert json.loads(new_preset_row.preset) == preset_manager.default_preset.as_json
        mock_audit.assert_called_once_with(sa, session, f"Changing world {w1.name}")


@pytest.mark.parametrize("already_exists", [False, True])
@pytest.mark.parametrize("valid_name", [False, True])
def test_admin_session_rename_world(
    mock_emit_session_update: MagicMock, mock_audit, clean_database, flask_app, valid_name, already_exists
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    w1 = database.World.create(session=session, name="W1", preset="{}")
    database.World.create(session=session, name="W2", preset="{}")
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock(spec=ServerApp)
    sa.get_current_user.return_value = user1

    if valid_name:
        new_name = "TheNewName"
        if already_exists:
            database.World.create(session=session, name=new_name, preset="{}")
            context = pytest.raises(error.InvalidActionError, match="World name already exists")
        else:
            context = contextlib.nullcontext()
    else:
        context = pytest.raises(error.InvalidActionError, match="Invalid world name")
        new_name = "TheNew,?/1#Name"

    # Run
    with flask_app.test_request_context(), context:
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.RENAME_WORLD.value, str(w1.uuid), new_name)

    world_after = database.World.get_by_id(w1.id)
    # Assert
    if valid_name and not already_exists:
        mock_emit_session_update.assert_called_once_with(session)
        assert world_after.name == new_name
        mock_audit.assert_called_once_with(sa, session, f"Renaming world W1 to {new_name}")
    else:
        mock_emit_session_update.assert_not_called()
        assert world_after.name == "W1"
        mock_audit.assert_not_called()


@pytest.mark.parametrize("association", ["no", "yes", "admin"])
def test_admin_session_delete_world(
    mock_emit_session_update: MagicMock, mock_audit, clean_database, flask_app, preset_manager, association
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    w1 = database.World.create(session=session, name="W1", preset="{}")
    database.World.create(session=session, name="W2", preset="{}")
    database.MultiplayerMembership.create(user=user1, session=session, admin=association == "admin")
    sa = MagicMock(spec=ServerApp)
    sa.get_current_user.return_value = user1

    if association == "no":
        context = pytest.raises(error.NotAuthorizedForActionError)
    else:
        context = contextlib.nullcontext()

    if association == "yes":
        database.WorldUserAssociation.create(world=w1, user=user1)

    # Run
    with flask_app.test_request_context(), context:
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.DELETE_WORLD.value, str(w1.uuid))

    # Assert
    world_count = database.World.select().count()

    if association == "no":
        mock_emit_session_update.assert_not_called()
        assert world_count == 2
        mock_audit.assert_not_called()
    else:
        mock_emit_session_update.assert_called_once_with(session)
        assert world_count == 1
        mock_audit.assert_called_once_with(sa, session, f"Deleting world {w1.name}")


def test_admin_session_delete_world_missing(clean_database, flask_app):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1
    uid = "ffa5bf78-21f5-45af-96e6-f2c025a9ead2"

    context = pytest.raises(error.WorldDoesNotExistError)

    # Run
    with flask_app.test_request_context(), context:
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.DELETE_WORLD.value, uid)

    # Assert
    assert database.World.select().count() == 0


@pytest.mark.parametrize("case", ["to_false", "to_true_free", "to_true_busy"])
def test_admin_session_update_layout_generation(mock_emit_session_update: MagicMock, clean_database, flask_app, case):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        generation_in_progress=user2 if case == "to_true_busy" else None,
    )
    w1 = database.World.create(
        session=session, name="W1", preset="{}", uuid=uuid.UUID("00000000-0000-0000-0000-000000000000")
    )
    w2 = database.World.create(
        session=session, name="W2", preset="{}", uuid=uuid.UUID("00000000-0000-0000-0000-000000000001")
    )
    w3 = database.World.create(
        session=session, name="W3", preset="{}", uuid=uuid.UUID("00000000-0000-0000-0000-000000000002")
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    order = [str(w.uuid) for w in [w2, w1, w3]]
    expected_order = {w.name: None for w in [w1, w2, w3]}

    if case == "to_true_busy":
        expectation = pytest.raises(error.InvalidActionError, match="Generation already in progress by Other.")
        expected_user = user2
    else:
        expectation = contextlib.nullcontext()
        if case == "to_false":
            expected_user = None
            order = []
        else:
            expected_user = user1
            expected_order = {
                "W1": 1,
                "W2": 0,
                "W3": 2,
            }

    # Run
    with expectation, flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION.value, order)

    # Assert
    if case == "to_true_busy":
        mock_emit_session_update.assert_not_called()
    else:
        mock_emit_session_update.assert_called_once_with(session)

    assert database.MultiplayerSession.get_by_id(1).generation_in_progress == expected_user
    worlds = {w.name: w.order for w in database.World.select()}
    assert worlds == expected_order


def test_admin_session_change_layout_description(
    clean_database, preset_manager, mock_emit_session_update, mocker, flask_app, mock_audit
):
    mock_verify_no_layout_description = mocker.patch(
        "randovania.server.multiplayer.session_admin._verify_no_layout_description", autospec=True
    )
    mock_emit_session_actions_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_actions_update", autospec=True
    )
    mock_from_json_dict: MagicMock = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_bytes")

    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES)
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1, generation_in_progress=user1
    )
    database.World.create_for(session=session, name="W1", preset=preset, order=0)
    database.World.create_for(session=session, name="W2", preset=preset, order=1)
    database.MultiplayerMembership.create(user=user1, session=session, row=None, admin=True)

    new_preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).get_preset()
    assert isinstance(new_preset.configuration, EchoesConfiguration)
    new_preset = dataclasses.replace(
        new_preset, configuration=dataclasses.replace(new_preset.configuration, menu_mod=False)
    )

    sa = MagicMock()
    sa.get_current_user.return_value = user1
    layout_description = mock_from_json_dict.return_value
    layout_description.as_binary.return_value = b"OUR_ENCODED_LAYOUT"
    layout_description.world_count = 2
    layout_description.all_presets = [new_preset, new_preset]
    layout_description.shareable_word_hash = "Hash Words"
    layout_description.shareable_hash = "ASDF"
    layout_description.has_spoiler = True

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(
            sa, 1, SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION.value, b"layout_description_json"
        )

    # Assert
    mock_emit_session_actions_update.assert_called_once_with(session)
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sa, session, "Set game to Hash Words")
    mock_verify_no_layout_description.assert_called_once_with(session)
    layout_description.as_binary.assert_called_once_with(force_spoiler=True, include_presets=False)

    session_mod = database.MultiplayerSession.get_by_id(1)
    assert session_mod.layout_description_json == b"OUR_ENCODED_LAYOUT"
    assert session_mod.generation_in_progress is None
    assert session_mod.game_details_json == '{"seed_hash": "ASDF", "word_hash": "Hash Words", "spoiler": true}'


def test_admin_session_remove_layout_description(
    mock_emit_session_update: MagicMock, clean_database, flask_app, mock_audit, mocker: pytest_mock.MockerFixture
):
    mock_emit_session_actions_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_actions_update", autospec=True
    )

    original_uid = uuid.UUID("6b5ac1a1-d250-4f05-0000-ae37e8a92165")
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        generation_in_progress=user1,
        layout_description_json="layout_description_json",
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    database.World.create(session=session, name="W1", preset="{}", uuid=original_uid)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION.value, None)

    # Assert
    mock_emit_session_actions_update.assert_called_once_with(session)
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sa, session, "Removed generated game")
    assert database.MultiplayerSession.get_by_id(1).layout_description_json is None
    assert database.MultiplayerSession.get_by_id(1).generation_in_progress is None
    assert database.World.get_by_id(1).uuid != original_uid


@pytest.mark.parametrize("other_user", [False, True])
def test_admin_session_change_layout_description_invalid(
    mock_emit_session_update: MagicMock, clean_database, other_user, flask_app
):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        generation_in_progress=user2 if other_user else None,
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    if other_user:
        expected_message = "Waiting for a layout from Other."
    else:
        expected_message = "Not waiting for a layout."

    # Run
    with pytest.raises(error.InvalidActionError, match=expected_message), flask_app.test_request_context():
        session_admin.admin_session(
            sa, 1, SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION.value, "layout_description_json"
        )

    # Assert
    mock_emit_session_update.assert_not_called()
    assert database.MultiplayerSession.get_by_id(1).layout_description_json is None


@pytest.mark.parametrize("reason", ["layout", "preset"])
def test_admin_session_change_layout_description_invalid_layout(
    mock_emit_session_update: MagicMock, clean_database, flask_app, mocker, reason
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        generation_in_progress=user1,
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    from_bytes = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_bytes")
    if reason == "layout":
        expected_message = "Invalid layout: "
        from_bytes.side_effect = InvalidLayoutDescription()
    else:
        expected_message = "Presets do not match layout"
        from_bytes.side_effect = ValueError()
    # Run
    with pytest.raises(error.InvalidActionError, match=expected_message), flask_app.test_request_context():
        session_admin._change_layout_description(sa, session, b"layout_description_json")


def test_admin_session_download_layout_description(
    flask_app, solo_two_world_session, mock_emit_session_update, mock_audit
):
    session = database.MultiplayerSession.get_by_id(1)
    sa = MagicMock(spec=ServerApp)
    sa.get_current_user.return_value = database.User.get_by_id(1234)

    # Run
    with flask_app.test_request_context():
        result = session_admin.admin_session(sa, 1, SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION.value)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_audit.assert_called_once_with(sa, session, "Requested the spoiler log")
    assert result == session.get_layout_description_as_binary()


def test_admin_session_download_layout_description_no_spoiler(
    clean_database, mock_emit_session_update, flask_app, mocker
):
    mock_layout_description: PropertyMock = mocker.patch(
        "randovania.server.database.MultiplayerSession.layout_description", new_callable=PropertyMock
    )
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        layout_description_json="layout_description_json",
        game_details_json=json.dumps(GameDetails(spoiler=False, word_hash="fun", seed_hash="fun").as_json),
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=False)
    sa = MagicMock(spec=ServerApp)
    sa.get_current_user.return_value = user1

    # Run
    with pytest.raises(error.InvalidActionError), flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION.value)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_layout_description.assert_not_called()


@pytest.mark.parametrize("old_visibility", [MultiplayerSessionVisibility.HIDDEN, MultiplayerSessionVisibility.VISIBLE])
@pytest.mark.parametrize("new_visibility", [MultiplayerSessionVisibility.HIDDEN, MultiplayerSessionVisibility.VISIBLE])
def test_admin_session_change_visibility(
    mock_emit_session_update, clean_database, preset_manager, flask_app, mock_audit, old_visibility, new_visibility
):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=old_visibility, creator=user1, layout_description_json="{}"
    )
    database.World.create(session=session, name="W1", preset="{}")
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.CHANGE_VISIBILITY.value, new_visibility)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sa, session, f"Changed visibility to {new_visibility.user_friendly_name}")
    assert database.MultiplayerSession.get_by_id(1).visibility == new_visibility


def test_admin_session_change_password(clean_database, mock_emit_session_update, flask_app, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1
    expected_password = "da92cfbc5e318c64e33dc1b0501e5db214cea0e2a5cecabf90269f32f8eaa15f"

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.CHANGE_PASSWORD.value, "the_password")

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sa, session, "Changed password")
    assert database.MultiplayerSession.get_by_id(1).password == expected_password


@pytest.mark.parametrize("valid_name", [False, True])
def test_admin_session_change_title(clean_database, mock_emit_session_update, flask_app, mock_audit, valid_name):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    if valid_name:
        context = contextlib.nullcontext()
        new_name = "new_name"
    else:
        context = pytest.raises(error.InvalidActionError, match="Invalid session name length")
        new_name = "new_name" * 10

    # Run
    with flask_app.test_request_context(), context:
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.CHANGE_TITLE.value, new_name)

    # Assert
    if valid_name:
        mock_emit_session_update.assert_called_once_with(session)
        mock_audit.assert_called_once_with(sa, session, "Changed name from Debug to new_name")
        assert database.MultiplayerSession.get_by_id(1).name == "new_name"
    else:
        mock_emit_session_update.assert_not_called()
        mock_audit.assert_not_called()
        assert database.MultiplayerSession.get_by_id(1).name == "Debug"


def test_admin_session_duplicate_session(clean_database, mock_emit_session_update, flask_app, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=2345, name="Other Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    database.World.create(session=session, name="W1", preset="{}")
    database.World.create(session=session, name="W2", preset='{"foo": 5}')
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    database.MultiplayerMembership.create(user=user2, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.DUPLICATE_SESSION.value, "new_name")

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_audit.assert_called_once_with(sa, session, "Duplicated session as new_name")
    new_session = database.MultiplayerSession.get_by_id(2)
    assert new_session.name == "new_name"
    assert [w.name for w in new_session.worlds] == ["W1", "W2"]
    assert [w.preset for w in new_session.worlds] == ["{}", '{"foo": 5}']
    assert [mem.user.name for mem in new_session.members] == ["The Name"]
    assert [a.message for a in new_session.audit_log] == ["Duplicated from Debug"]
    assert list(itertools.chain.from_iterable(w.associations for w in new_session.worlds)) == []


def test_admin_session_download_permalink(
    solo_two_world_session, mock_emit_session_update, flask_app, mock_audit, mocker
):
    assoc = database.MultiplayerMembership.get_by_ids(1234, 1)
    assoc.admin = True
    assoc.save()
    user1 = assoc.user

    sa = MagicMock()
    sa.get_current_user.return_value = user1
    mock_permalink: PropertyMock = mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.permalink", new_callable=PropertyMock
    )

    # Run
    with flask_app.test_request_context():
        result = session_admin.admin_session(sa, 1, SessionAdminGlobalAction.REQUEST_PERMALINK.value)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_audit.assert_called_once_with(sa, solo_two_world_session, "Requested permalink")
    assert result == mock_permalink.return_value.as_base64_str


def test_admin_session_download_permalink_no_layout(clean_database, mock_emit_session_update, flask_app, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context(), pytest.raises(error.InvalidActionError):
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.REQUEST_PERMALINK.value)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_audit.assert_not_called()


def test_verify_no_layout_description(clean_database, flask_app):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.MultiplayerSession.create(id=1, name="Debug", creator=user1, layout_description_json="{}")

    with (
        pytest.raises(error.InvalidActionError, match="Session has a generated game"),
        flask_app.test_request_context(),
    ):
        session_admin._verify_no_layout_description(session)


@pytest.mark.parametrize("new_state", [False, True])
@pytest.mark.parametrize("old_state", [False, True])
def test_admin_set_allow_everyone_claim(
    flask_app, two_player_session, mock_audit, mock_emit_session_update, old_state, new_state
):
    sa = MagicMock()
    sa.get_current_user.return_value = database.User.get_by_id(1234)
    two_player_session.allow_everyone_claim_world = old_state
    two_player_session.save()

    # Run
    with flask_app.test_request_context():
        session_admin.admin_session(sa, 1, SessionAdminGlobalAction.SET_ALLOW_EVERYONE_CLAIM.value, new_state)

    assert database.MultiplayerSession.get_by_id(1).allow_everyone_claim_world == new_state
    mock_audit.assert_called_once_with(
        sa, two_player_session, f"{'Allowing' if new_state else 'Disallowing'} everyone to claim worlds."
    )
    mock_emit_session_update.assert_called_once_with(two_player_session)
