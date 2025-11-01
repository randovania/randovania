import json
import typing
import uuid

import peewee

import randovania
from randovania import monitoring
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import InvalidLayoutDescription, LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import error
from randovania.network_common.admin_actions import SessionAdminGlobalAction, SessionAdminUserAction
from randovania.network_common.multiplayer_session import MAX_SESSION_NAME_LENGTH, WORLD_NAME_RE
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database
from randovania.server.database import (
    MultiplayerAuditEntry,
    MultiplayerMembership,
    MultiplayerSession,
    World,
    WorldAction,
    WorldUserAssociation,
    is_boolean,
)
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp


async def _check_user_associated_with(sa: ServerApp, sid: str, world: World) -> None:
    try:
        WorldUserAssociation.get(
            WorldUserAssociation.world == world,
            WorldUserAssociation.user == await sa.get_current_user(sid),
        )
    except peewee.DoesNotExist:
        raise error.NotAuthorizedForActionError


async def verify_has_admin(
    sa: ServerApp, sid: str, session_id: int, admin_user_id: int | None, *, allow_when_no_admins: bool = False
) -> None:
    """
    Checks if the logged user can do admin operations to the given session,
    :param sa:
    :param session_id: The GameSessions id.
    :param admin_user_id: An user id that is exceptionally authorized for this.
    :param allow_when_no_admins: This action is authorized for non-admins if there are no admins.
    :return:
    """
    current_user = await sa.get_current_user(sid)
    current_membership = await session_common.get_membership_for(current_user, session_id, sid)

    if not (current_membership.admin or (admin_user_id is not None and current_user.id == admin_user_id)):
        if (
            allow_when_no_admins
            and MultiplayerMembership.select()
            .where(MultiplayerMembership.session == session_id, is_boolean(MultiplayerMembership.admin, True))
            .count()
            == 0
        ):
            return
        raise error.NotAuthorizedForActionError


async def verify_has_admin_or_claimed(sa: ServerApp, sid: str, world: World) -> None:
    """
    Checks if the logged user can do admin operations to the given session,
    :param sa:
    :param world:
    :return:
    """
    current_membership = await session_common.get_membership_for(sa, world.session, sid)

    if not current_membership.admin:
        await _check_user_associated_with(sa, sid, world)


def _verify_world_has_session(world: World, session: MultiplayerSession) -> None:
    if world.session_id != session.id:
        raise error.InvalidActionError("Wrong session")


def _verify_no_layout_description(session: MultiplayerSession) -> None:
    if session.layout_description_json is not None:
        raise error.InvalidActionError("Session has a generated game")


def _verify_not_in_generation(session: MultiplayerSession) -> None:
    if session.generation_in_progress is not None:
        raise error.InvalidActionError("Session game is being generated")


def _get_preset(preset_bytes: bytes) -> VersionedPreset:
    try:
        preset: VersionedPreset = VersionedPreset.from_bytes(preset_bytes)
        preset.get_preset()  # test if valid
        return preset
    except Exception as e:
        raise error.InvalidActionError(f"invalid preset: {e}")


def _verify_preset_allowed_for(preset: VersionedPreset, session: MultiplayerSession) -> None:
    if preset.game not in session.allowed_games:
        raise error.InvalidActionError(f"{preset.game.long_name} not allowed.")

    if not randovania.is_dev_version() and preset.get_preset().configuration.unsupported_features():
        raise error.InvalidActionError("Preset uses unsupported features.")


async def _create_world(
    sa: ServerApp, sid: str, session: MultiplayerSession, name: str, preset_bytes: bytes, *, for_user: int | None = None
) -> World:
    await verify_has_admin(sa, sid, session.id, for_user)

    _verify_no_layout_description(session)
    _verify_not_in_generation(session)
    preset = _get_preset(preset_bytes)

    _verify_preset_allowed_for(preset, session)

    if WORLD_NAME_RE.match(name) is None:
        raise error.InvalidActionError("Invalid world name")

    if any(name == world.name for world in session.worlds):
        raise error.InvalidActionError("World name already exists")

    sa.logger.info(f"{session_common.describe_session(session)}: Creating world {name}.")

    world = World.create_for(session=session, name=name, preset=preset)
    await session_common.add_audit_entry(sa, sid, session, f"Created new world {world.name}")
    return world


