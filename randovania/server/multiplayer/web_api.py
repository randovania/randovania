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
from randovania.server.database import (
    MultiplayerAuditEntry,
    MultiplayerMembership,
    MultiplayerSession,
    User,
    World,
    WorldUserAssociation,
)
from randovania.server.multiplayer.session_common import emit_session_audit_update
from randovania.server.server_app import AdminDep, RequireAdminUser, ServerApp, ServerAppDep

router = APIRouter()


def RdvFileResponse(data: str, filename: str) -> Response:
    return Response(data, headers={"Content-Disposition": f"attachment; filename={filename}"})


# For endpoints, there are 2 ways to  gate them behind being accessible only by an RDV-Admin:
# - pass in an AdminDep as an argument
# - pass in RequireAdminUser as a dependency in the decorator.


@router.get("/sessions", response_class=HTMLResponse)
def admin_sessions(
    sa: ServerAppDep, user: AdminDep, request: Request, page: Annotated[int, Query(ge=1)] = 1
) -> HTMLResponse:
    page_count = ceil(MultiplayerSession.select().count() / 20)

    if not page_count:
        return sa.templates.TemplateResponse(
            request,
            "basic_page.html.jinja",
            context={
                "title": "Sessions",
                "header": "Sessions",
                "content": "<p>No sessions.</p>",
            },
        )

    if page > page_count:
        raise HTTPException(status_code=404, detail="Session page not found")

    order = MultiplayerSession.creation_date.desc()  # type: ignore[attr-defined]
    paginated_query = MultiplayerSession.select().order_by(order).paginate(page, 20)

    return sa.templates.TemplateResponse(
        request,
        "web_api/session_list.html.jinja",
        context={
            "page": page,
            "page_count": page_count,
            "sessions": list(paginated_query),
        },
    )


@router.get("/session/{session_id}", response_class=HTMLResponse)
def admin_session(sa: ServerAppDep, user: AdminDep, request: Request, session_id: int) -> HTMLResponse:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    associations: list[WorldUserAssociation] = list(
        WorldUserAssociation.select()
        .join(World)
        .where(
            World.session == session,
        )
    )

    assoc_contexts = []

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

        assoc_contexts.append(
            {
                "user": association.user,
                "world": association.world,
                "game": json.loads(association.world.preset)["game"],
                "connection_state": association.connection_state,
                "inventory": ", ".join(inventory),
                "is_admin": MultiplayerMembership.get_by_ids(association.user_id, session_id).admin,
                "world_id": association.world_id,
            }
        )

    return sa.templates.TemplateResponse(
        request,
        "web_api/session.html.jinja",
        context={
            "session": session,
            "assocations": assoc_contexts,
        },
    )


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


@router.post("/session/{session_id}/user/{user_id}/toggle_admin", response_class=HTMLResponse)
async def toggle_admin_status(
    sa: ServerAppDep, admin: AdminDep, request: Request, session_id: int, user_id: int
) -> HTMLResponse:
    try:
        membership = MultiplayerMembership.get_by_ids(user_id, session_id)
        user = User.get_by_id(user_id)
        session = MultiplayerSession.get_by_id(session_id)
    except MultiplayerMembership.DoesNotExist:
        raise HTTPException(status_code=404, detail="Membership not found")
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    membership.admin = not membership.admin
    membership.save()

    MultiplayerAuditEntry.create(
        session=session,
        user=admin,
        message=f"Randovania Team made {user.name}{' not' if not membership.admin else ''} an Admin",
    )
    await emit_session_audit_update(sa, session)

    content = "Admin status of <code>{user}</code> toggled. <a href='{to_session}'>Return to session</a>".format(
        user=user.name,
        to_session=request.url_for("admin_session", session_id=session_id),
    )
    return sa.templates.TemplateResponse(
        request,
        "basic_page.html.jinja",
        context={
            "title": "Toggle Admin Status",
            "header": "Toggle Admin Status",
            "content": content,
        },
    )


@router.get("/session/{session_id}/delete", dependencies=[RequireAdminUser], response_class=HTMLResponse)
def get_delete_session(sa: ServerAppDep, request: Request, session_id: int) -> HTMLResponse:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    return sa.templates.TemplateResponse(
        request,
        "web_api/delete_session.html.jinja",
        context={
            "session": session,
        },
    )


@router.post("/session/{session_id}/delete", dependencies=[RequireAdminUser], response_class=HTMLResponse)
def delete_session(sa: ServerAppDep, request: Request, session_id: int) -> HTMLResponse:
    try:
        session: MultiplayerSession = MultiplayerSession.get_by_id(session_id)
    except MultiplayerSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    session.delete_instance(recursive=True)

    content = "Session deleted. <a href='{to_list}'>Return to list</a>".format(
        to_list=request.url_for("admin_sessions"),
    )
    return sa.templates.TemplateResponse(
        request,
        "basic_page.html.jinja",
        context={
            "title": "Delete Session",
            "header": "Delete Session",
            "content": content,
        },
    )


def setup_app(sa: ServerApp) -> None:
    sa.app.include_router(router)
