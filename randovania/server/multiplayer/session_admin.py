import json
import uuid

import peewee

import randovania
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import error
from randovania.network_common.admin_actions import SessionAdminGlobalAction, SessionAdminUserAction
from randovania.network_common.multiplayer_session import MAX_SESSION_NAME_LENGTH, WORLD_NAME_RE
from randovania.network_common.session_state import MultiplayerSessionState
from randovania.server import database
from randovania.server.database import MultiplayerMembership, is_boolean, MultiplayerSession, World, \
    WorldUserAssociation, MultiplayerAuditEntry
from randovania.server.lib import logger
from randovania.server.multiplayer import session_common
from randovania.server.server_app import ServerApp


def _check_user_associated_with(sio: ServerApp, world: World):
    try:
        WorldUserAssociation.get(
            WorldUserAssociation.world == world,
            WorldUserAssociation.user == sio.get_current_user(),
        )
    except peewee.DoesNotExist:
        raise error.NotAuthorizedForActionError()


def verify_has_admin(sio: ServerApp, session_id: int, admin_user_id: int | None,
                     *, allow_when_no_admins: bool = False) -> None:
    """
    Checks if the logged user can do admin operations to the given session,
    :param sio:
    :param session_id: The GameSessions id.
    :param admin_user_id: An user id that is exceptionally authorized for this.
    :param allow_when_no_admins: This action is authorized for non-admins if there are no admins.
    :return:
    """
    current_user = sio.get_current_user()
    current_membership = session_common.get_membership_for(current_user, session_id)

    if not (current_membership.admin or (admin_user_id is not None and current_user.id == admin_user_id)):
        if allow_when_no_admins and MultiplayerMembership.select().where(
                MultiplayerMembership.session == session_id,
                is_boolean(MultiplayerMembership.admin, True)
        ).count() == 0:
            return
        raise error.NotAuthorizedForActionError()


def verify_has_admin_or_claimed(sio: ServerApp, world: World) -> None:
    """
    Checks if the logged user can do admin operations to the given session,
    :param sio:
    :param world:
    :return:
    """
    current_membership = session_common.get_membership_for(sio, world.session)

    if not current_membership.admin:
        _check_user_associated_with(sio, world)


def _verify_world_has_session(world: World, session: MultiplayerSession):
    if world.session.id != session.id:
        raise error.InvalidActionError("Wrong session")


def _verify_in_state(session: MultiplayerSession, state: MultiplayerSessionState):
    if session.state != state:
        raise error.SessionInWrongStateError(state)


def _verify_in_setup(session: MultiplayerSession):
    _verify_in_state(session, MultiplayerSessionState.SETUP)


def _verify_no_layout_description(session: MultiplayerSession):
    if session.layout_description_json is not None:
        raise error.InvalidActionError("Session has a generated game")


def _verify_not_in_generation(session: MultiplayerSession):
    if session.generation_in_progress is not None:
        raise error.InvalidActionError("Session game is being generated")


def _get_preset(preset_json: dict) -> VersionedPreset:
    try:
        preset = VersionedPreset(preset_json)
        preset.get_preset()  # test if valid
        return preset
    except Exception as e:
        raise error.InvalidActionError(f"invalid preset: {e}")


def _create_world(sio: ServerApp, session: MultiplayerSession, arg: tuple[str, dict], for_user: int | None = None):
    if len(arg) != 2:
        raise error.InvalidActionError("Missing arguments.")
    verify_has_admin(sio, session.id, for_user)

    _verify_in_setup(session)
    _verify_no_layout_description(session)
    _verify_not_in_generation(session)
    name, preset_json = arg
    preset = _get_preset(preset_json)

    if WORLD_NAME_RE.match(name) is None:
        raise error.InvalidActionError("Invalid world name")

    logger().info(f"{session_common.describe_session(session)}: Creating world {name}.")

    world = World.create_for(session=session, name=name, preset=preset)
    session_common.add_audit_entry(sio, session, f"Created new world {world.name}")
    return world


