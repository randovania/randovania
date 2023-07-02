
from randovania.network_common import error
from randovania.network_common.multiplayer_session import MAX_SESSION_NAME_LENGTH
from randovania.server import database
from randovania.server.database import MultiplayerSession, MultiplayerMembership, User
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp


def list_sessions(sio: ServerApp, limit: int | None):
    sessions: list[MultiplayerSession] = list(
        MultiplayerSession.select().order_by(MultiplayerSession.id.desc()).limit(limit)
    )

    return [
        session.create_list_entry(sio.get_current_user()).as_json
        for session in sessions
    ]


def create_session(sio: ServerApp, session_name: str):
    current_user = sio.get_current_user()

    if not (0 < len(session_name) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidAction("Invalid session name length")

    with database.db.atomic():
        new_session: MultiplayerSession = MultiplayerSession.create(
            name=session_name,
            password=None,
            creator=current_user,
        )
        MultiplayerMembership.create(
            user=sio.get_current_user(),
            session=new_session,
            admin=True,
        )

    session_common.join_room(sio, new_session)
    return new_session.create_session_entry().as_json


def join_session(sio: ServerApp, session_id: int, password: str | None):
    session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    user: User = sio.get_current_user()

    if not session.is_user_in_session(user):
        if session.password is not None:
            if password is None or session_common.hash_password(password) != session.password:
                raise error.WrongPasswordError()
        elif password is not None:
            raise error.WrongPasswordError()

    MultiplayerMembership.get_or_create(user=sio.get_current_user(), session=session)
    session_common.join_room(sio, session)
    session_common.emit_session_meta_update(session)

    return session.create_session_entry().as_json


def listen_to_session(sio: ServerApp, session_id: int, listen: bool):
    if listen:
        membership = session_common.get_membership_for(sio, session_id)
        session_common.join_room(sio, membership.session)
    else:
        session_common.leave_room(sio, session_id)


def request_session_update(sio: ServerApp, session_id: int):
    session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)

    session_common.emit_session_meta_update(session)
    if session.has_layout_description():
        session_common.emit_session_actions_update(session)

    session_common.emit_session_audit_update(session)


def setup_app(sio: ServerApp):
    sio.on("multiplayer_list_sessions", list_sessions, with_header_check=True)
    sio.on("multiplayer_create_session", create_session, with_header_check=True)
    sio.on("multiplayer_join_session", join_session, with_header_check=True)
    sio.on("multiplayer_listen_to_session", listen_to_session, with_header_check=True)
    sio.on("multiplayer_request_session_update", request_session_update)
