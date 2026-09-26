from math import ceil
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse

from randovania.lib import json_lib
from randovania.server.database import (
    AsyncRaceEntry,
    AsyncRaceRoom,
)
from randovania.server.server_app import AdminDep, ServerApp, ServerAppDep

router = APIRouter()


def RdvFileResponse(data: str, filename: str) -> Response:
    return Response(data, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/async-race-rooms", response_class=HTMLResponse)
def admin_async_rooms(
    sa: ServerAppDep, user: AdminDep, request: Request, page: Annotated[int, Query(ge=1)] = 1
) -> HTMLResponse:
    page_count = ceil(AsyncRaceRoom.select().count() / 20)

    if not page_count:
        return sa.templates.TemplateResponse(
            request,
            "basic_page.html.jinja",
            context={
                "title": "Async Race Rooms",
                "header": "Async Race Rooms",
                "content": "<p>No Async Race Rooms.</p>",
            },
        )

    if page > page_count:
        raise HTTPException(status_code=404, detail="Async Race Room page not found")

    order = AsyncRaceRoom.creation_date.desc()  # type: ignore[attr-defined]
    paginated_query = AsyncRaceRoom.select().order_by(order).paginate(page, 20)

    return sa.templates.TemplateResponse(
        request,
        "web_api/asyncs_list.html.jinja",
        context={
            "page": page,
            "page_count": page_count,
            "rooms": list(paginated_query),
        },
    )


@router.get("/async-race-room/{async_room_id}", response_class=HTMLResponse)
def admin_async_room(sa: ServerAppDep, user: AdminDep, request: Request, async_room_id: int) -> HTMLResponse:
    try:
        async_room: AsyncRaceRoom = AsyncRaceRoom.get_by_id(async_room_id)
    except AsyncRaceRoom.DoesNotExist:
        raise HTTPException(status_code=404, detail="Async Room not found")

    user_entries = list(AsyncRaceEntry.select().where(AsyncRaceEntry.room == async_room))

    print(user_entries)

    return sa.templates.TemplateResponse(
        request,
        "web_api/async_room.html.jinja",
        context={
            "async_room": async_room,
            "entries": user_entries,
        },
    )


@router.get("/async-race-room/{async_room_id}/rdvgame")
def download_async_room_spoiler(user: AdminDep, async_room_id: int) -> Response:
    try:
        async_room: AsyncRaceRoom = AsyncRaceRoom.get_by_id(async_room_id)
    except AsyncRaceRoom.DoesNotExist:
        raise HTTPException(status_code=404, detail="Async Room not found")

    layout = async_room.layout_description.as_json()

    return RdvFileResponse(json_lib.encode(layout), f"{async_room.name}.rdvgame")


def setup_app(sa: ServerApp) -> None:
    sa.app.include_router(router)
