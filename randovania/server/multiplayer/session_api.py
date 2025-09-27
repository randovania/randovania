import datetime
from typing import Any

from peewee import Case, fn

from randovania.network_common import error
from randovania.network_common.multiplayer_session import (
    MAX_SESSION_NAME_LENGTH,
    MultiplayerSessionListEntry,
)
from randovania.server import database
from randovania.server.database import MultiplayerMembership, MultiplayerSession, User, World
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp


async def list_sessions(sa: ServerApp, sid: str, limit: int | None) -> list[dict]:
    # Note: this query fails to list any session that has no memberships
    # But that's fine, because these sessions should've been deleted!
    def construct_helper(**args: Any) -> MultiplayerSessionListEntry:
        args["creation_date"] = datetime.datetime.fromisoformat(args["creation_date"])
        args["join_date"] = datetime.datetime.fromisoformat(args["join_date"])
        args["has_password"] = bool(args["has_password"])
        args["is_user_in_session"] = bool(args["is_user_in_session"])
        return MultiplayerSessionListEntry(**args)

    user = await sa.get_current_user(sid)
    world_count_subquery = World.select(fn.COUNT(World.id)).where(World.session_id == MultiplayerSession.id)
    sessions: list[MultiplayerSessionListEntry] = (
        MultiplayerSession.select(
            MultiplayerSession.id,
            MultiplayerSession.name,
            Case(None, ((MultiplayerSession.password.is_null(), False),), True).alias("has_password"),  # type: ignore[union-attr]
            MultiplayerSession.visibility,
            fn.COUNT(MultiplayerMembership.user_id).alias("num_users"),
            world_count_subquery.alias("num_worlds"),  # type: ignore[attr-defined]
            User.name.alias("creator"),  # type: ignore[attr-defined]
            MultiplayerSession.creation_date.alias("creation_date"),  # type: ignore[attr-defined]
            fn.MAX(Case(MultiplayerMembership.user_id, ((user.id, True),), False)).alias("is_user_in_session"),
            MultiplayerMembership.join_date.alias("join_date"),
        )
        .join(User, on=MultiplayerSession.creator)
        .join(
            MultiplayerMembership,
            on=MultiplayerMembership.session == MultiplayerSession.id,
        )
        .group_by(MultiplayerSession.id)
        .order_by(MultiplayerSession.id.desc())  # type: ignore[attr-defined]
        .limit(limit)
        .objects(construct_helper)
    )

    return [session.as_json for session in sessions]


async def create_session(sa: ServerApp, sid: str, session_name: str) -> dict:
    current_user = await sa.get_current_user(sid)

    if not (0 < len(session_name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    with database.db.atomic():
        new_session: MultiplayerSession = MultiplayerSession.create(
            name=session_name,
            password=None,
            creator=current_user,
        )
        MultiplayerMembership.create(
            user=current_user,
            session=new_session,
            admin=True,
        )

    await session_common.join_room(sa, sid, new_session)
    return new_session.create_session_entry().as_json


async def join_session(sa: ServerApp, sid: str, session_id: int, password: str | None) -> dict:
    session = MultiplayerSession.get_by_id(session_id)
    user = await sa.get_current_user(sid)

    if not session.is_user_in_session(user):
        if session.password is not None:
            if password is None or session_common.hash_password(password) != session.password:
                raise error.WrongPasswordError
        elif password is not None:
            raise error.WrongPasswordError

    MultiplayerMembership.get_or_create(user=user, session=session)
    await session_common.join_room(sa, sid, session)
    await session_common.emit_session_meta_update(sa, session)

    return session.create_session_entry().as_json


async def listen_to_session(sa: ServerApp, sid: str, session_id: int, listen: bool) -> None:
    if listen:
        membership = await session_common.get_membership_for(sa, session_id, sid)
        await session_common.join_room(sa, sid, membership.session)
    else:
        await session_common.leave_room(sa, sid, session_id)


async def request_session_update(sa: ServerApp, sid: str, session_id: int) -> None:
    session = MultiplayerSession.get_by_id(session_id)

    await session_common.emit_session_meta_update(sa, session)
    if session.has_layout_description():
        await session_common.emit_session_actions_update(sa, session)

    await session_common.emit_session_audit_update(sa, session)


def setup_app(sa: ServerApp) -> None:
    sa.on("multiplayer_list_sessions", list_sessions, with_header_check=True)
    sa.on("multiplayer_create_session", create_session, with_header_check=True)
    sa.on("multiplayer_join_session", join_session, with_header_check=True)
    sa.on("multiplayer_listen_to_session", listen_to_session, with_header_check=True)
    sa.on("multiplayer_request_session_update", request_session_update)