async def _change_world(
    sa: ServerApp, sid: str, session: MultiplayerSession, world_uid: uuid.UUID, preset_bytes: bytes
) -> None:
    world = World.get_by_uuid(world_uid)

    _verify_no_layout_description(session)
    _verify_not_in_generation(session)
    preset = _get_preset(preset_bytes)

    _verify_world_has_session(world, session)
    await verify_has_admin_or_claimed(sa, sid, world)

    _verify_preset_allowed_for(preset, session)

    try:
        with database.db.atomic():
            world.preset = json.dumps(preset.as_json)
            sa.logger.info(f"{session_common.describe_session(session)}: Changing world {world_uid}.")
            world.save()
            await session_common.add_audit_entry(sa, sid, session, f"Changing world {world.name}")

    except peewee.DoesNotExist:
        raise error.InvalidActionError(f"invalid world: {world_uid}")


async def _rename_world(
    sa: ServerApp, sid: str, session: MultiplayerSession, world_uid: uuid.UUID, new_name: str
) -> None:
    world = World.get_by_uuid(world_uid)
    _verify_world_has_session(world, session)
    await verify_has_admin_or_claimed(sa, sid, world)

    if WORLD_NAME_RE.match(new_name) is None:
        raise error.InvalidActionError("Invalid world name")

    if any(new_name == world.name for world in session.worlds):
        raise error.InvalidActionError("World name already exists")

    with database.db.atomic():
        sa.logger.info(
            f"{session_common.describe_session(session)}: Renaming {world.name} ({world_uid}) to {new_name}."
        )
        await session_common.add_audit_entry(sa, sid, session, f"Renaming world {world.name} to {new_name}")
        world.name = new_name
        world.save()


async def _delete_world(sa: ServerApp, sid: str, session: MultiplayerSession, world_uid: str) -> None:
    world = World.get_by_uuid(world_uid)

    await verify_has_admin_or_claimed(sa, sid, world)
    _verify_world_has_session(world, session)
    _verify_no_layout_description(session)
    _verify_not_in_generation(session)

    world = World.get_by_uuid(world_uid)
    with database.db.atomic():
        sa.logger.info(f"{session_common.describe_session(session)}: Deleting {world.name} ({world_uid}).")
        await session_common.add_audit_entry(sa, sid, session, f"Deleting world {world.name}")
        WorldUserAssociation.delete().where(WorldUserAssociation.world == world.id).execute()
        world.delete_instance()


async def _update_layout_generation(
    sa: ServerApp, sid: str, session: MultiplayerSession, world_order: list[str]
) -> None:
    await verify_has_admin(sa, sid, session.id, None)

    world_objects: dict[str, World] = {str(world.uuid): world for world in session.worlds}
    if world_order:
        _verify_no_layout_description(session)
        used_ids = set(world_objects.keys())
        for world_uuid in world_order:
            if world_uuid not in used_ids:
                raise error.InvalidActionError(f"World {world_uuid} duplicated in order, or unknown.")
            used_ids.remove(world_uuid)

        if used_ids:
            raise error.InvalidActionError(f"Expected {len(world_objects)} worlds, got {len(world_order)}.")

        if session.generation_in_progress is not None:
            raise error.InvalidActionError(f"Generation already in progress by {session.generation_in_progress.name}.")

    with database.db.atomic():
        if world_order:
            session.generation_in_progress = await sa.get_current_user(sid)
            objects_to_save = []
            for i, world_uuid in enumerate(world_order):
                world_obj = world_objects[world_uuid]
                world_obj.order = i
                objects_to_save.append(world_obj)

            World.bulk_update(objects_to_save, fields=[World.order], batch_size=50)

        else:
            session.generation_in_progress = None

        sa.logger.info(
            "%s: Making generation in progress to %s",
            session_common.describe_session(session),
            str(session.generation_in_progress),
        )
        session.save()


