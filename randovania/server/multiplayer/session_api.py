import datetime

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


def list_sessions(sa: ServerApp, limit: int | None):
    # Note: this query fails to list any session that has no memberships
    # But that's fine, because these sessions should've been deleted!
    def construct_helper(**args):
        args["creation_date"] = datetime.datetime.fromisoformat(args["creation_date"])
        args["join_date"] = datetime.datetime.fromisoformat(args["join_date"])
        args["has_password"] = bool(args["has_password"])
        args["is_user_in_session"] = bool(args["is_user_in_session"])
        return MultiplayerSessionListEntry(**args)

    user = sa.get_current_user()
    world_count_subquery = World.select(fn.COUNT(World.id)).where(World.session_id == MultiplayerSession.id)
    sessions: list[MultiplayerSessionListEntry] = (
        MultiplayerSession.select(
            MultiplayerSession.id,
            MultiplayerSession.name,
            Case(None, ((MultiplayerSession.password.is_null(), False),), True).alias("has_password"),
            MultiplayerSession.visibility,
            fn.COUNT(MultiplayerMembership.user_id).alias("num_users"),
            world_count_subquery.alias("num_worlds"),
            User.name.alias("creator"),
            MultiplayerSession.creation_date.alias("creation_date"),
            fn.MAX(Case(MultiplayerMembership.user_id, ((user.id, True),), False)).alias("is_user_in_session"),
            MultiplayerMembership.join_date.alias("join_date"),
        )
        .join(User, on=MultiplayerSession.creator)
        .join(
            MultiplayerMembership,
            on=MultiplayerMembership.session == MultiplayerSession.id,
        )
        .group_by(MultiplayerSession.id)
        .order_by(MultiplayerSession.id.desc())
        .limit(limit)
        .objects(construct_helper)
    )

    return [session.as_json for session in sessions]


def create_session(sa: ServerApp, session_name: str):
    current_user = sa.get_current_user()

    if not (0 < len(session_name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    with database.db.atomic():
        new_session: MultiplayerSession = MultiplayerSession.create(
            name=session_name,
            password=None,
            creator=current_user,
        )
        MultiplayerMembership.create(
            user=sa.get_current_user(),
            session=new_session,
            admin=True,
        )

    session_common.join_room(sa, new_session)
    return new_session.create_session_entry().as_json


def join_session(sa: ServerApp, session_id: int, password: str | None):
    session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    user: User = sa.get_current_user()

    if not session.is_user_in_session(user):
        if session.password is not None:
            if password is None or session_common.hash_password(password) != session.password:
                raise error.WrongPasswordError
        elif password is not None:
            raise error.WrongPasswordError

    MultiplayerMembership.get_or_create(user=sa.get_current_user(), session=session)
    session_common.join_room(sa, session)
    session_common.emit_session_meta_update(session)

    return session.create_session_entry().as_json


def listen_to_session(sa: ServerApp, session_id: int, listen: bool):
    if listen:
        membership = session_common.get_membership_for(sa, session_id)
        session_common.join_room(sa, membership.session)
    else:
        session_common.leave_room(sa, session_id)


def request_session_update(sa: ServerApp, session_id: int):
    session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)

    session_common.emit_session_meta_update(session)
    if session.has_layout_description():
        session_common.emit_session_actions_update(session)

    session_common.emit_session_audit_update(session)


def setup_app(sa: ServerApp):
    sa.on("multiplayer_list_sessions", list_sessions, with_header_check=True)
    sa.on("multiplayer_create_session", create_session, with_header_check=True)
    sa.on("multiplayer_join_session", join_session, with_header_check=True)
    sa.on("multiplayer_listen_to_session", listen_to_session, with_header_check=True)
    sa.on("multiplayer_request_session_update", request_session_update)
