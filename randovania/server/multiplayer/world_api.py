import base64
import datetime
import logging
import uuid
from typing import TYPE_CHECKING

import construct
import flask_socketio
import peewee
import sentry_sdk
from frozendict import frozendict

from randovania.bitpacking import bitpacking
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.game import RandovaniaGame
from randovania.layout.layout_description import LayoutDescription
from randovania.network_common import error, remote_inventory, signals
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.pickup_serializer import BitPackPickupEntry
from randovania.network_common.world_sync import (
    ServerSyncRequest,
    ServerSyncResponse,
    ServerWorldResponse,
    ServerWorldSync,
)
from randovania.server.database import MultiplayerSession, User, World, WorldAction, WorldUserAssociation
from randovania.server.lib import logger
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp

if TYPE_CHECKING:
    from collections.abc import Iterable


def _get_world_room(world: World):
    return f"world-{world.uuid}"


def get_inventory_room_name_raw(world_uuid: uuid.UUID, user_id: int):
    return f"multiplayer-{world_uuid}-{user_id}-inventory"


def emit_inventory_update(sa: ServerApp, world: World, user_id: int, inventory: bytes):
    room_name = get_inventory_room_name_raw(world.uuid, user_id)

    sa.sio.emit(
        signals.WORLD_BINARY_INVENTORY,
        (str(world.uuid), user_id, inventory),
        namespace="/",
        to=room_name,
        include_self=True,
    )
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


def _base64_encode_pickup(pickup: PickupEntry, resource_database: ResourceDatabase) -> str:
    encoded_pickup = bitpacking.pack_value(BitPackPickupEntry(pickup, resource_database))
    return base64.b85encode(encoded_pickup).decode("utf-8")


def _get_resource_database(description: LayoutDescription, player: int) -> ResourceDatabase:
    return default_database.resource_database_for(description.get_preset(player).game)


def _get_pickup_target(description: LayoutDescription, provider: int, location: int) -> PickupTarget | None:
    pickup_assignment = description.all_patches[provider].pickup_assignment
    return pickup_assignment.get(PickupIndex(location))


def _add_pickup_to_inventory(inventory: bytes, pickup: PickupEntry, game: RandovaniaGame) -> bytes:
    decoded_or_err = remote_inventory.decode_remote_inventory(inventory)
    if isinstance(decoded_or_err, construct.ConstructError):
        return inventory

    db = default_database.resource_database_for(game)
    collection = ResourceCollection.with_database(db)
    collection.add_resource_gain((db.get_item(name), quantity) for name, quantity in decoded_or_err.items())
    collection.add_resource_gain(pickup.resource_gain(collection))

    return remote_inventory.inventory_to_encoded_remote(Inventory.from_collection(collection))


@sentry_sdk.trace
def _collect_location(
    sa: ServerApp, session: MultiplayerSession, world: World, description: LayoutDescription, pickup_location: int
) -> World | None:
    """
    Collects the pickup in the given location. Returns
    :param session:
    :param world:
    :param description:
    :param pickup_location:
    :return: The rewarded player if some player must be updated of the fact.
    """
    pickup_target = _get_pickup_target(description, world.order, pickup_location)

    def log(msg: str, *args):
        logger().info(
            "%s found item at %d. " + msg, session_common.describe_session(session, world), pickup_location, *args
        )

    if pickup_target is None:
        log("It's nothing.")
        return None

    if pickup_target.player == world.order:
        log("It's a %s for themselves.", pickup_target.pickup.name)
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
        log("It's a %s for %s, but it was already collected.", pickup_target.pickup.name, target_world.name)
        return None

    target_game = description.get_preset(target_world.order).game
    associations: Iterable[WorldUserAssociation] = WorldUserAssociation.select().where(
        WorldUserAssociation.world == target_world,
        WorldUserAssociation.connection_state == GameConnectionStatus.Disconnected,
        WorldUserAssociation.inventory.is_null(False),
    )
    for assoc in associations:
        new_inventory = _add_pickup_to_inventory(assoc.inventory, pickup_target.pickup, target_game)
        if assoc.inventory != new_inventory:
            assoc.inventory = new_inventory
            assoc.save()
            emit_inventory_update(sa, target_world, assoc.user_id, new_inventory)

    log("It's a %s for %s.", pickup_target.pickup.name, target_world.name)
    return target_world


@sentry_sdk.trace
def collect_locations(
    sa: ServerApp,
    source_world: World,
    pickup_locations: tuple[int, ...],
) -> set[World]:
    session = source_world.session

    logger().info(f"{session_common.describe_session(session, source_world)} found items {pickup_locations}")
    description = session.layout_description

    receiver_worlds = set()
    for location in pickup_locations:
        target_world = _collect_location(sa, session, source_world, description, location)
        if target_world is not None:
            receiver_worlds.add(target_world)

    return receiver_worlds


def watch_inventory(sa: ServerApp, world_uid: uuid.UUID, user_id: int, watch: bool, binary: bool):
    logger().debug("Watching inventory of %s/%d: %s", world_uid, user_id, watch)
    room_name = get_inventory_room_name_raw(world_uid, user_id)

    if watch:
        world = World.get_by_uuid(world_uid)
        session_common.get_membership_for(sa, world.session)
        try:
            association = WorldUserAssociation.get_by_instances(world=world, user=user_id)
        except peewee.DoesNotExist:
            raise error.WorldNotAssociatedError

        flask_socketio.join_room(room_name)
        if association.inventory is not None:
            emit_inventory_update(sa, world, user_id, association.inventory)
    else:
        # Allow one to stop listening even if you're not allowed to start listening
        flask_socketio.leave_room(room_name)


