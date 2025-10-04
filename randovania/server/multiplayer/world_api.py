import base64
import datetime
import uuid

import construct
import peewee
import sentry_sdk
from frozendict import frozendict

from randovania.bitpacking import bitpacking
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
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
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp


def _get_world_room(world: World) -> str:
    return f"world-{world.uuid}"


def get_inventory_room_name_raw(world_uuid: uuid.UUID, user_id: int) -> str:
    return f"multiplayer-{world_uuid}-{user_id}-inventory"


async def emit_inventory_update(sa: ServerApp, world: World, user_id: int, inventory: bytes) -> None:
    room_name = get_inventory_room_name_raw(world.uuid, user_id)

    await sa.sio.emit(
        signals.WORLD_BINARY_INVENTORY,
        (str(world.uuid), user_id, inventory),
        namespace="/",
        to=room_name,
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
    #     sa.logger.warning("Unable to encode inventory for world %s, user %d: %s",
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

    game_view = game.game_description
    collection = game_view.create_resource_collection()
    collection.add_resource_gain(
        (game_view.get_resource_database_view().get_item(name), quantity) for name, quantity in decoded_or_err.items()
    )
    collection.add_resource_gain(pickup.resource_gain(collection))

    return remote_inventory.inventory_to_encoded_remote(Inventory.from_collection(collection))


@sentry_sdk.trace
async def _collect_location(
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
    assert world.order is not None
    pickup_target = _get_pickup_target(description, world.order, pickup_location)

    def log(msg: str, *args: object) -> None:
        sa.logger.info(
            "%s found item at %d. " + msg,
            session_common.describe_session(session, world),
            pickup_location,
            *args,
            extra={
                "session_id": session.id,
                "world_uuid": str(world.uuid),
            },
        )

    if pickup_target is None:
        log("It's nothing.")
        return None

    if pickup_target.player == world.order and not session.allow_coop:
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

    assert target_world.order is not None
    target_game = description.get_preset(target_world.order).game
    associations = WorldUserAssociation.select().where(
        WorldUserAssociation.world == target_world,
        WorldUserAssociation.connection_state == GameConnectionStatus.Disconnected,
        WorldUserAssociation.inventory.is_null(False),  # type: ignore[attr-defined]
    )
    for assoc in associations:
        new_inventory = _add_pickup_to_inventory(assoc.inventory, pickup_target.pickup, target_game)
        if assoc.inventory != new_inventory:
            assoc.inventory = new_inventory
            assoc.save()
            await emit_inventory_update(sa, target_world, assoc.user_id, new_inventory)

    log("It's a %s for %s.", pickup_target.pickup.name, target_world.name)
    return target_world


@sentry_sdk.trace
async def collect_locations(
    sa: ServerApp,
    source_world: World,
    pickup_locations: tuple[int, ...],
) -> set[World]:
    session = source_world.session

    sa.logger.info(f"{session_common.describe_session(session, source_world)} found items {pickup_locations}")
    description = session.layout_description
    assert description is not None

    receiver_worlds = set()
    for location in pickup_locations:
        target_world = await _collect_location(sa, session, source_world, description, location)
        if target_world is not None:
            receiver_worlds.add(target_world)

    return receiver_worlds


async def watch_inventory(
    sa: ServerApp, sid: str, world_uid: uuid.UUID, user_id: int, watch: bool, binary: bool
) -> None:
    sa.logger.debug("Watching inventory of %s/%d: %s", world_uid, user_id, watch)
    room_name = get_inventory_room_name_raw(world_uid, user_id)

    if watch:
        world = World.get_by_uuid(world_uid)
        await session_common.get_membership_for(sa, world.session, sid)
        try:
            association = WorldUserAssociation.get_by_instances(world=world, user=user_id)
        except peewee.DoesNotExist:
            raise error.WorldNotAssociatedError

        await sa.sio.enter_room(sid, room_name)
        if association.inventory is not None:
            await emit_inventory_update(sa, world, user_id, association.inventory)
    else:
        # Allow one to stop listening even if you're not allowed to start listening
        await sa.sio.leave_room(sid, room_name)


def _check_user_is_associated(user: User, world: World) -> WorldUserAssociation:
    try:
        return WorldUserAssociation.get_by_instances(
            world=world,
            user=user,
        )
    except peewee.DoesNotExist:
        raise error.WorldNotAssociatedError


@sentry_sdk.trace
async def sync_one_world(
    sa: ServerApp,
    sid: str,
    user: User,
    uid: uuid.UUID,
    world_request: ServerWorldSync,
) -> tuple[ServerWorldResponse | None, int | None, set[World]]:
    sentry_sdk.set_tag("world_uuid", str(uid))
    world = World.get_by_uuid(uid)
    sentry_sdk.set_tag("session_id", world.session_id)
    session = MultiplayerSession.get_by_id(world.session_id)

    association = _check_user_is_associated(user, world)
    should_update_activity = False
    worlds_to_emit_update = set()
    session_id_to_return = None
    response = None

    # Join/leave room based on status
    if world_request.status == GameConnectionStatus.Disconnected:
        await sa.sio.leave_room(sid, _get_world_room(world))
    else:
        if await sa.ensure_in_room(sid, _get_world_room(world)):
            worlds_to_emit_update.add(world)
            await sa.store_world_in_session(sid, world)

    # Update association connection state
    if world_request.status != association.connection_state:
        association.connection_state = world_request.status
        should_update_activity = True
        session_id_to_return = world.session_id
        sa.logger.info(
            "Session %d, World %s has new connection state: %s",
            world.session_id,
            world.name,
            world_request.status.pretty_text,
            extra={
                "session_id": world.session_id,
                "world_uuid": str(world.uuid),
            },
        )

    # Update association inventory
    if world_request.inventory is not None and world_request.inventory != association.inventory:
        association.inventory = world_request.inventory
        should_update_activity = True
        await emit_inventory_update(sa, world, user.id, world_request.inventory)
        sa.logger.info(
            "Session %d, World %s has new inventory",
            world.session_id,
            world.name,
            extra={
                "session_id": world.session_id,
                "world_uuid": str(world.uuid),
            },
        )

    if world_request.request_details:
        response = ServerWorldResponse(
            world_name=world.name,
            session_id=world.session_id,
            session_name=world.session.name,
        )

    # Do this last, as it fails if session is in setup
    if world_request.collected_locations:
        worlds_to_emit_update.update(await collect_locations(sa, world, world_request.collected_locations))
        should_update_activity = True

    # User has beaten game, so toggle it. The Beat-Game status can not be disabled.
    if world_request.has_been_beaten and not world.beaten:
        sa.logger.info("Session %d, World %s has been beaten", world.session_id, world.name)
        world.beaten = True
        world.save()
        await session_common.add_audit_entry(sa, sid, session, f"World {world.name} has been beaten.")
        worlds_to_emit_update.add(world)
        should_update_activity = True

    # User did something, so update activity
    if should_update_activity:
        association.last_activity = datetime.datetime.now(datetime.UTC)
        association.save()

    return response, session_id_to_return, worlds_to_emit_update


async def world_sync(sa: ServerApp, sid: str, request: ServerSyncRequest) -> ServerSyncResponse:
    user = await sa.get_current_user(sid)

    world_details = {}
    failed_syncs = {}

    worlds_to_emit_update = set()
    sessions_to_update_actions = set()
    sessions_to_update_meta = set()

    for uid, world_request in request.worlds.items():
        try:
            response, session_id, new_worlds_to_emit_update = await sync_one_world(sa, sid, user, uid, world_request)

            if response is not None:
                world_details[uid] = response

            if session_id is not None:
                sessions_to_update_meta.add(session_id)

            worlds_to_emit_update.update(new_worlds_to_emit_update)

        except error.BaseNetworkError as e:
            sa.logger.info(
                "[%s] Refused sync for %s: %s",
                user.name,
                uid,
                e,
                extra={
                    "user_id": user.id,
                    "world_uuid": str(uid),
                },
            )
            failed_syncs[uid] = e

        except Exception as e:
            sa.logger.exception(
                "[%s] Failed sync for %s: %s",
                user.name,
                uid,
                e,
                extra={
                    "user_id": user.id,
                    "world_uuid": str(uid),
                },
            )
            failed_syncs[uid] = error.ServerError()

    for world in worlds_to_emit_update:
        await emit_world_pickups_update(sa, world)
        sessions_to_update_actions.add(world.session.id)

    for session_id in sessions_to_update_meta:
        await session_common.emit_session_meta_update(sa, MultiplayerSession.get_by_id(session_id))

    for session_id in sessions_to_update_actions:
        await session_common.emit_session_actions_update(sa, MultiplayerSession.get_by_id(session_id))

    return ServerSyncResponse(
        worlds=frozendict(world_details),
        errors=frozendict(failed_syncs),
    )


@sentry_sdk.trace
async def emit_world_pickups_update(sa: ServerApp, world: World) -> None:
    session = world.session

    assert session.layout_description is not None
    description = session.layout_description

    assert world.order is not None
    resource_database = _get_resource_database(description, world.order)

    result: list[dict | None] = []
    actions: list[WorldAction] = (
        WorldAction.select(
            WorldAction.location,
            World.order,
            World.name,
            World.uuid,
        )
        .join(World, on=WorldAction.provider)
        .where(WorldAction.receiver == world)
        .order_by(WorldAction.time.asc())  # type: ignore[attr-defined]
    )

    for action in actions:
        assert action.provider.order is not None
        pickup_target = _get_pickup_target(description, action.provider.order, action.location)

        if pickup_target is None:
            result.append(None)
        else:
            result.append(
                {
                    "provider_name": action.provider.name,
                    "pickup": _base64_encode_pickup(pickup_target.pickup, resource_database),
                    "coop_location": action.location if action.provider.uuid == world.uuid else None,
                }
            )

    sa.logger.info(
        "%s notifying %s of %s pickups.",
        session_common.describe_session(session, world),
        resource_database.game_enum.value,
        len(result),
        extra={
            "session_id": world.session_id,
            "world_uuid": str(world.uuid),
        },
    )

    data = {
        "world": str(world.uuid),
        "game": resource_database.game_enum.value,
        "pickups": result,
    }
    await sa.sio.emit(signals.WORLD_PICKUPS_UPDATE, data, room=_get_world_room(world))


async def report_disconnect(sa: ServerApp, session_dict: dict) -> None:
    user_id: int | None = session_dict.get("user-id")
    if user_id is None:
        return

    world_ids: list[int] = session_dict.get("worlds", [])

    sa.logger.info(f"User {user_id} is disconnected, disconnecting from sessions: {world_ids}")
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
        await session_common.emit_session_meta_update(sa, session)


def setup_app(sa: ServerApp) -> None:
    sa.on("multiplayer_watch_inventory", watch_inventory)
    sa.on_with_wrapper("multiplayer_world_sync", world_sync)
