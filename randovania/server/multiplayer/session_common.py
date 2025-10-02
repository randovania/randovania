import hashlib
from collections.abc import Sequence

import peewee
import sentry_sdk

from randovania.bitpacking import construct_pack
from randovania.lib.json_lib import JsonObject_RO, JsonType_RO
from randovania.network_common import error, signals
from randovania.server import database
from randovania.server.database import MultiplayerAuditEntry, MultiplayerSession, World
from randovania.server.server_app import ServerApp


def room_name_for(session_id: int) -> str:
    assert isinstance(session_id, int)
    return f"multiplayer-session-{session_id}"


async def emit_session_global_event(
    sa: ServerApp,
    session: MultiplayerSession,
    name: str,
    data: str | bytes | Sequence[JsonType_RO] | JsonObject_RO,
) -> None:
    await sa.sio.emit(name, data, room=room_name_for(session.id), namespace="/")


async def get_membership_for(
    sio_or_user: ServerApp | database.User | int,
    session: int | database.MultiplayerSession,
    sid: str | None = None,
) -> database.MultiplayerMembership:
    if isinstance(sio_or_user, ServerApp):
        assert sid is not None
        user: database.User | int = await sio_or_user.get_current_user(sid)
    else:
        user = sio_or_user

    try:
        return database.MultiplayerMembership.get_by_ids(user, session)
    except peewee.DoesNotExist:
        raise error.NotAuthorizedForActionError


def describe_session(session: MultiplayerSession, world: World | None = None) -> str:
    if world is not None:
        return f"Session {session.id} ({session.name}), World {world.name}"
    else:
        return f"Session {session.id} ({session.name})"


async def emit_session_meta_update(sa: ServerApp, session: MultiplayerSession) -> None:
    with sentry_sdk.start_span(op="emit", description="session_meta_update") as span:
        span.set_data("session.id", session.id)
        span.set_data("session.name", session.name)
        sa.logger.debug("multiplayer_session_meta_update for session %d (%s)", session.id, session.name)
        await emit_session_global_event(
            sa, session, signals.SESSION_META_UPDATE, session.create_session_entry().as_json
        )


async def emit_session_actions_update(sa: ServerApp, session: MultiplayerSession) -> None:
    with sentry_sdk.start_span(op="emit", description="session_actions_update") as span:
        sa.logger.debug("multiplayer_session_actions_update for session %d (%s)", session.id, session.name)
        actions = session.describe_actions()

        span.set_data("session.id", session.id)
        span.set_data("session.name", session.name)
        span.set_data("session.actions", len(actions.actions))
        await emit_session_global_event(sa, session, signals.SESSION_ACTIONS_UPDATE, construct_pack.encode(actions))


async def emit_session_audit_update(sa: ServerApp, session: MultiplayerSession) -> None:
    with sentry_sdk.start_span(op="emit", description="session_audit_update") as span:
        sa.logger.debug("multiplayer_session_audit_update for session %d (%s)", session.id, session.name)
        log = session.get_audit_log()

        span.set_data("session.id", session.id)
        span.set_data("session.name", session.name)
        span.set_data("session.audit", len(log.entries))
        await emit_session_global_event(sa, session, signals.SESSION_AUDIT_UPDATE, construct_pack.encode(log))


async def add_audit_entry(sa: ServerApp, sid: str, session: MultiplayerSession, message: str) -> None:
    user = await sa.get_current_user(sid)
    MultiplayerAuditEntry.create(session=session, user=user, message=message)
    await emit_session_audit_update(sa, session)


def hash_password(password: str) -> str:
    return hashlib.blake2s(password.encode("utf-8")).hexdigest()


async def join_room(sa: ServerApp, sid: str, session: MultiplayerSession) -> None:
    room_name = room_name_for(session.id)
    await sa.sio.enter_room(sid, room_name)

    async with sa.sio.session(sid) as sio_session:
        if "multiplayer_sessions" not in sio_session:
            sio_session["multiplayer_sessions"] = []

        if session.id not in sio_session["multiplayer_sessions"]:
            sio_session["multiplayer_sessions"].append(session.id)


async def leave_room(sa: ServerApp, sid: str, session_id: int) -> None:
    await sa.sio.leave_room(sid, room_name_for(session_id))

    async with sa.sio.session(sid) as sio_session:
        if "multiplayer_sessions" in sio_session:
            if session_id in sio_session["multiplayer_sessions"]:
                sio_session["multiplayer_sessions"].remove(session_id)


async def leave_all_rooms(sa: ServerApp, sid: str) -> None:
    async with sa.sio.session(sid) as sio_session:
        multiplayer_sessions: list[int] = sio_session.pop("multiplayer_sessions", [])

    for session_id in multiplayer_sessions:
        await sa.sio.leave_room(sid, room_name_for(session_id))
