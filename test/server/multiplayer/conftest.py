from __future__ import annotations

import datetime
import json
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.games.game import RandovaniaGame
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common.multiplayer_session import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database


@pytest.fixture()
def mock_emit_session_update(mocker) -> MagicMock:
    return mocker.patch("randovania.server.multiplayer.session_common.emit_session_meta_update", autospec=True)


@pytest.fixture()
def mock_audit(mocker) -> MagicMock:
    return mocker.patch("randovania.server.multiplayer.session_common.add_audit_entry", autospec=True)


@pytest.fixture()
def solo_two_world_session(clean_database, test_files_dir):
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime1_and_2_multi.rdvgame"))
    preset_0 = VersionedPreset.with_preset(description.get_preset(0))
    preset_1 = VersionedPreset.with_preset(description.get_preset(1))

    user1 = database.User.create(id=1234, name="The Name")

    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        creation_date=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
    )
    session.layout_description = description
    session.save()
    w1 = database.World.create_for(
        session=session, name="World 1", preset=preset_0, order=0, uid=uuid.UUID("1179c986-758a-4170-9b07-fe4541d78db0")
    )
    w2 = database.World.create_for(
        session=session, name="World 2", preset=preset_1, order=1, uid=uuid.UUID("6b5ac1a1-d250-4f05-a5fb-ae37e8a92165")
    )

    database.MultiplayerMembership.create(user=user1, session=session, admin=False)
    database.WorldUserAssociation.create(
        world=w1, user=user1, last_activity=datetime.datetime(2021, 9, 1, 10, 20, tzinfo=datetime.UTC)
    )
    database.WorldUserAssociation.create(
        world=w2, user=user1, last_activity=datetime.datetime(2022, 5, 6, 12, 0, tzinfo=datetime.UTC)
    )
    database.WorldAction.create(provider=w2, location=0, receiver=w1, session=session)

    return session


@pytest.fixture()
def two_player_session(clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")

    session = database.MultiplayerSession.create(
        id=1, name="Debug", state=MultiplayerSessionVisibility.VISIBLE, creator=user1
    )
    w1 = database.World.create(
        session=session, name="World 1", preset="{}", order=0, uuid=uuid.UUID("1179c986-758a-4170-9b07-fe4541d78db0")
    )
    w2 = database.World.create(
        session=session, name="World 2", preset="{}", order=1, uuid=uuid.UUID("6b5ac1a1-d250-4f05-a5fb-ae37e8a92165")
    )

    database.MultiplayerMembership.create(user=user1, session=session, admin=True)
    database.MultiplayerMembership.create(user=user2, session=session, admin=False)
    database.WorldUserAssociation.create(
        world=w1, user=user1, last_activity=datetime.datetime(2021, 9, 1, 10, 20, tzinfo=datetime.UTC)
    )
    database.WorldUserAssociation.create(
        world=w2, user=user2, last_activity=datetime.datetime(2022, 5, 6, 12, 0, tzinfo=datetime.UTC)
    )
    database.WorldAction.create(provider=w2, location=0, receiver=w1, session=session)

    return session


@pytest.fixture()
def session_update(clean_database, mocker):
    mock_layout = MagicMock(spec=LayoutDescription)
    mock_layout.shareable_word_hash = "Words of O-Lir"
    mock_layout.shareable_hash = "ABCDEFG"
    mock_layout.has_spoiler = True
    mock_layout.permalink.as_base64_str = "<permalink>"
    mock_layout.get_preset.return_value.game = RandovaniaGame.METROID_PRIME_ECHOES
    time = datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC)

    game_details = GameDetails(
        seed_hash="ABCDEFG",
        word_hash="Words of O-Lir",
        spoiler=True,
    )

    mock_layout.all_patches = MagicMock()
    target = mock_layout.all_patches.__getitem__.return_value.pickup_assignment.__getitem__.return_value
    target.pickup.name = "The Pickup"

    mocker.patch("randovania.server.database.MultiplayerSession._get_layout_description", return_value=mock_layout)

    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other")
    session = database.MultiplayerSession.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        creator=user1,
        layout_description_json="{}",
        game_details_json=json.dumps(game_details.as_json),
    )
    database.MultiplayerMembership.create(user=user1, session=session, row=0, admin=True, connection_state="Something")
    database.MultiplayerMembership.create(
        user=user2, session=session, row=1, admin=False, ready=True, connection_state="Game"
    )
    w1 = database.World.create(
        session=session, name="World1", uuid=uuid.UUID("67d75d0e-da8d-4a90-b29e-cae83bcf9519"), preset="{}"
    )
    w2 = database.World.create(
        session=session, name="World2", uuid=uuid.UUID("d0f7ed70-66b0-413c-bc13-f9f7fb018726"), preset="{}"
    )

    database.WorldAction.create(provider=w1, location=0, session=session, receiver=w2, time=time)

    return session
