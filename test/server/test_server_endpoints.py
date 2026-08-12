from __future__ import annotations

import pytest

from randovania.network_common import server_endpoints
from randovania.network_common.server_endpoints import CreateSessionRequest, ServerEndpoint


@pytest.fixture
def server_routes(test_client) -> set[tuple[str, str]]:
    """Every (method, path) the server documents. The routers are only added by the lifespan."""
    return {
        (method.upper(), path)
        for path, operations in test_client.sa.app.openapi()["paths"].items()
        for method in operations
    }


@pytest.mark.parametrize("endpoint", server_endpoints.ALL_ENDPOINTS, ids=lambda it: it.fn.__name__)
def test_endpoint_is_provided_by_the_server(endpoint: ServerEndpoint, server_routes: set[tuple[str, str]]) -> None:
    # Every endpoint the client calls must exist on the server with the same method and path.
    assert (endpoint.method, endpoint.path) in server_routes


def test_prepare_request_formats_path_and_payload() -> None:
    path, options = server_endpoints.GetAbandonedWorldData.prepare_request(world_uuid="00000000-0000/0000")

    # Path parameters are quoted, so they can't escape their own segment.
    assert path == "/world/00000000-0000%2F0000/abandoned-data"
    assert options == {}

    # Pydantic payloads are sent as their JSON representation.
    path, options = server_endpoints.CreateSession.prepare_request(body=CreateSessionRequest(name="The Session"))
    assert path == "/session"
    assert options == {"json": {"name": "The Session"}}

    path, options = server_endpoints.GuestLogin.prepare_request(form={"name": "Foo", "sid": "1234"})
    assert path == "/guest_login"
    assert options == {"data": {"name": "Foo", "sid": "1234"}}


def test_cannot_be_called_directly() -> None:
    with pytest.raises(TypeError, match="Cannot call ServerEndpoint CreateSession directly"):
        server_endpoints.CreateSession(body=CreateSessionRequest(name="The Session"))


def test_declaration_must_cover_the_path_placeholders() -> None:
    with pytest.raises(TypeError, match=r"has no parameters for the path placeholders \['room_id'\]"):

        @server_endpoints.server_endpoint("GET", "/room/{room_id}")
        async def BadEndpoint() -> None:
            raise NotImplementedError


def test_declaration_must_not_have_unknown_parameters() -> None:
    with pytest.raises(TypeError, match=r"neither in the path nor a payload: \['listen'\]"):

        @server_endpoints.server_endpoint("GET", "/room")
        async def BadEndpoint(listen: bool) -> None:
            raise NotImplementedError
