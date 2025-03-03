import html
import json

import construct
import flask
from flask.typing import ResponseReturnValue
from playhouse import flask_utils

from randovania.game_description import default_database
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import json_lib
from randovania.network_common import remote_inventory
from randovania.server.database import MultiplayerMembership, MultiplayerSession, User, World, WorldUserAssociation
from randovania.server.server_app import ServerApp


def admin_sessions(user: User) -> ResponseReturnValue:
    paginated_query = flask_utils.PaginatedQuery(
        MultiplayerSession.select().order_by(MultiplayerSession.creation_date.desc()),
        paginate_by=20,
        check_bounds=True,
    )

    lines = []
    for session in paginated_query.get_object_list():
        assert isinstance(session, MultiplayerSession)
        lines.append(
            "<tr>{}</tr>".format(
                "".join(
                    f"<td>{col}</td>"
                    for col in [
                        "<a href='{}'>{}</a>".format(
                            flask.url_for("admin_session", session_id=session.id),
                            html.escape(session.name),
                        ),
                        html.escape(session.creator.name),
                        session.creation_date,
                        len(session.members),
                        len(session.worlds),
                        session.password is not None,
                    ]
                )
            )
        )

    page = paginated_query.get_page()
    previous = "Previous"
    if page > 1:
        previous = "<a href='{}'>Previous</a>".format(flask.url_for(".admin_sessions", page=page - 1))

    next_link = "Next"
    if page < paginated_query.get_page_count():
        next_link = "<a href='{}'>Next</a>".format(flask.url_for(".admin_sessions", page=page + 1))

    header = ["Name", "Creator", "Creation Date", "Num Users", "Num Worlds", "Has Password?"]
    return (
        "<table border='1'><tr>{header}</tr>{content}</table>Page {page} of {num_pages}. {previous} / {next}."
    ).format(
        header="".join(f"<th>{it}</th>" for it in header),
        content="".join(lines),
        page=page,
        num_pages=paginated_query.get_page_count(),
        previous=previous,
        next=next_link,
    )


def admin_session(user: User, session_id: int) -> ResponseReturnValue:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        return "Session not found", 404

    rows = []

    associations: list[WorldUserAssociation] = list(
        WorldUserAssociation.select()
        .join(World)
        .where(
            World.session == session,
        )
    )

    for association in associations:
        inventory = []

        if association.inventory is not None:
            parsed_inventory = remote_inventory.decode_remote_inventory(association.inventory)

            if isinstance(parsed_inventory, construct.ConstructError):
                inventory.append(f"Error parsing: {parsed_inventory}")
            else:
                game = VersionedPreset.from_str(association.world.preset).game
                db = default_database.resource_database_for(game)
                for item_name, item in parsed_inventory.items():
                    if item > 0:
                        inventory.append(f"{db.get_item(item_name).long_name} x{item}")
        else:
            inventory.append("Missing")

        rows.append(
            [
                html.escape(association.user.name),
                html.escape(association.world.name),
                json.loads(association.world.preset)["game"],
                association.connection_state.pretty_text,
                ", ".join(inventory),
                MultiplayerMembership.get_by_ids(association.user_id, session_id).admin,
                "<a href='{link}'>Download</a>".format(
                    link=flask.url_for("download_world_preset", world_id=association.world_id)
                ),
            ]
        )

    header = ["User", "World", "Game", "Connection State", "Inventory", "Is Admin?", "Preset"]
    table = "<table border='1'><tr>{}</tr>{}</table>".format(
        "".join(f"<th>{h}</th>" for h in header),
        "".join("<tr>{}</tr>".format("".join(f"<td>{h}</td>" for h in r)) for r in rows),
    )

    entries = [
        f"<p>Session: {html.escape(session.name)}</p>",
        f"<p>Created by {html.escape(session.creator.name)} at {session.creation_datetime}</p>",
        f"<p>Session is password protected, password is <code>{html.escape(session.password)}</code></p>"
        if session.password is not None
        else "Session is not password protected",
        "<p><a href='{link}'>Download rdvgame</a></p>".format(
            link=flask.url_for("download_session_spoiler", session_id=session_id)
        )
        if session.has_layout_description()
        else "<p>No rdvgame attached</p>",
        "<p><a href='{link}'>Delete session</a></p>".format(
            link=flask.url_for("delete_session", session_id=session_id)
        ),
        table,
    ]

    return "\n".join(entries)


def download_session_spoiler(user: User, session_id: int) -> ResponseReturnValue:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        return "Session not found", 404

    layout = session.get_layout_description_as_json()
    if layout is None:
        return flask.abort(404)

    response = flask.make_response(json_lib.encode(layout))
    response.headers["Content-Disposition"] = f"attachment; filename={session.name}.rdvgame"
    return response


def download_world_preset(user: User, world_id: int) -> ResponseReturnValue:
    try:
        world = World.get_by_id(world_id)
    except World.DoesNotExist:
        return "World not found", 404

    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(world.session_id)
    except MultiplayerSession.DoesNotExist:
        return "Session not found", 404

    response = flask.make_response(world.preset)
    response.headers["Content-Disposition"] = f"attachment; filename={session.name} - {world.name}.rdvpreset"
    return response


def delete_session(user: User, session_id: int) -> ResponseReturnValue:
    if flask.request.method == "GET":
        return '<form method="POST"><input type="submit" value="Confirm delete"></form>'

    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        return "Session not found", 404
    session.delete_instance(recursive=True)

    return "Session deleted. <a href='{to_list}'>Return to list</a>".format(
        to_list=flask.url_for("admin_sessions"),
    )


def setup_app(sa: ServerApp):
    sa.route_with_user("/sessions", need_admin=True)(admin_sessions)
    sa.route_with_user("/session/<session_id>", need_admin=True)(admin_session)
    sa.route_with_user("/session/<session_id>/rdvgame", need_admin=True)(download_session_spoiler)
    sa.route_with_user("/session/<session_id>/delete", methods=["GET", "POST"], need_admin=True)(delete_session)
    sa.route_with_user("/world/<world_id>/rdvpreset", need_admin=True)(download_world_preset)