async def _change_layout_description(
    sa: ServerApp, sid: str, session: MultiplayerSession, description_bytes: bytes | None
) -> None:
    await verify_has_admin(sa, sid, session.id, None)
    worlds_to_update = []

    if description_bytes is None:
        if not session.has_layout_description():
            return

        description = None
        for world in session.worlds:
            world.uuid = uuid.uuid4()
            world.beaten = False
            worlds_to_update.append(world)

    else:
        if session.generation_in_progress != await sa.get_current_user(sid):
            if session.generation_in_progress is None:
                raise error.InvalidActionError("Not waiting for a layout.")
            else:
                raise error.InvalidActionError(f"Waiting for a layout from {session.generation_in_progress.name}.")

        _verify_no_layout_description(session)
        worlds = session.get_ordered_worlds()
        if any(world.order is None for world in worlds):
            raise error.InvalidActionError("One of the worlds has undefined order field.")

        try:
            description = LayoutDescription.from_bytes(
                description_bytes, presets=[VersionedPreset.from_str(world.preset) for world in worlds]
            )
        except InvalidLayoutDescription as e:
            raise error.InvalidActionError(f"Invalid layout: {e}") from e
        except ValueError as e:
            raise error.InvalidActionError("Presets do not match layout") from e

    with database.db.atomic():
        if worlds_to_update:
            # Delete all collected locations. This is only relevant when removing a layout description, and since we're
            # also creating new layout uuids there's no problem with already exported worlds
            WorldAction.delete().where(WorldAction.session == session).execute()

        for world in worlds_to_update:
            world.save()

        session.generation_in_progress = None
        session.layout_description = description
        session.save()

        await session_common.emit_session_actions_update(sa, session)
        await session_common.add_audit_entry(
            sa,
            sid,
            session,
            "Removed generated game" if description is None else f"Set game to {description.shareable_word_hash}",
        )


async def _download_layout_description(sa: ServerApp, sid: str, session: MultiplayerSession) -> bytes:
    # You must be a session member to do get the spoiler
    await session_common.get_membership_for(sa, session, sid)

    if not session.has_layout_description():
        raise error.InvalidActionError("Session does not contain a game")

    if not session.game_details().spoiler:  # type: ignore[union-attr]
        raise error.InvalidActionError("Session does not contain a spoiler")

    await session_common.add_audit_entry(sa, sid, session, "Requested the spoiler log")
    return session.get_layout_description_as_binary()  # type: ignore[return-value]


async def _change_visibility(sa: ServerApp, sid: str, session: MultiplayerSession, new_visibility: str) -> None:
    await verify_has_admin(sa, sid, session.id, None)
    new_visibility_ = MultiplayerSessionVisibility(new_visibility)

    session.visibility = new_visibility_
    sa.logger.info("%s: Changing visibility to %s.", session_common.describe_session(session), new_visibility_)
    session.save()
    await session_common.add_audit_entry(
        sa, sid, session, f"Changed visibility to {new_visibility_.user_friendly_name}"
    )


async def _change_password(sa: ServerApp, sid: str, session: MultiplayerSession, password: str) -> None:
    await verify_has_admin(sa, sid, session.id, None)

    session.password = session_common.hash_password(password)
    sa.logger.info(f"{session_common.describe_session(session)}: Changing password.")
    session.save()
    await session_common.add_audit_entry(sa, sid, session, "Changed password")