def _check_user_is_associated(user: User, world: World) -> WorldUserAssociation:
    try:
        return WorldUserAssociation.get_by_instances(
            world=world,
            user=user,
        )
    except peewee.DoesNotExist:
        raise error.WorldNotAssociatedError


@sentry_sdk.trace
def sync_one_world(
    sa: ServerApp,
    user: User,
    uid: uuid.UUID,
    world_request: ServerWorldSync,
) -> tuple[ServerWorldResponse | None, int | None, set[World]]:
    sentry_sdk.set_tag("world_uuid", str(uid))
    world = World.get_by_uuid(uid)
    sentry_sdk.set_tag("session_id", world.session_id)

    association = _check_user_is_associated(user, world)
    should_update_activity = False
    worlds_to_update = set()
    session_id_to_return = None
    response = None

    # Join/leave room based on status
    if world_request.status == GameConnectionStatus.Disconnected:
        flask_socketio.leave_room(_get_world_room(world))
    else:
        if sa.ensure_in_room(_get_world_room(world)):
            worlds_to_update.add(world)
            sa.store_world_in_session(world)

    # Update association connection state
    if world_request.status != association.connection_state:
        association.connection_state = world_request.status
        should_update_activity = True
        session_id_to_return = world.session_id
        logger().info(
            "Session %d, World %s has new connection state: %s",
            world.session_id,
            world.name,
            world_request.status.pretty_text,
        )

    # Update association inventory
    if world_request.inventory is not None and world_request.inventory != association.inventory:
        association.inventory = world_request.inventory
        should_update_activity = True
        emit_inventory_update(sa, world, user.id, world_request.inventory)
        logger().info(
            "Session %d, World %s has new inventory",
            world.session_id,
            world.name,
        )

    if world_request.request_details:
        response = ServerWorldResponse(
            world_name=world.name,
            session_id=world.session_id,
            session_name=world.session.name,
        )

    # Do this last, as it fails if session is in setup
    if world_request.collected_locations:
        worlds_to_update.update(collect_locations(sa, world, world_request.collected_locations))
        should_update_activity = True

    # User did something, so update activity
    if should_update_activity:
        association.last_activity = datetime.datetime.now(datetime.UTC)
        association.save()

    return response, session_id_to_return, worlds_to_update


def world_sync(sa: ServerApp, request: ServerSyncRequest) -> ServerSyncResponse:
    user = sa.get_current_user()

    world_details = {}
    failed_syncs = {}

    worlds_to_update = set()
    sessions_to_update_actions = set()
    sessions_to_update_meta = set()

    for uid, world_request in request.worlds.items():
        try:
            response, session_id, new_worlds_to_update = sync_one_world(sa, user, uid, world_request)

            if response is not None:
                world_details[uid] = response

            if session_id is not None:
                sessions_to_update_meta.add(session_id)

            worlds_to_update.update(new_worlds_to_update)

        except error.BaseNetworkError as e:
            logger().info("[%s] Refused sync for %s: %s", user.name, uid, e)
            failed_syncs[uid] = e

        except Exception as e:
            logger().exception("[%s] Failed sync for %s: %s", user.name, uid, e)
            failed_syncs[uid] = error.ServerError()

    for world in worlds_to_update:
        emit_world_pickups_update(sa, world)
        sessions_to_update_actions.add(world.session.id)

    for session_id in sessions_to_update_meta:
        session_common.emit_session_meta_update(MultiplayerSession.get_by_id(session_id))

    for session_id in sessions_to_update_actions:
        session_common.emit_session_actions_update(MultiplayerSession.get_by_id(session_id))

    return ServerSyncResponse(
        worlds=frozendict(world_details),
        errors=frozendict(failed_syncs),
    )


@sentry_sdk.trace
def emit_world_pickups_update(sa: ServerApp, world: World):
    session = world.session

    description = session.layout_description
    resource_database = _get_resource_database(description, world.order)

    result = []
    actions: list[WorldAction] = (
        WorldAction.select(
            WorldAction.location,
            World.order,
            World.name,
        )
        .join(World, on=WorldAction.provider)
        .where(WorldAction.receiver == world)
        .order_by(WorldAction.time.asc())
    )

    for action in actions:
        pickup_target = _get_pickup_target(description, action.provider.order, action.location)

        if pickup_target is None:
            result.append(None)
        else:
            result.append(
                {
                    "provider_name": action.provider.name,
                    "pickup": _base64_encode_pickup(pickup_target.pickup, resource_database),
                }
            )

    logger().info(
        "%s notifying %s of %s pickups.",
        session_common.describe_session(session, world),
        resource_database.game_enum.value,
        len(result),
    )

    data = {
        "world": str(world.uuid),
        "game": resource_database.game_enum.value,
        "pickups": result,
    }
    flask_socketio.emit(signals.WORLD_PICKUPS_UPDATE, data, room=_get_world_room(world))


def report_disconnect(sa: ServerApp, session_dict: dict, log: logging.Logger):
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


def setup_app(sa: ServerApp):
    sa.on("multiplayer_watch_inventory", watch_inventory)
    sa.on_with_wrapper("multiplayer_world_sync", world_sync)
