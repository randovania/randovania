import datetime
import json
import uuid
from unittest.mock import MagicMock

from randovania.game.game_enum import RandovaniaGame
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.widgets.multiplayer_session_users_widget import MultiplayerSessionUsersWidget
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import (
    MultiplayerSessionEntry,
    MultiplayerUser,
    MultiplayerWorld,
    UserWorldDetail,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility


def test_widgets_in_normal_session(skip_qtbot, preset_manager):
    u1 = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")
    u2 = uuid.UUID("4bdb294e-9059-4fdf-9822-3f649023249a")
    u3 = uuid.UUID("b1aa125a-dd65-4d2a-937d-4a64c4632261")

    session = MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[
            MultiplayerWorld(
                name="W1",
                id=u1,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
            MultiplayerWorld(
                name="W2",
                id=u2,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
            ),
            MultiplayerWorld(
                name="W3",
                id=u3,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
        ],
        users_list=[
            MultiplayerUser(
                12,
                "Player A",
                True,
                True,
                worlds={
                    u1: UserWorldDetail(
                        GameConnectionStatus.InGame, datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC)
                    )
                },
            ),
            MultiplayerUser(
                13,
                "Player B",
                False,
                True,
                worlds={
                    u2: UserWorldDetail(
                        GameConnectionStatus.InGame, datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC)
                    )
                },
            ),
        ],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
        allow_coop=False,
        allow_everyone_claim_world=True,
    )

    session_api = MagicMock()
    session_api.network_client = MagicMock()
    session_api.network_client.current_user = MagicMock()
    session_api.network_client.current_user.id = 12

    window = MultiplayerSessionUsersWidget(MagicMock(), MagicMock(spec=WindowManager), session_api)
    skip_qtbot.addWidget(window)
    window._session = MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[],
        users_list=[
            MultiplayerUser(
                12,
                "Player A",
                True,
                True,
                worlds={},
            ),
            MultiplayerUser(
                13,
                "Player B",
                False,
                True,
                worlds={},
            ),
        ],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
        allow_coop=False,
        allow_everyone_claim_world=True,
    )

    # Run
    window.update_state(session)

    root = window.invisibleRootItem()
    assert root.childCount() == 3
    p_a = root.child(0)
    p_b = root.child(1)
    assert p_a.text(0) == "Player A"
    assert p_b.text(0) == "Player B"
    assert p_a.childCount() == p_b.childCount() == 2
    assert p_a.child(0).text(0) == "W1"
    assert p_b.child(0).text(0) == "W2"
    unclaimed = root.child(2)
    assert unclaimed.text(0) == "Unclaimed Worlds"
    assert unclaimed.childCount() == 1
    assert unclaimed.child(0).text(0) == "W3"


def test_widgets_in_coop_session(skip_qtbot, preset_manager):
    u1 = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")
    u2 = uuid.UUID("4bdb294e-9059-4fdf-9822-3f649023249a")
    u3 = uuid.UUID("b1aa125a-dd65-4d2a-937d-4a64c4632261")

    session = MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[
            MultiplayerWorld(
                name="W1",
                id=u1,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
            MultiplayerWorld(
                name="W2",
                id=u2,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
            ),
            MultiplayerWorld(
                name="W3",
                id=u3,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
        ],
        users_list=[
            MultiplayerUser(
                12,
                "Player A",
                True,
                True,
                worlds={
                    u1: UserWorldDetail(
                        GameConnectionStatus.InGame, datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC)
                    ),
                    u2: UserWorldDetail(
                        GameConnectionStatus.InGame, datetime.datetime(2020, 1, 3, 2, 50, tzinfo=datetime.UTC)
                    ),
                },
            ),
            MultiplayerUser(
                13,
                "Player B",
                False,
                True,
                worlds={
                    u2: UserWorldDetail(
                        GameConnectionStatus.InGame, datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC)
                    )
                },
            ),
        ],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
        allow_coop=True,
        allow_everyone_claim_world=True,
    )

    session_api = MagicMock()
    session_api.network_client = MagicMock()
    session_api.network_client.current_user = MagicMock()
    session_api.network_client.current_user.id = 12

    window = MultiplayerSessionUsersWidget(MagicMock(), MagicMock(spec=WindowManager), session_api)
    skip_qtbot.addWidget(window)
    window._session = MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[],
        users_list=[
            MultiplayerUser(
                12,
                "Player A",
                True,
                True,
                worlds={},
            ),
            MultiplayerUser(
                13,
                "Player B",
                False,
                True,
                worlds={},
            ),
        ],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
        allow_coop=False,
        allow_everyone_claim_world=True,
    )

    # Run
    window.update_state(session)

    def do_stuff(item, indent):
        print("-" * indent + item.text(0))
        for index in range(item.childCount()):
            do_stuff(item.child(index), indent + 1)

    do_stuff(window.invisibleRootItem(), 0)

    root = window.invisibleRootItem()
    assert root.childCount() == 4
    p_a = root.child(0)
    p_b = root.child(1)
    assert p_a.text(0) == "Player A"
    assert p_a.childCount() == 3
    assert p_a.child(0).text(0) == "W1"
    assert p_a.child(1).text(0) == "W2"
    assert p_b.text(0) == "Player B"
    assert p_b.child(0).text(0) == "W2"
    assert p_b.childCount() == 2
    unclaimed = root.child(2)
    assert unclaimed.text(0) == "Unclaimed Worlds"
    assert unclaimed.childCount() == 1
    assert unclaimed.child(0).text(0) == "W3"
    all_worlds = root.child(3)
    assert all_worlds.text(0) == "All Worlds"
    assert all_worlds.childCount() == 3
    for i in range(all_worlds.childCount()):
        assert all_worlds.child(i).text(0) == f"W{i + 1}"
