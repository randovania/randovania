import datetime
import json
import uuid
from unittest.mock import AsyncMock, MagicMock

from PySide6 import QtWidgets

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

WORLD_1 = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")
WORLD_3 = uuid.UUID("b1aa125a-dd65-4d2a-937d-4a64c4632261")


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
                has_been_beaten=True,
            ),
            MultiplayerWorld(
                name="W2",
                id=u2,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
                has_been_beaten=False,
            ),
            MultiplayerWorld(
                name="W3",
                id=u3,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
                has_been_beaten=False,
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
        allow_abandon_worlds=True,
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
        allow_abandon_worlds=True,
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
    assert p_a.child(0).text(6) == "Beaten"
    assert p_b.child(0).text(6) == ""
    unclaimed = root.child(2)
    assert unclaimed.text(0) == "Unclaimed Worlds"
    assert unclaimed.childCount() == 1
    assert unclaimed.child(0).text(0) == "W3"


def test_widgets_with_abandoned_world(skip_qtbot, preset_manager):
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
                has_been_beaten=False,
            ),
            MultiplayerWorld(
                name="W2",
                id=u2,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
                has_been_beaten=False,
            ),
            # Abandoned world, associated to nobody.
            MultiplayerWorld(
                name="W3",
                id=u3,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
                has_been_beaten=False,
                is_abandoned=True,
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
        ],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
        allow_coop=False,
        allow_everyone_claim_world=True,
        allow_abandon_worlds=True,
    )

    session_api = MagicMock()
    session_api.network_client = MagicMock()
    session_api.network_client.current_user = MagicMock()
    session_api.network_client.current_user.id = 12

    window = MultiplayerSessionUsersWidget(MagicMock(), MagicMock(spec=WindowManager), session_api)
    skip_qtbot.addWidget(window)

    # Run
    window.update_state(session)

    root = window.invisibleRootItem()
    # Player A, Unclaimed Worlds (W2), Abandoned Worlds (W3)
    assert root.childCount() == 3
    assert root.child(0).text(0) == "Player A"
    # W1 plus the "Add new world" button item (no layout generated yet).
    assert root.child(0).childCount() == 2
    assert root.child(0).child(0).text(0) == "W1"

    unclaimed = root.child(1)
    assert unclaimed.text(0) == "Unclaimed Worlds"
    assert unclaimed.childCount() == 1
    assert unclaimed.child(0).text(0) == "W2"

    abandoned = root.child(2)
    assert abandoned.text(0) == "Abandoned Worlds"
    assert abandoned.childCount() == 1
    assert abandoned.child(0).text(0) == "W3"
    assert abandoned.child(0).text(6) == "Abandoned"


def _abandoned_world_session(preset_manager, *, claimed: bool) -> MultiplayerSessionEntry:
    """A session with W1, owned by Player A, and W3, abandoned and optionally claimed by Player A."""
    activity = datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC)
    worlds = {WORLD_1: UserWorldDetail(GameConnectionStatus.InGame, activity)}
    if claimed:
        worlds[WORLD_3] = UserWorldDetail(GameConnectionStatus.InGame, activity)

    return MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[
            MultiplayerWorld(
                name="W1",
                id=WORLD_1,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
                has_been_beaten=False,
            ),
            MultiplayerWorld(
                name="W3",
                id=WORLD_3,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
                has_been_beaten=False,
                is_abandoned=True,
            ),
        ],
        users_list=[MultiplayerUser(12, "Player A", True, True, worlds=worlds)],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.BLANK],
        allow_coop=False,
        allow_everyone_claim_world=True,
        allow_abandon_worlds=True,
    )


def _users_widget_for(skip_qtbot, session: MultiplayerSessionEntry) -> MultiplayerSessionUsersWidget:
    session_api = MagicMock()
    session_api.abandon_world = AsyncMock()
    session_api.network_client = MagicMock()
    session_api.network_client.current_user = MagicMock()
    session_api.network_client.current_user.id = 12

    window = MultiplayerSessionUsersWidget(MagicMock(), MagicMock(spec=WindowManager), session_api)
    skip_qtbot.addWidget(window)
    window.update_state(session)
    return window


def test_widgets_with_claimed_abandoned_world(skip_qtbot, preset_manager):
    # An abandoned world is claimed by whoever runs its bot, so it's shown under that user. Only the
    # abandoned worlds nobody runs are left in the "Abandoned Worlds" section.
    window = _users_widget_for(skip_qtbot, _abandoned_world_session(preset_manager, claimed=True))

    root = window.invisibleRootItem()
    # No "Abandoned Worlds" section: Player A runs the only abandoned world's bot.
    assert root.childCount() == 1
    player_a = root.child(0)
    assert player_a.text(0) == "Player A"
    # W1 and W3, plus the "Add new world" button item (no layout generated yet).
    world_names = {player_a.child(i).text(0) for i in range(player_a.childCount())}
    assert world_names == {"W1", "W3", ""}


def _clicks_button(mocker, button_text: str) -> MagicMock:
    """Makes the abandon confirmation dialog answer with the button of the given text."""

    async def execute(box: QtWidgets.QMessageBox) -> None:
        box.clickedButton = MagicMock(return_value=next(b for b in box.buttons() if b.text() == button_text))

    return mocker.patch(
        "randovania.gui.widgets.multiplayer_session_users_widget.async_dialog.execute_dialog", side_effect=execute
    )


async def test_world_abandon_play_here(skip_qtbot, preset_manager, mocker):
    window = _users_widget_for(skip_qtbot, _abandoned_world_session(preset_manager, claimed=False))
    _clicks_button(mocker, "Abandon and play it here")
    register = mocker.patch.object(window, "_register_abandoned_world_connector")

    await window._world_abandon(WORLD_1, 12)

    # Claiming the world is what allows this instance to run its bot.
    window._session_api.abandon_world.assert_awaited_once_with(WORLD_1, 12, True)
    register.assert_called_once_with(WORLD_1)


async def test_world_abandon_only(skip_qtbot, preset_manager, mocker):
    window = _users_widget_for(skip_qtbot, _abandoned_world_session(preset_manager, claimed=False))
    _clicks_button(mocker, "Abandon only")
    register = mocker.patch.object(window, "_register_abandoned_world_connector")

    await window._world_abandon(WORLD_1, 12)

    window._session_api.abandon_world.assert_awaited_once_with(WORLD_1, 12, False)
    register.assert_not_called()


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
                has_been_beaten=True,
            ),
            MultiplayerWorld(
                name="W2",
                id=u2,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
                has_been_beaten=False,
            ),
            MultiplayerWorld(
                name="W3",
                id=u3,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
                has_been_beaten=False,
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
        allow_abandon_worlds=True,
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
        allow_abandon_worlds=True,
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
    assert p_a.child(0).text(6) == "Beaten"
    assert p_a.child(1).text(6) == ""
    assert p_b.text(0) == "Player B"
    assert p_b.child(0).text(0) == "W2"
    assert p_b.child(1).text(6) == ""
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
