from __future__ import annotations

import datetime

import pytest
from peewee import SqliteDatabase

from randovania.games.game import RandovaniaGame
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import multiplayer_session
from randovania.network_common.multiplayer_session import (
    GameDetails,
    MultiplayerSessionAction,
    MultiplayerSessionActions,
    MultiplayerWorld,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database


def test_init(tmpdir):
    test_db = SqliteDatabase(":memory:")
    with test_db.bind_ctx(database.all_classes):
        test_db.connect(reuse_if_open=True)
        test_db.create_tables(database.all_classes)


@pytest.mark.usefixtures("_mock_seed_hash")
@pytest.mark.parametrize("has_description", [False, True])
def test_multiplayer_session_create_session_entry(clean_database, has_description, test_files_dir, default_game_list):
    # Setup
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime1_and_2_multi.rdvgame"))
    someone = database.User.create(name="Someone")
    s = database.MultiplayerSession.create(
        name="Debug", creator=someone, visibility=MultiplayerSessionVisibility.HIDDEN
    )
    game_details = None
    worlds = []
    actions = []
    if has_description:
        dt = datetime.datetime(2023, 6, 10, 23, 27, 25, 357120, tzinfo=datetime.UTC)
        w1 = database.World.create_for(
            session=s, name="Prime 1", order=0, preset=VersionedPreset.with_preset(description.get_preset(0))
        )
        w2 = database.World.create_for(
            session=s, name="Prime 2", order=1, preset=VersionedPreset.with_preset(description.get_preset(1))
        )
        database.WorldAction.create(provider=w1, location=34, session=s, receiver=w2, time=dt)

        s.layout_description = description
        s.save()
        game_details = GameDetails(
            seed_hash="XXXXXXXX",
            spoiler=True,
            word_hash="Some Words",
        )
        worlds.append(MultiplayerWorld(id=w1.uuid, name="Prime 1", preset_raw=w1.preset))
        worlds.append(MultiplayerWorld(id=w2.uuid, name="Prime 2", preset_raw=w2.preset))
        actions.append(
            MultiplayerSessionAction(
                provider=w1.uuid, receiver=w2.uuid, pickup="Power Bomb Expansion", location=34, time=dt
            )
        )

    # Run
    session = database.MultiplayerSession.get_by_id(1)
    result = session.create_session_entry()
    result_actions = session.describe_actions()

    # Assert
    assert result == multiplayer_session.MultiplayerSessionEntry(
        allowed_games=[RandovaniaGame(g) for g in default_game_list],
        game_details=game_details,
        generation_in_progress=None,
        id=1,
        name="Debug",
        users_list=[],
        worlds=worlds,
        visibility=MultiplayerSessionVisibility.HIDDEN,
        allow_coop=False,
        allow_everyone_claim_world=False,
    )
    assert result_actions == MultiplayerSessionActions(session_id=1, actions=actions)


def test_fun(clean_database):
    user1 = database.User.create(name="Someone")
    user2 = database.User.create(name="Other")
    session1 = database.MultiplayerSession.create(name="Debug1", creator=user1)
    session2 = database.MultiplayerSession.create(name="Debug2", creator=user1)
    world1 = database.World.create(session=session1, name="World1", preset="{}")
    world2 = database.World.create(session=session1, name="World2", preset="{}")
    world3 = database.World.create(session=session1, name="World3", preset="{}")
    world4 = database.World.create(session=session2, name="World4", preset="{}")
    a1 = database.WorldUserAssociation.create(world=world1, user=user1)
    a2 = database.WorldUserAssociation.create(world=world2, user=user1)
    database.WorldUserAssociation.create(world=world3, user=user2)
    database.WorldUserAssociation.create(world=world4, user=user1)

    result = list(
        database.WorldUserAssociation.find_all_for_user_in_session(
            user_id=user1.id,
            session_id=session1.id,
        )
    )

    assert result == [a1, a2]


def test_multiplayer_session_defaults_to_now(clean_database):
    someone = database.User.create(name="Someone")
    database.MultiplayerSession.create(name="Debug", num_teams=1, creator=someone)

    session: database.MultiplayerSession = database.MultiplayerSession.get_by_id(1)
    assert (datetime.datetime.now(datetime.UTC) - session.creation_datetime) < datetime.timedelta(seconds=5)