def _change_world(sio: ServerApp, session: MultiplayerSession, arg: tuple[uuid.UUID, dict]):
    if len(arg) != 2:
        raise error.InvalidActionError("Missing arguments.")

    world_uid, preset_json = arg
    world = World.get_by_uuid(world_uid)

    _verify_in_setup(session)
    _verify_no_layout_description(session)
    _verify_not_in_generation(session)
    preset = _get_preset(preset_json)

    _verify_world_has_session(world, session)
    verify_has_admin_or_claimed(sio, world)

    if preset.game not in session.allowed_games:
        raise error.InvalidActionError(f"Only {preset.game} preset not allowed.")

    if not randovania.is_dev_version() and preset.get_preset().configuration.unsupported_features():
        raise error.InvalidActionError("Preset uses unsupported features.")

    try:
        with database.db.atomic():
            world.preset = json.dumps(preset.as_json)
            logger().info(f"{session_common.describe_session(session)}: Changing world {world_uid}.")
            world.save()
            session_common.add_audit_entry(sio, session, f"Changing world {world.name}")

    except peewee.DoesNotExist:
        raise error.InvalidActionError(f"invalid world: {world_uid}")


def _rename_world(sio: ServerApp, session: MultiplayerSession, arg: tuple[uuid.UUID, str]):
    if len(arg) != 2:
        raise error.InvalidActionError("Missing arguments.")
    world_uid, new_name = arg

    world = World.get_by_uuid(world_uid)
    _verify_world_has_session(world, session)
    verify_has_admin_or_claimed(sio, world)

    if WORLD_NAME_RE.match(new_name) is None:
        raise error.InvalidActionError("Invalid world name")

    with database.db.atomic():
        logger().info(f"{session_common.describe_session(session)}: Renaming {world.name} ({world_uid}) to {new_name}.")
        session_common.add_audit_entry(sio, session, f"Renaming world {world.name} to {new_name}")
        world.name = new_name
        world.save()


def _delete_world(sio: ServerApp, session: MultiplayerSession, world_uid: str):
    world = World.get_by_uuid(world_uid)

    verify_has_admin_or_claimed(sio, world)
    _verify_world_has_session(world, session)
    _verify_in_setup(session)
    _verify_no_layout_description(session)
    _verify_not_in_generation(session)

    world = World.get_by_uuid(world_uid)
    with database.db.atomic():
        logger().info(f"{session_common.describe_session(session)}: Deleting {world.name} ({world_uid}).")
        session_common.add_audit_entry(sio, session, f"Deleting world {world.name}")
        WorldUserAssociation.delete().where(WorldUserAssociation.world == world.id).execute()
        world.delete_instance()


def _update_layout_generation(sio: ServerApp, session: MultiplayerSession, world_order: list[str]):
    verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)

    world_objects: dict[str, World] = {
        str(world.uuid): world
        for world in session.worlds
    }
    if world_order:
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
            session.generation_in_progress = sio.get_current_user()
            for i, world_uuid in enumerate(world_order):
                world_objects[world_uuid].order = i
                world_objects[world_uuid].save()
        else:
            session.generation_in_progress = None

        logger().info("%s: Making generation in progress to %s", session_common.describe_session(session),
                      str(session.generation_in_progress))
        session.save()


