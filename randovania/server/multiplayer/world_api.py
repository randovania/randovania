import base64
import datetime
import logging
import uuid

import flask_socketio
import peewee
from frozendict import frozendict

from randovania.bitpacking import bitpacking
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.layout.layout_description import LayoutDescription
from randovania.network_common import signals, error
from randovania.network_common.error import InvalidAction
from randovania.network_common.pickup_serializer import BitPackPickupEntry
from randovania.network_common.session_state import MultiplayerSessionState
from randovania.network_common.world_sync import ServerSyncRequest, ServerSyncResponse, ServerWorldResponse
from randovania.server.database import (
    World, WorldUserAssociation, MultiplayerSession,
    WorldAction, User
)
from randovania.server.lib import logger
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp


def _get_world_room(world: World):
    return f"world-{world.uuid}"


def _base64_encode_pickup(pickup: PickupEntry, resource_database: ResourceDatabase) -> str:
    encoded_pickup = bitpacking.pack_value(BitPackPickupEntry(pickup, resource_database))
    return base64.b85encode(encoded_pickup).decode("utf-8")


def _get_resource_database(description: LayoutDescription, player: int) -> ResourceDatabase:
    return default_database.resource_database_for(description.get_preset(player).game)


def _get_pickup_target(description: LayoutDescription, provider: int, location: int) -> PickupTarget | None:
    pickup_assignment = description.all_patches[provider].pickup_assignment
    return pickup_assignment.get(PickupIndex(location))


def _collect_location(session: MultiplayerSession, world: World,
                      description: LayoutDescription,
                      pickup_location: int) -> World | None:
    """
    Collects the pickup in the given location. Returns
    :param session:
    :param world:
    :param description:
    :param pickup_location:
    :return: The rewarded player if some player must be updated of the fact.
    """
    pickup_target = _get_pickup_target(description, world.order, pickup_location)

    def log(msg):
        logger().info(f"{session_common.describe_session(session, world)} found item at {pickup_location}. {msg}")

    if pickup_target is None:
        log("It's nothing.")
        return None

    if pickup_target.player == world.order:
        log(f"It's a {pickup_target.pickup.name} for themselves.")
        return None

    target_world = World.get_by_order(session.id, pickup_target.player)

    try:
        WorldAction.create(
            provider=world,
            location=pickup_location,

            session=session,
            receiver=target_world,
        )
    except peewee.IntegrityError:
        # Already exists, and it's for another player, no inventory update needed
        log(f"It's a {pickup_target.pickup.name} for {target_world.name}, but it was already collected.")
        return None

    log(f"It's a {pickup_target.pickup.name} for {target_world.name}.")
    return target_world


def collect_locations(sio: ServerApp, source_world: World, pickup_locations: tuple[int, ...],
                      ) -> set[World]:
    session = source_world.session

    if session.state != MultiplayerSessionState.IN_PROGRESS:
        raise InvalidAction("Unable to collect locations of sessions that aren't in progress")

    logger().info(f"{session_common.describe_session(session, source_world)} found items {pickup_locations}")
    description = session.layout_description

    receiver_worlds = set()
    for location in pickup_locations:
        target_world = _collect_location(session, source_world, description, location)
        if target_world is not None:
            receiver_worlds.add(target_world)

    return receiver_worlds


def update_association(user: User, world: World, inventory: bytes | None,
                       connection_state: GameConnectionStatus, ) -> int | None:
    association = WorldUserAssociation.get_by_instances(world=world, user=user)
    session = association.world.session

    new_inventory = False
    association.connection_state = connection_state
    if session.state == MultiplayerSessionState.IN_PROGRESS and inventory is not None:
        association.inventory = inventory
        new_inventory = True

    if association.is_dirty():
        association.last_activity = datetime.datetime.now(datetime.timezone.utc)
        association.save()

        if new_inventory:
            session_common.emit_inventory_update(association)

        logger().info(
            "%s has new connection state: %s",
            session_common.describe_session(session, association.world), connection_state.pretty_text,
        )
        return session.id

    return None


def watch_inventory(sio: ServerApp, world_uid: uuid.UUID, user_id: int, watch: bool, binary: bool):
    if watch:
        # current_user = sio.get_current_user()
        # TODO: check if current user belongs to the same session

        association = WorldUserAssociation.get_by_ids(
            world_uid=world_uid,
            user_id=user_id,
        )

        flask_socketio.join_room(session_common.get_inventory_room_name(association))
        session_common.emit_inventory_update(association)
    else:
        # Allow one to stop listening even if you're not allowed to start listening
        flask_socketio.leave_room(session_common.get_inventory_room_name_raw(world_uid, user_id))


