from __future__ import annotations

import base64
import datetime
from typing import TYPE_CHECKING, Any, NamedTuple, cast
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.json_base_model import JsonBaseModel
from randovania.network_common import connection_headers, error
from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomAdminData,
    AsyncRaceRoomEntry,
    AsyncRaceRoomListEntry,
    AsyncRaceRoomRaceStatus,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
    RaceRoomLeaderboard,
    RaceRoomLeaderboardEntry,
)
from randovania.network_common.async_race_room_endpoints import async_race_room_endpoints as race_endpoints
from randovania.network_common.audit import AuditEntry
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser

if TYPE_CHECKING:
    import pytest_mock

    from randovania.network_client.network_client import NetworkClient


@pytest.fixture
def client(tmp_path, mocker: pytest_mock.MockerFixture) -> NetworkClient:
    from randovania.network_client.network_client import NetworkClient

    mock_http_session = mocker.patch("randovania.lib.http_lib.http_session")
    mock_http_session.return_value.closed = False
    return NetworkClient(
        tmp_path,
        {
            "server_address": "http://localhost:5000",
            "socketio_path": "/socket.io",
        },
    )


def _wire(model: JsonBaseModel) -> Any:
    """
    The json the server actually sends for the given model.
    FastAPI serializes responses with pydantic's json mode, which is not necessarily the same as `as_json`.
    """
    return model.model_dump(mode="json")


class MockedCall(NamedTuple):
    request: MagicMock
    """The mocked `server_get`/`server_post`/`server_patch`."""

    response: AsyncMock
    """The response yielded by the request's context manager."""


def mock_response(
    client: NetworkClient, method: str, *, status: int = 200, json: Any = None, body: bytes = b""
) -> MockedCall:
    """Replaces `server_get`/`server_post`/`server_patch` with a mock that returns the given response."""
    request = MagicMock(return_value=AsyncMock())
    setattr(client, method, request)

    response = request.return_value.__aenter__.return_value
    response.status = status
    response.json.return_value = json
    response.read.return_value = body
    return MockedCall(request, response)


@pytest.fixture
def room() -> AsyncRaceRoomEntry:
    return AsyncRaceRoomEntry(
        id=1000,
        name="Async Room",
        creator="TheCreator",
        creation_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 3, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        race_status=AsyncRaceRoomRaceStatus.ACTIVE,
        auth_token="Token",
        game_details=GameDetails(seed_hash="HASH", word_hash="Words Words", spoiler=False),
        presets_raw=[b"PresetBytes"],
        is_admin=True,
        self_status=AsyncRaceRoomUserStatus.NOT_MEMBER,
        allow_pause=False,
    )


@pytest.fixture
def settings() -> AsyncRaceSettings:
    return AsyncRaceSettings(
        name="TheRoom",
        password=None,
        start_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 3, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=True,
    )


async def test_create_async_race_room(client: NetworkClient, room, settings, test_files_dir):
    mocked = mock_response(client, "server_post", json=_wire(room))
    layout = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))

    # Run
    result = await client.create_async_race_room(layout, settings)

    # Assert
    assert result == room
    mocked.request.assert_called_once_with(
        race_endpoints.create_room(),
        json={
            "layout_bin": base64.b64encode(layout.as_binary(force_spoiler=True)).decode("ascii"),
            "settings": settings.as_json,
        },
    )
    assert mocked.response.json.await_count == 1


@pytest.mark.parametrize("ignore_limit", [False, True])
async def test_get_async_race_room_list(client: NetworkClient, ignore_limit: bool):
    entry = AsyncRaceRoomListEntry(
        id=1000,
        name="Async Room",
        games=None,
        has_password=False,
        creator="TheCreator",
        creation_date=datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 3, 1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        race_status=AsyncRaceRoomRaceStatus.ACTIVE,
    )
    mocked = mock_response(client, "server_get", json=[_wire(entry)])

    # Run
    result = await client.get_async_race_room_list(ignore_limit)

    # Assert
    assert result == [entry]
    mocked.request.assert_called_once_with(
        race_endpoints.list_rooms(),
        params={} if ignore_limit else {"limit": "100"},
    )