def _change_layout_description(sio: ServerApp, session: MultiplayerSession, description_json: dict | None):
    verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)
    worlds_to_update = []

    if description_json is None:
        if not session.has_layout_description():
            return

        description = None
        for world in session.worlds:
            world.uuid = uuid.uuid4()
            worlds_to_update.append(world)

    else:
        if session.generation_in_progress != sio.get_current_user():
            if session.generation_in_progress is None:
                raise error.InvalidActionError("Not waiting for a layout.")
            else:
                raise error.InvalidActionError(f"Waiting for a layout from {session.generation_in_progress.name}.")

        _verify_no_layout_description(session)
        description = LayoutDescription.from_json_dict(description_json)
        worlds = session.get_ordered_worlds()

        if description.player_count != len(worlds):
            raise error.InvalidActionError(f"Description is for a {description.player_count} players,"
                                           f" while the session is for {len(worlds)}.")

        if any(world.order is None for world in worlds):
            raise error.InvalidActionError("One of the worlds has undefined order field.")

        for permalink_preset, world in zip(description.all_presets, worlds):
            if _get_preset(json.loads(world.preset)).get_preset() != permalink_preset:
                preset = VersionedPreset.with_preset(permalink_preset)
                if preset.game not in session.allowed_games:
                    raise error.InvalidActionError(f"{preset.game} preset not allowed.")
                if not randovania.is_dev_version() and permalink_preset.configuration.unsupported_features():
                    raise error.InvalidActionError(f"Preset {permalink_preset.name} uses unsupported features.")
                world.preset = json.dumps(preset.as_json)
                worlds_to_update.append(world)

    with database.db.atomic():
        for world in worlds_to_update:
            world.save()

        session.generation_in_progress = None
        session.layout_description = description
        session.save()
        session_common.add_audit_entry(sio, session,
                                       "Removed generated game" if description is None
                                       else f"Set game to {description.shareable_word_hash}")


def _download_layout_description(sio: ServerApp, session: MultiplayerSession):
    # You must be a session member to do get the spoiler
    session_common.get_membership_for(sio, session)

    if not session.has_layout_description():
        raise error.InvalidActionError("Session does not contain a game")

    description = session.layout_description

    if not description.has_spoiler:
        raise error.InvalidActionError("Session does not contain a spoiler")

    session_common.add_audit_entry(sio, session, "Requested the spoiler log")
    return json.dumps(description.as_json())


def _start_session(sio: ServerApp, session: MultiplayerSession):
    verify_has_admin(sio, session.id, None)
    _verify_in_setup(session)
    if session.layout_description_json is None:
        raise error.InvalidActionError("Unable to start session, no game is available.")

    session.state = MultiplayerSessionState.IN_PROGRESS
    logger().info(f"{session_common.describe_session(session)}: Starting session.")
    session.save()
    session_common.add_audit_entry(sio, session, "Started session")


def _finish_session(sio: ServerApp, session: MultiplayerSession):
    verify_has_admin(sio, session.id, None)
    _verify_in_state(session, MultiplayerSessionState.IN_PROGRESS)

    session.state = MultiplayerSessionState.FINISHED
    logger().info(f"{session_common.describe_session(session)}: Finishing session.")
    session.save()
    session_common.add_audit_entry(sio, session, "Finished session")


def _change_password(sio: ServerApp, session: MultiplayerSession, password: str):
    verify_has_admin(sio, session.id, None)

    session.password = session_common.hash_password(password)
    logger().info(f"{session_common.describe_session(session)}: Changing password.")
    session.save()
    session_common.add_audit_entry(sio, session, "Changed password")