async def _change_title(sa: ServerApp, sid: str, session: MultiplayerSession, title: str) -> None:
    await verify_has_admin(sa, sid, session.id, None)

    if not (0 < len(title) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    old_name = session.name
    session.name = title
    sa.logger.info(f"{session_common.describe_session(session)}: Changed name from {old_name}.")
    session.save()
    await session_common.add_audit_entry(sa, sid, session, f"Changed name from {old_name} to {title}")


async def _duplicate_session(sa: ServerApp, sid: str, session: MultiplayerSession, new_title: str) -> None:
    await verify_has_admin(sa, sid, session.id, None)

    if not (0 < len(new_title) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    current_user = await sa.get_current_user(sid)
    await session_common.add_audit_entry(sa, sid, session, f"Duplicated session as {new_title}")

    with database.db.atomic():
        new_session: MultiplayerSession = MultiplayerSession.create(
            name=new_title,
            password=session.password,
            creator=current_user,
            layout_description_json=session.layout_description_json,
            game_details_json=session.game_details_json,
            dev_features=session.dev_features,
            allow_coop=session.allow_coop,
            allow_everyone_claim_world=session.allow_everyone_claim_world,
        )
        for world in session.worlds:
            assert isinstance(world, World)
            World.create(
                session=new_session,
                name=world.name,
                preset=world.preset,
                order=world.order,
            )
        MultiplayerMembership.create(
            user=current_user,
            session=new_session,
            admin=True,
        )
        MultiplayerAuditEntry.create(
            session=new_session,
            user=current_user,
            message=f"Duplicated from {session.name}",
        )


async def _get_permalink(sa: ServerApp, sid: str, session: MultiplayerSession) -> str:
    await verify_has_admin(sa, sid, session.id, None)

    if not session.has_layout_description():
        raise error.InvalidActionError("Session does not contain a game")
    assert session.layout_description is not None

    await session_common.add_audit_entry(sa, sid, session, "Requested permalink")
    return session.layout_description.permalink.as_base64_str


async def admin_session(sa: ServerApp, sid: str, session_id: int, action: str, *args: typing.Any) -> typing.Any:
    monitoring.set_tag("action", action)

    action_ = SessionAdminGlobalAction(action)
    session: database.MultiplayerSession = database.MultiplayerSession.get_by_id(session_id)

    if action_ == SessionAdminGlobalAction.CREATE_WORLD:
        await _create_world(sa, sid, session, *args, for_user=None)

    elif action_ == SessionAdminGlobalAction.CHANGE_WORLD:
        await _change_world(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.RENAME_WORLD:
        await _rename_world(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.DELETE_WORLD:
        await _delete_world(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION:
        await _update_layout_generation(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION:
        await _change_layout_description(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION:
        return await _download_layout_description(sa, sid, session)

    elif action_ == SessionAdminGlobalAction.CHANGE_VISIBILITY:
        await _change_visibility(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.CHANGE_PASSWORD:
        await _change_password(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.CHANGE_TITLE:
        await _change_title(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.DUPLICATE_SESSION:
        return await _duplicate_session(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.DELETE_SESSION:
        sa.logger.info(f"{session_common.describe_session(session)}: Deleting session.")
        session.delete_instance(recursive=True)

    elif action_ == SessionAdminGlobalAction.REQUEST_PERMALINK:
        return await _get_permalink(sa, sid, session)

    elif action_ == SessionAdminGlobalAction.CREATE_PATCHER_FILE:
        return await _create_patcher_file(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.SET_ALLOW_COOP:
        await _set_allow_coop(sa, sid, session, *args)

    elif action_ == SessionAdminGlobalAction.SET_ALLOW_EVERYONE_CLAIM:
        await _set_allow_everyone_claim(sa, sid, session, *args)

    await session_common.emit_session_meta_update(sa, session)


async def _kick_user(
    sa: ServerApp, sid: str, session: MultiplayerSession, membership: MultiplayerMembership, user_id: int
) -> None:
    await session_common.add_audit_entry(
        sa,
        sid,
        session,
        f"Kicked {membership.effective_name}"
        if membership.user != (await sa.get_current_user(sid))
        else "Left session",
    )

    with database.db.atomic():
        for association in (
            WorldUserAssociation.select()
            .join(World)
            .where(
                World.session == session.id,
                WorldUserAssociation.user == user_id,
            )
        ):
            association.delete_instance()
        membership.delete_instance()
        if not list(session.members):
            session.delete_instance(recursive=True)
            sa.logger.info(f"{session_common.describe_session(session)}. Kicking user {user_id} and deleting session.")
        else:
            sa.logger.info(f"{session_common.describe_session(session)}. Kicking user {user_id}.")


async def _create_world_for(
    sa: ServerApp,
    sid: str,
    session: MultiplayerSession,
    membership: MultiplayerMembership,
    name: str,
    preset_bytes: bytes,
) -> None:
    with database.db.atomic():
        new_world = await _create_world(sa, sid, session, name, preset_bytes, for_user=membership.user.id)
        WorldUserAssociation.create(
            world=new_world,
            user=membership.user,
        )
        await session_common.add_audit_entry(
            sa, sid, session, f"Associated new world {new_world.name} for {membership.user.name}"
        )


async def _claim_world(
    sa: ServerApp, sid: str, session: MultiplayerSession, user_id: int, world_uid: uuid.UUID
) -> None:
    if not session.allow_everyone_claim_world:
        await verify_has_admin(sa, sid, session.id, None)

    world = World.get_by_uuid(world_uid)

    if not session.allow_coop:
        for _ in WorldUserAssociation.select().where(WorldUserAssociation.world == world.id):
            raise error.InvalidActionError("World is already claimed")

    WorldUserAssociation.create(
        world=world,
        user=user_id,
    )
    await session_common.add_audit_entry(
        sa, sid, session, f"Associated world {world.name} for {database.User.get_by_id(user_id).name}"
    )


async def _unclaim_world(
    sa: ServerApp, sid: str, session: MultiplayerSession, user_id: int, world_uid: uuid.UUID
) -> None:
    if (await sa.get_current_user(sid)).id != user_id and not session.allow_everyone_claim_world:
        await verify_has_admin(sa, sid, session.id, None)

    world = World.get_by_uuid(world_uid)
    user = database.User.get_by_id(user_id)

    try:
        association = WorldUserAssociation.get_by_instances(world=world, user=user)
    except peewee.DoesNotExist:
        raise error.InvalidActionError(f"User {world.name} does not claim world {world.name}")

    association.delete_instance()
    await session_common.add_audit_entry(sa, sid, session, f"Unassociated world {world.name} from {user.name}")


async def _switch_admin(
    sa: ServerApp, sid: str, session: MultiplayerSession, membership: MultiplayerMembership
) -> None:
    session_id = session.id

    # Must be admin for this
    await verify_has_admin(sa, sid, session_id, None, allow_when_no_admins=True)
    num_admins = (
        MultiplayerMembership.select()
        .where(MultiplayerMembership.session == session_id, is_boolean(MultiplayerMembership.admin, True))
        .count()
    )

    if membership.admin and num_admins <= 1:
        raise error.InvalidActionError("can't demote the only admin")

    membership.admin = not membership.admin
    await session_common.add_audit_entry(
        sa, sid, session, f"Made {membership.effective_name} {'' if membership.admin else 'not '}an admin"
    )
    sa.logger.info(
        f"{session_common.describe_session(session)}, User {membership.user.id}. Performing admin switch, "
        f"new status is {membership.admin}."
    )
    membership.save()


async def _switch_ready(
    sa: ServerApp, sid: str, session: MultiplayerSession, membership: MultiplayerMembership
) -> None:
    with database.db.atomic():
        membership.ready = not membership.ready
        membership.save()
        sa.logger.info(f"{session_common.describe_session(session)}. Switching ready-ness.")


async def _set_allow_everyone_claim(sa: ServerApp, sid: str, session: MultiplayerSession, new_state: bool) -> None:
    await verify_has_admin(sa, sid, session.id, None)

    with database.db.atomic():
        session.allow_everyone_claim_world = new_state
        new_operation = "Allowing" if session.allow_everyone_claim_world else "Disallowing"
        await session_common.add_audit_entry(sa, sid, session, f"{new_operation} everyone to claim worlds.")
        session.save()


async def _set_allow_coop(sa: ServerApp, sid: str, session: MultiplayerSession, new_state: bool) -> None:
    """Sets the Co-Op state of the given session to the desired state."""
    await verify_has_admin(sa, sid, session.id, None)

    if not new_state:
        for generic_world in session.worlds:
            if len(generic_world.associations) >= 2:
                raise error.InvalidActionError(
                    "Can only disable coop, if a world isn't associated to multiple users at once."
                )

    with database.db.atomic():
        session.allow_coop = new_state
        new_operation = "Allowing" if session.allow_coop else "Disallowing"
        await session_common.add_audit_entry(sa, sid, session, f"{new_operation} coop for the session.")
        session.save()


async def _create_patcher_file(
    sa: ServerApp, sid: str, session: MultiplayerSession, world_uid: str, cosmetic_json: dict
) -> dict:
    player_names = {}
    uuids = {}
    player_index = None
    world_uuid = uuid.UUID(world_uid)

    for world in session.get_ordered_worlds():
        assert world.order is not None
        player_names[world.order] = world.name
        uuids[world.order] = world.uuid
        if world.uuid == world_uuid:
            player_index = world.order
            await _check_user_associated_with(sa, sid, world)

    if player_index is None:
        raise error.InvalidActionError("Unknown world uid for exporting")

    layout_description = session.layout_description
    assert layout_description is not None
    players_config = PlayersConfiguration(
        player_index=player_index,
        player_names=player_names,
        uuids=uuids,
        session_name=session.name,
        is_coop=session.allow_coop,
    )
    preset = layout_description.get_preset(players_config.player_index)
    cosmetic_patches = preset.game.data.layout.cosmetic_patches.from_json(cosmetic_json)

    await session_common.add_audit_entry(
        sa, sid, session, f"Exporting game named {players_config.player_names[players_config.player_index]}"
    )

    data_factory = preset.game.patch_data_factory(layout_description, players_config, cosmetic_patches)
    try:
        return data_factory.create_data()
    except Exception as e:
        sa.logger.exception("Error when creating patch data")
        raise error.InvalidActionError(f"Unable to export game: {e}")


async def admin_player(sa: ServerApp, sid: str, session_id: int, user_id: int, action: str, *args: typing.Any) -> None:
    monitoring.set_tag("action", action)

    await verify_has_admin(sa, sid, session_id, user_id)
    action_ = SessionAdminUserAction(action)

    session: MultiplayerSession = database.MultiplayerSession.get_by_id(session_id)
    membership = await session_common.get_membership_for(user_id, session, sid)

    if action_ == SessionAdminUserAction.KICK:
        await _kick_user(sa, sid, session, membership, user_id)

    elif action_ == SessionAdminUserAction.CREATE_WORLD_FOR:
        await _create_world_for(sa, sid, session, membership, *args)

    elif action_ == SessionAdminUserAction.CLAIM:
        await _claim_world(sa, sid, session, user_id, *args)

    elif action_ == SessionAdminUserAction.UNCLAIM:
        await _unclaim_world(sa, sid, session, user_id, *args)

    elif action_ == SessionAdminUserAction.SWITCH_ADMIN:
        await _switch_admin(sa, sid, session, membership)

    elif action_ == SessionAdminUserAction.SWITCH_READY:
        await _switch_ready(sa, sid, session, membership)

    elif action_ == SessionAdminUserAction.ABANDON:
        # FIXME
        raise error.InvalidActionError("Abandon is NYI")

    await session_common.emit_session_meta_update(sa, session)


def setup_app(sa: ServerApp) -> None:
    sa.on("multiplayer_admin_session", admin_session)
    sa.on("multiplayer_admin_player", admin_player)