@pytest.mark.parametrize("password", [None, "TheSecret"])
async def test_get_async_race_room(client: NetworkClient, room, password: str | None):
    mocked = mock_response(client, "server_get", json=_wire(room))

    # Run
    result = await client.get_async_race_room(1000, password)

    # Assert
    assert result == room
    mocked.request.assert_called_once_with(
        race_endpoints.get_room(1000),
        params={} if password is None else {"password": password},
    )


async def test_async_race_refresh_room(client: NetworkClient, room):
    mocked = mock_response(client, "server_get", json=_wire(room))

    # Run
    result = await client.async_race_refresh_room(room)

    # Assert
    assert result == room
    mocked.request.assert_called_once_with(
        race_endpoints.refresh_room(1000),
        params={"auth_token": "Token"},
    )


async def test_async_race_get_leaderboard(client: NetworkClient, room):
    leaderboard = RaceRoomLeaderboard(
        entries=[
            RaceRoomLeaderboardEntry(user=RandovaniaUser(id=1234, name="The Player"), time=datetime.timedelta(hours=2)),
            RaceRoomLeaderboardEntry(user=RandovaniaUser(id=1235, name="Other Player"), time=None),
        ]
    )
    mocked = mock_response(client, "server_get", json=_wire(leaderboard))

    # Run
    result = await client.async_race_get_leaderboard(room)

    # Assert
    assert result == leaderboard
    mocked.request.assert_called_once_with(
        race_endpoints.room_leaderboard(1000),
        params={"auth_token": "Token"},
    )


async def test_async_race_get_layout(client: NetworkClient, room, test_files_dir):
    layout = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))
    # The layout is the raw response body, not json
    mocked = mock_response(client, "server_get", body=layout.as_binary())

    # Run
    result = await client.async_race_get_layout(room)

    # Assert
    assert result == layout
    mocked.response.json.assert_not_awaited()
    mocked.request.assert_called_once_with(
        race_endpoints.room_layout(1000),
        params={"auth_token": "Token"},
    )


async def test_async_race_get_audit_log(client: NetworkClient, room):
    entries = [
        AuditEntry(user="The Player", message="Did a thing", time=datetime.datetime(2020, 5, 1, tzinfo=datetime.UTC)),
        AuditEntry(user="The Name", message="Did another", time=datetime.datetime(2020, 5, 2, tzinfo=datetime.UTC)),
    ]
    mocked = mock_response(client, "server_get", json=[_wire(it) for it in entries])

    # Run
    result = await client.async_race_get_audit_log(room)

    # Assert
    assert result == entries
    mocked.request.assert_called_once_with(
        race_endpoints.room_audit_log(1000),
        params={"auth_token": "Token"},
    )


async def test_async_race_get_livesplit_url(client: NetworkClient, room):
    mocked = mock_response(client, "server_get", json="ws://example.com/livesplit/1000")

    # Run
    result = await client.async_race_get_livesplit_url(room)

    # Assert
    assert result == "ws://example.com/livesplit/1000"
    mocked.request.assert_called_once_with(race_endpoints.room_livesplit_url(1000))


def _entry_data(user_id: int) -> AsyncRaceEntryData:
    return AsyncRaceEntryData(
        user=RandovaniaUser(id=user_id, name="The Player"),
        join_date=datetime.datetime(2020, 2, 1, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 2, 2, tzinfo=datetime.UTC),
        finish_date=None,
        forfeit=False,
        pauses=[],
        submission_notes="",
        proof_url="",
    )


async def test_async_race_admin_get_admin_data(client: NetworkClient):
    admin_data = AsyncRaceRoomAdminData(users=[_entry_data(1234)])
    mocked = mock_response(client, "server_get", json=_wire(admin_data))

    # Run
    result = await client.async_race_admin_get_admin_data(1000)

    # Assert
    assert result == admin_data
    mocked.request.assert_called_once_with(race_endpoints.room_admin_data(1000))


async def test_async_race_admin_update_entries(client: NetworkClient, room):
    entries = [_entry_data(1234), _entry_data(1235)]
    mocked = mock_response(client, "server_post", json=_wire(room))

    # Run
    result = await client.async_race_admin_update_entries(1000, entries)

    # Assert
    assert result == room
    mocked.request.assert_called_once_with(
        race_endpoints.room_admin_entries(1000),
        json=[it.as_json for it in entries],
    )