def _change_title(sio: ServerApp, session: MultiplayerSession, title: str):
    verify_has_admin(sio, session.id, None)

    if not (0 < len(title) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    old_name = session.name
    session.name = title
    logger().info(f"{session_common.describe_session(session)}: Changed name from {old_name}.")
    session.save()
    session_common.add_audit_entry(sio, session, f"Changed name from {old_name} to {title}")


def _duplicate_session(sio: ServerApp, session: MultiplayerSession, new_title: str):
    verify_has_admin(sio, session.id, None)

    if not (0 < len(new_title) <= MAX_SESSION_NAME_LENGTH):
        raise error.InvalidActionError("Invalid session name length")

    current_user = sio.get_current_user()
    session_common.add_audit_entry(sio, session, f"Duplicated session as {new_title}")

    with database.db.atomic():
        new_session: MultiplayerSession = MultiplayerSession.create(
            name=new_title,
            password=session.password,
            creator=current_user,
            layout_description_json=session.layout_description_json,
            game_details_json=session.game_details_json,
            dev_features=session.dev_features,
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


def _get_permalink(sio: ServerApp, session: MultiplayerSession) -> str:
    verify_has_admin(sio, session.id, None)

    if not session.has_layout_description():
        raise error.InvalidActionError("Session does not contain a game")

    session_common.add_audit_entry(sio, session, "Requested permalink")
    return session.layout_description.permalink.as_base64_str


def admin_session(sio: ServerApp, session_id: int, action: str, arg):
    action: SessionAdminGlobalAction = SessionAdminGlobalAction(action)
    session: database.MultiplayerSession = database.MultiplayerSession.get_by_id(session_id)

    if action == SessionAdminGlobalAction.CREATE_WORLD:
        _create_world(sio, session, arg)

    elif action == SessionAdminGlobalAction.CHANGE_WORLD:
        _change_world(sio, session, arg)

    elif action == SessionAdminGlobalAction.RENAME_WORLD:
        _rename_world(sio, session, arg)

    elif action == SessionAdminGlobalAction.DELETE_WORLD:
        _delete_world(sio, session, arg)

    elif action == SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION:
        _update_layout_generation(sio, session, arg)

    elif action == SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION:
        _change_layout_description(sio, session, arg)

    elif action == SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION:
        return _download_layout_description(sio, session)

    elif action == SessionAdminGlobalAction.START_SESSION:
        _start_session(sio, session)

    elif action == SessionAdminGlobalAction.FINISH_SESSION:
        _finish_session(sio, session)

    elif action == SessionAdminGlobalAction.CHANGE_PASSWORD:
        _change_password(sio, session, arg)

    elif action == SessionAdminGlobalAction.CHANGE_TITLE:
        _change_title(sio, session, arg)

    elif action == SessionAdminGlobalAction.DUPLICATE_SESSION:
        return _duplicate_session(sio, session, arg)

    elif action == SessionAdminGlobalAction.DELETE_SESSION:
        logger().info(f"{session_common.describe_session(session)}: Deleting session.")
        session.delete_instance(recursive=True)

    elif action == SessionAdminGlobalAction.REQUEST_PERMALINK:
        return _get_permalink(sio, session)

    elif action == SessionAdminGlobalAction.CREATE_PATCHER_FILE:
        world_uid, cosmetic_json = arg
        return _create_patcher_file(sio, session, world_uid, cosmetic_json)

    session_common.emit_session_meta_update(session)


def _kick_user(sio: ServerApp, session: MultiplayerSession, membership: MultiplayerMembership, user_id: int):
    session_common.add_audit_entry(
        sio, session,
        f"Kicked {membership.effective_name}" if membership.user != sio.get_current_user() else "Left session"
    )

    with database.db.atomic():
        for association in WorldUserAssociation.select().join(World).where(
                World.session == session.id,
                WorldUserAssociation.user == user_id,
        ):
            association.delete_instance()
        membership.delete_instance()
        if not list(session.members):
            session.delete_instance(recursive=True)
            logger().info(f"{session_common.describe_session(session)}. Kicking user {user_id} and deleting session.")
        else:
            logger().info(f"{session_common.describe_session(session)}. Kicking user {user_id}.")


def _create_world_for(sio: ServerApp, session: MultiplayerSession, membership: MultiplayerMembership,
                      arg: tuple[str, dict]):
    with database.db.atomic():
        new_world = _create_world(sio, session, arg, membership.user.id)
        WorldUserAssociation.create(
            world=new_world,
            user=membership.user,
        )
        session_common.add_audit_entry(sio, session,
                                       f"Associated new world {new_world.name} for {membership.user.name}")


def _claim_world(sio: ServerApp, session: MultiplayerSession, user_id: int, world_uid: uuid.UUID):
    if not session.allow_everyone_claim_world:
        verify_has_admin(sio, session.id, None)

    world = World.get_by_uuid(world_uid)

    if not session.allow_coop:
        for _ in WorldUserAssociation.select().where(WorldUserAssociation.world == world.id):
            raise error.InvalidActionError("World is already claimed")

    WorldUserAssociation.create(
        world=world,
        user=user_id,
    )
    session_common.add_audit_entry(sio, session,
                                   f"Associated world {world.name} for {database.User.get_by_id(user_id).name}")


def _unclaim_world(sio: ServerApp, session: MultiplayerSession, user_id: int, world_uid: uuid.UUID):
    if not session.allow_everyone_claim_world:
        verify_has_admin(sio, session.id, None)

    world = World.get_by_uuid(world_uid)
    user = database.User.get_by_id(user_id)

    WorldUserAssociation.get_by_instances(world=world, user=user).delete_instance()
    session_common.add_audit_entry(sio, session,
                                   f"Unassociated world {world.name} from {user.name}")


def _switch_admin(sio: ServerApp, session: MultiplayerSession, membership: MultiplayerMembership):
    session_id = session.id

    # Must be admin for this
    verify_has_admin(sio, session_id, None, allow_when_no_admins=True)
    num_admins = MultiplayerMembership.select().where(MultiplayerMembership.session == session_id,
                                                      is_boolean(MultiplayerMembership.admin, True)).count()

    if membership.admin and num_admins <= 1:
        raise error.InvalidActionError("can't demote the only admin")

    membership.admin = not membership.admin
    session_common.add_audit_entry(sio, session,
                                   f"Made {membership.effective_name} {'' if membership.admin else 'not '}an admin")
    logger().info(f"{session_common.describe_session(session)}, User {membership.user.id}. Performing admin switch, "
                  f"new status is {membership.admin}.")
    membership.save()


def _create_patcher_file(sio: ServerApp, session: MultiplayerSession, world_uid: str, cosmetic_json: dict):
    player_names = {}
    uuids = {}
    player_index = None
    world_uid = uuid.UUID(world_uid)

    for world in session.get_ordered_worlds():
        player_names[world.order] = world.name
        uuids[world.order] = world.uuid
        if world.uuid == world_uid:
            player_index = world.order
            _check_user_associated_with(sio, world)

    if player_index is None:
        raise error.InvalidActionError("Unknown world uid for exporting")

    layout_description = session.layout_description
    players_config = PlayersConfiguration(
        player_index=player_index,
        player_names=player_names,
        uuids=uuids,
        session_name=session.name,
    )
    preset = layout_description.get_preset(players_config.player_index)
    cosmetic_patches = preset.game.data.layout.cosmetic_patches.from_json(cosmetic_json)

    session_common.add_audit_entry(sio, session,
                                   f"Exporting game named {players_config.player_names[players_config.player_index]}")

    data_factory = preset.game.patch_data_factory(layout_description, players_config, cosmetic_patches)
    try:
        return data_factory.create_data()
    except Exception as e:
        logger().exception("Error when creating patch data")
        raise error.InvalidActionError(f"Unable to export game: {e}")


def admin_player(sio: ServerApp, session_id: int, user_id: int, action: str, arg):
    verify_has_admin(sio, session_id, user_id)
    action: SessionAdminUserAction = SessionAdminUserAction(action)

    session: MultiplayerSession = database.MultiplayerSession.get_by_id(session_id)
    membership = session_common.get_membership_for(user_id, session)

    if action == SessionAdminUserAction.KICK:
        _kick_user(sio, session, membership, user_id)

    elif action == SessionAdminUserAction.CREATE_WORLD_FOR:
        _create_world_for(sio, session, membership, arg)

    elif action == SessionAdminUserAction.CLAIM:
        _claim_world(sio, session, user_id, arg)

    elif action == SessionAdminUserAction.UNCLAIM:
        _unclaim_world(sio, session, user_id, arg)

    elif action == SessionAdminUserAction.SWITCH_ADMIN:
        _switch_admin(sio, session, membership)

    elif action == SessionAdminUserAction.ABANDON:
        # FIXME
        raise error.InvalidActionError("Abandon is NYI")

    session_common.emit_session_meta_update(session)


def setup_app(sio: ServerApp):
    sio.on("multiplayer_admin_session", admin_session)
    sio.on("multiplayer_admin_player", admin_player)