def _check_user_is_associated(user: User, world: World):
    try:
        WorldUserAssociation.get_by_ids(
            world_uid=world.uuid,
            user_id=user.id,
        )
    except peewee.DoesNotExist:
        raise error.WorldNotAssociatedError()


def world_sync(sio: ServerApp, request: ServerSyncRequest) -> ServerSyncResponse:
    user = sio.get_current_user()

    world_details = {}
    failed_syncs = {}

    worlds_to_update = set()
    sessions_to_update_actions = set()
    sessions_to_update_meta = set()

    for uid, world_request in request.worlds.items():
        try:
            try:
                world = World.get_by_uuid(uid)
            except peewee.DoesNotExist:
                raise error.WorldDoesNotExistError()

            _check_user_is_associated(user, world)

            if world_request.status == GameConnectionStatus.Disconnected:
                flask_socketio.leave_room(_get_world_room(world))
            else:
                flask_socketio.join_room(_get_world_room(world))
                worlds_to_update.add(world)
                sio.store_world_in_session(world)

            session_id = update_association(user, world, world_request.inventory, world_request.status)
            if session_id is not None:
                sessions_to_update_meta.add(session_id)

            if world_request.request_details:
                world_details[uid] = ServerWorldResponse(
                    world_name=world.name,
                    session=world.session.create_list_entry(),
                )

            # Do this last, as it fails if session is in setup
            if world_request.collected_locations:
                worlds_to_update.update(collect_locations(sio, world, world_request.collected_locations))

        except error.BaseNetworkError as e:
            logger().info("Failed sync for %s: %s", uid, e)
            failed_syncs[uid] = e

        except Exception as e:
            logger().exception("Failed sync for %s: %s", uid, e)
            failed_syncs[uid] = error.ServerError()

    for world in worlds_to_update:
        emit_world_pickups_update(sio, world)
        sessions_to_update_actions.add(world.session.id)

    for session_id in sessions_to_update_meta:
        session_common.emit_session_meta_update(MultiplayerSession.get_by_id(session_id))

    for session_id in sessions_to_update_actions:
        session_common.emit_session_actions_update(MultiplayerSession.get_by_id(session_id))

    return ServerSyncResponse(
        worlds=frozendict(world_details),
        errors=frozendict(failed_syncs),
    )


def emit_world_pickups_update(sio: ServerApp, world: World):
    session = world.session

    if session.state == MultiplayerSessionState.SETUP:
        logger().warning("Attempting to emit pickups for %s during SETUP", world)
        return

    description = session.layout_description
    resource_database = _get_resource_database(description, world.order)

    result = []
    actions: list[WorldAction] = WorldAction.select().where(
        WorldAction.receiver == world).order_by(WorldAction.time.asc())

    for action in actions:
        pickup_target = _get_pickup_target(description, action.provider.order,
                                           action.location)

        if pickup_target is None:
            logging.error(f"Action {action} has a location index with nothing.")
            result.append(None)
        else:
            result.append({
                "provider_name": action.provider.name,
                "pickup": _base64_encode_pickup(pickup_target.pickup, resource_database),
            })

    logger().info(f"{session_common.describe_session(session, world)} "
                  f"notifying {resource_database.game_enum.value} of {len(result)} pickups.")

    data = {
        "world": str(world.uuid),
        "game": resource_database.game_enum.value,
        "pickups": result,
    }
    flask_socketio.emit(signals.WORLD_PICKUPS_UPDATE, data, room=f"world-{world.uuid}")


def report_disconnect(sio: ServerApp, session_dict: dict, log: logging.Logger):
    user_id: int | None = session_dict.get("user-id")
    if user_id is None:
        return

    world_ids: list[int] = session_dict.get("worlds", [])

    log.info(f"User {user_id} is disconnected, disconnecting from sessions: {world_ids}")
    sessions_to_update = {}

    for world_id in world_ids:
        try:
            association = WorldUserAssociation.get_by_instances(
                world=world_id,
                user=user_id,
            )
        except peewee.DoesNotExist:
            continue
        association.connection_state = GameConnectionStatus.Disconnected
        session = association.world.session
        sessions_to_update[session.id] = session
        association.save()

    for session in sessions_to_update.values():
        session_common.emit_session_meta_update(session)


def setup_app(sio: ServerApp):
    sio.on("multiplayer_watch_inventory", watch_inventory)
    sio.on_with_wrapper("multiplayer_world_sync", world_sync)
