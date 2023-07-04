import hashlib
import uuid

import flask_socketio
import peewee
import sentry_sdk

from randovania.bitpacking import construct_pack
from randovania.network_common import signals, error
from randovania.server import database
from randovania.server.database import (MultiplayerSession, MultiplayerAuditEntry,
                                        WorldUserAssociation, World)
from randovania.server.lib import logger
from randovania.server.server_app import ServerApp


def room_name_for(session_id: int) -> str:
    assert isinstance(session_id, int)
    return f"multiplayer-session-{session_id}"


def emit_session_global_event(session: MultiplayerSession, name: str, data):
    flask_socketio.emit(name, data, room=room_name_for(session.id), namespace="/")


def get_inventory_room_name_raw(world_uuid: uuid.UUID, user_id: int):
    return f"multiplayer-{world_uuid}-{user_id}-inventory"


def get_inventory_room_name(association: WorldUserAssociation):
    return get_inventory_room_name_raw(association.world.uuid, association.user.id)


def get_membership_for(sio_or_user: ServerApp | database.User | int, session: int | database.MultiplayerSession
                       ) -> database.MultiplayerMembership:
    if isinstance(sio_or_user, ServerApp):
        user = sio_or_user.get_current_user()
    else:
        user = sio_or_user

    try:
        return database.MultiplayerMembership.get_by_ids(user, session)
    except peewee.DoesNotExist:
        raise error.NotAuthorizedForActionError()


def emit_inventory_update(association: WorldUserAssociation):
    if association.inventory is None:
        return

    flask_socketio.emit(signals.WORLD_BINARY_INVENTORY,
                        (str(association.world.uuid), association.user.id, association.inventory),
                        room=get_inventory_room_name(association),
                        namespace="/")
    # try:
    #     inventory: RemoteInventory = construct_pack.decode(association.inventory, RemoteInventory)
    #     flask_socketio.emit(
    #         signals.WORLD_JSON_INVENTORY,
    #         (association.world.uuid, association.user.id, {
    #             name: {"amount": item.amount, "capacity": item.capacity}
    #             for name, item in inventory.items()
    #         }),
    #         room=get_inventory_room_name(association),
    #         namespace="/"
    #     )
    # except construct.ConstructError as e:
    #     logger().warning("Unable to encode inventory for world %s, user %d: %s",
    #                      association.world.uuid, association.user.id, str(e))


def describe_session(session: MultiplayerSession, world: World | None = None) -> str:
    if world is not None:
        return f"Session {session.id} ({session.name}), World {world.name}"
    else:
        return f"Session {session.id} ({session.name})"


def emit_session_meta_update(session: MultiplayerSession):
    with sentry_sdk.start_span(op="emit", description="session_meta_update") as span:
        span.set_data("session.id", session.id)
        span.set_data("session.name", session.name)
        logger().debug("multiplayer_session_meta_update for session %d (%s)", session.id, session.name)
        emit_session_global_event(session, signals.SESSION_META_UPDATE, session.create_session_entry().as_json)


def emit_session_actions_update(session: MultiplayerSession):
    with sentry_sdk.start_span(op="emit", description="session_actions_update") as span:
        logger().debug("multiplayer_session_actions_update for session %d (%s)", session.id, session.name)
        actions = session.describe_actions()

        span.set_data("session.id", session.id)
        span.set_data("session.name", session.name)
        span.set_data("session.actions", len(actions.actions))
        emit_session_global_event(session, signals.SESSION_ACTIONS_UPDATE,
                                  construct_pack.encode(actions))


def emit_session_audit_update(session: MultiplayerSession):
    with sentry_sdk.start_span(op="emit", description="session_audit_update") as span:
        logger().debug("multiplayer_session_audit_update for session %d (%s)", session.id, session.name)
        log = session.get_audit_log()

        span.set_data("session.id", session.id)
        span.set_data("session.name", session.name)
        span.set_data("session.audit", len(log.entries))
        emit_session_global_event(session, signals.SESSION_AUDIT_UPDATE,
                                  construct_pack.encode(log))


def add_audit_entry(sio: ServerApp, session: MultiplayerSession, message: str):
    MultiplayerAuditEntry.create(
        session=session,
        user=sio.get_current_user(),
        message=message
    )
    emit_session_audit_update(session)


def hash_password(password: str) -> str:
    return hashlib.blake2s(password.encode("utf-8")).hexdigest()


def join_room(sio: ServerApp, session: MultiplayerSession):
    room_name = room_name_for(session.id)
    flask_socketio.join_room(room_name)

    with sio.session() as sio_session:
        if "multiplayer_sessions" not in sio_session:
            sio_session["multiplayer_sessions"] = []

        if session.id not in sio_session["multiplayer_sessions"]:
            sio_session["multiplayer_sessions"].append(session.id)


def leave_room(sio: ServerApp, session_id: int):
    flask_socketio.leave_room(room_name_for(session_id))

    with sio.session() as sio_session:
        if "multiplayer_sessions" in sio_session:
            if session_id in sio_session["multiplayer_sessions"]:
                sio_session["multiplayer_sessions"].remove(session_id)


def leave_all_rooms(sio: ServerApp):
    with sio.session() as sio_session:
        multiplayer_sessions: list[int] = sio_session.pop("multiplayer_sessions", [])

    for session_id in multiplayer_sessions:
        flask_socketio.leave_room(room_name_for(session_id))
