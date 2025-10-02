import html
import json
from math import ceil
from typing import Annotated

import construct
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse

from randovania.game_description import default_database
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import json_lib
from randovania.network_common import remote_inventory
from randovania.server.database import MultiplayerMembership, MultiplayerSession, World, WorldUserAssociation
from randovania.server.server_app import AdminDep, RequireAdminUser, ServerApp

router = APIRouter()


def RdvFileResponse(data: str, filename: str) -> Response:
    return Response(data, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/sessions", response_class=HTMLResponse)
def admin_sessions(user: AdminDep, request: Request, page: Annotated[int, Query(ge=1)] = 1) -> str:
    page_count = ceil(MultiplayerMembership.select().count() / 20)

    if not page_count:
        return "<p>No sessions.</p>"

    if page > page_count:
        raise HTTPException(status_code=404, detail="Page not found")

    order = MultiplayerSession.creation_date.desc()  # type: ignore[attr-defined]
    paginated_query = MultiplayerSession.select().order_by(order).paginate(page, 20)

    lines = []
    for session in paginated_query:
        assert isinstance(session, MultiplayerSession)
        lines.append(
            "<tr>{}</tr>".format(
                "".join(
                    f"<td>{col}</td>"
                    for col in [
                        "<a href='{}'>{}</a>".format(
                            request.url_for("admin_session", session_id=session.id),
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

    previous = "Previous"
    if page > 1:
        previous = "<a href='{}?page={}'>Previous</a>".format(request.url_for(".admin_sessions"), page - 1)

    next_link = "Next"
    if page < page_count:
        next_link = "<a href='{}?page={}'>Next</a>".format(request.url_for(".admin_sessions"), page + 1)

    header = ["Name", "Creator", "Creation Date", "Num Users", "Num Worlds", "Has Password?"]
    return (
        "<table border='1'><tr>{header}</tr>{content}</table>Page {page} of {num_pages}. {previous} / {next}."
    ).format(
        header="".join(f"<th>{it}</th>" for it in header),
        content="".join(lines),
        page=page,
        num_pages=page_count,
        previous=previous,
        next=next_link,
    )


@router.get("/session/{session_id}", response_class=HTMLResponse)
def admin_session(user: AdminDep, request: Request, session_id: int) -> str:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

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
                "<a href='{}'>Download</a>".format(
                    request.url_for("download_world_preset", world_id=association.world_id)
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
        "<p><a href='{}'>Download rdvgame</a></p>".format(
            request.url_for("download_session_spoiler", session_id=session_id)
        )
        if session.has_layout_description()
        else "<p>No rdvgame attached</p>",
        "<p><a href='{}'>Delete session</a></p>".format(request.url_for("delete_session", session_id=session_id)),
        table,
    ]

    return "\n".join(entries)


@router.get("/session/{session_id}/rdvgame")
def download_session_spoiler(user: AdminDep, session_id: int) -> Response:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    layout = session.get_layout_description_as_json()
    if layout is None:
        raise HTTPException(status_code=404, detail="Session has no layout description")

    return RdvFileResponse(json_lib.encode(layout), f"{session.name}.rdvgame")


@router.get("/world/{world_id}/rdvpreset")
def download_world_preset(user: AdminDep, world_id: int) -> Response:
    try:
        world = World.get_by_id(world_id)
    except World.DoesNotExist:
        raise HTTPException(status_code=404, detail="World not found")

    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(world.session_id)
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    return RdvFileResponse(world.preset, f"{session.name} - {world.name}.rdvpreset")


@router.get("/session/{session_id}/delete", dependencies=[RequireAdminUser], response_class=HTMLResponse)
def get_delete_session(session_id: int) -> str:
    return '<form method="POST"><input type="submit" value="Confirm delete"></form>'


@router.post("/session/{session_id}/delete", dependencies=[RequireAdminUser], response_class=HTMLResponse)
def delete_session(request: Request, session_id: int) -> str:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    session.delete_instance(recursive=True)

    return "Session deleted. <a href='{to_list}'>Return to list</a>".format(
        to_list=request.url_for("admin_sessions"),
    )


def setup_app(sa: ServerApp) -> None:
    sa.app.include_router(router)