async def test_async_race_join_and_export(client: NetworkClient, room):
    # A concrete subclass of the abstract BaseCosmeticPatches: the server has to decode it
    # based on the room's game, so the client sends it as a plain json object.
    cosmetic = EchoesCosmeticPatches(open_map=False)
    mocked = mock_response(client, "server_post", json={"the": "patcher data"})

    # Run
    result = await client.async_race_join_and_export(room, cosmetic)

    # Assert
    assert result == {"the": "patcher data"}
    mocked.request.assert_called_once_with(
        race_endpoints.room_join_and_export(1000),
        params={"auth_token": "Token"},
        json=cosmetic.as_json,
    )


async def test_async_race_change_state(client: NetworkClient, room):
    mocked = mock_response(client, "server_post", json=_wire(room))

    # Run
    result = await client.async_race_change_state(1000, AsyncRaceRoomUserStatus.FINISHED)

    # Assert
    assert result == room
    mocked.request.assert_called_once_with(
        race_endpoints.room_state(1000),
        params={"new_state": "finished"},
    )


async def test_async_race_get_own_proof(client: NetworkClient):
    mocked = mock_response(client, "server_get", json=["The notes", "https://example.com/proof"])

    # Run
    result = await client.async_race_get_own_proof(1000)

    # Assert
    assert result == ("The notes", "https://example.com/proof")
    mocked.request.assert_called_once_with(race_endpoints.room_own_proof(1000))


async def test_async_race_submit_proof(client: NetworkClient):
    mocked = mock_response(client, "server_post", json=None)

    # Run
    await client.async_race_submit_proof(1000, "The notes", "https://example.com/proof")

    # Assert
    mocked.request.assert_called_once_with(
        race_endpoints.room_submit_proof(1000),
        params={"submission_notes": "The notes", "proof_url": "https://example.com/proof"},
    )
    # There's no body to decode
    mocked.response.json.assert_not_awaited()


async def test_async_race_change_room_settings(client: NetworkClient, room, settings):
    mocked = mock_response(client, "server_patch", json=_wire(room))

    # Run
    result = await client.async_race_change_room_settings(1000, settings)

    # Assert
    assert result == room
    mocked.request.assert_called_once_with(
        race_endpoints.change_room(1000),
        json=settings.as_json,
    )


async def test_rest_error_is_decoded(client: NetworkClient):
    mock_response(client, "server_get", status=403, json=error.NotAuthorizedForActionError().as_json)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        await client.async_race_admin_get_admin_data(1000)


async def test_rest_error_invalid_session_logs_out(client: NetworkClient):
    client.logout = AsyncMock()
    mock_response(client, "server_get", status=401, json=error.InvalidSessionError().as_json)

    # Run
    with pytest.raises(error.InvalidSessionError):
        await client.async_race_admin_get_admin_data(1000)

    # Assert
    client.logout.assert_awaited_once_with()


async def test_rest_error_unknown_body(client: NetworkClient):
    # A response that isn't one of our errors falls back to aiohttp's own handling
    mocked = mock_response(client, "server_get", status=404, json={"detail": "Resource not found"})
    mocked.response.raise_for_status = MagicMock(side_effect=aiohttp.ClientError("Not Found"))

    # Run
    with pytest.raises(aiohttp.ClientError):
        await client.async_race_admin_get_admin_data(1000)

    # Assert
    mocked.response.raise_for_status.assert_called_once_with()


async def test_rest_headers_include_patch(client: NetworkClient):
    # `server_patch` must apply the same authentication headers as get/post
    client._session_id = "the-sid"
    client._encoded_session = "the-session"
    http = cast("MagicMock", client.http)

    # Run
    client.server_patch("some-path", json={})

    # Assert
    http.patch.assert_called_once_with(
        "http://localhost:5000/some-path",
        json={},
        headers={
            **connection_headers(),
            "Accept": "application/json",
            "X-Randovania-Sid": "the-sid",
            "X-Randovania-Session": "the-session",
        },
    )
