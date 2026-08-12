from __future__ import annotations

import inspect
import string
import typing
import urllib.parse

import pydantic

from randovania.network_common import error
from randovania.network_common.multiplayer_session import MAX_SESSION_NAME_LENGTH

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from aiohttp.client import _RequestOptions
    from fastapi import APIRouter

    from randovania.lib.type_lib import AsyncCallable
    from randovania.network_client.network_client import NetworkClient
    from randovania.network_common.multiplayer_session import MultiplayerSessionEntry
    from randovania.network_common.signals.common import TypedJsonObject

type HttpMethod = typing.Literal["GET", "POST"]

_PAYLOAD_PARAMETERS = frozenset(
    (
        # The JSON body of the request.
        "body",
        # The form data of the request.
        "form",
        # The query string of the request.
        "query",
    )
)


def _as_payload(value: typing.Any) -> typing.Any:
    """Pydantic models are sent as their JSON representation; anything else is sent as-is."""
    if isinstance(value, pydantic.BaseModel):
        return value.model_dump(mode="json")
    return value


class ServerEndpoint[**P, RetT]:
    """
    One of the server's REST endpoints, declared so both sides agree on its method, path and types.

    The declaration describes the *client* side of the call: its parameters are what the client provides
    and its return type is what the client receives. The server's handler has additional parameters which
    are filled in by dependency injection (`ServerAppDep`, `UserDep`, ...) and are not part of this signature.

    A parameter named after a `{placeholder}` in the path is formatted into the URL. The parameters `body`,
    `form` and `query` carry, respectively, the JSON body, the form data and the query string.
    """

    def __init__(
        self,
        fn: AsyncCallable[P, RetT],
        method: HttpMethod,
        path: str,
        errors_for_status: Mapping[int, type[error.BaseNetworkError]] | None = None,
    ):
        self.fn = fn
        self.method = method
        self.path = path
        self.errors_for_status = errors_for_status if errors_for_status is not None else {}

        self._signature = inspect.signature(fn)
        self._path_parameters = frozenset(
            field_name for _, field_name, _, _ in string.Formatter().parse(path) if field_name is not None
        )

        missing = self._path_parameters - set(self._signature.parameters)
        if missing:
            raise TypeError(f"{fn.__name__} has no parameters for the path placeholders {sorted(missing)}")

        unknown = set(self._signature.parameters) - self._path_parameters - _PAYLOAD_PARAMETERS
        if unknown:
            raise TypeError(
                f"{fn.__name__} has parameters that are neither in the path nor a payload: {sorted(unknown)}"
            )

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> typing.Never:
        raise TypeError(
            f"Cannot call ServerEndpoint {self.fn.__name__} directly. "
            f"Did you mean to call {self.fn.__name__}.call_server() instead?"
        )

    def prepare_request(self, *args: P.args, **kwargs: P.kwargs) -> tuple[str, _RequestOptions]:
        """Splits the given arguments into this request's path and the arguments `aiohttp` needs for it."""

        bound = self._signature.bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = dict(bound.arguments)

        path = self.path.format(
            **{name: urllib.parse.quote(str(arguments[name]), safe="") for name in self._path_parameters}
        )

        request_options: _RequestOptions = {}
        if (body := arguments.get("body")) is not None:
            request_options["json"] = _as_payload(body)
        if (form := arguments.get("form")) is not None:
            request_options["data"] = _as_payload(form)
        if (query := arguments.get("query")) is not None:
            request_options["params"] = _as_payload(query)

        return path, request_options

    def error_for_response(self, status: int, detail: str) -> error.BaseNetworkError:
        """The error to raise for a response with the given status code."""

        error_class = self.errors_for_status.get(status)
        if error_class is not None:
            return error_class.from_detail(detail)

        return error.InvalidActionError(detail or f"Server returned status {status}")

    def call_server(self, network_client: NetworkClient) -> AsyncCallable[P, RetT]:
        """
        Returns an async callable which, when called and awaited, uses the `NetworkClient` to perform
        this request and returns the decoded result. Provides full typing support, so it's preferable
        over using `NetworkClient.server_get()`/`server_post()` directly.
        """

        async def inner(*args: P.args, **kwargs: P.kwargs) -> RetT:
            path, request_options = self.prepare_request(*args, **kwargs)
            result = await network_client.perform_rest_request(self, path, request_options)
            return typing.cast("RetT", result)

        return inner

    def route[HandlerT](self, router: APIRouter, **kwargs: typing.Any) -> Callable[[HandlerT], HandlerT]:
        """
        Registers the decorated function as this endpoint's handler on the given router.

        Using this function means the method and the path are only ever written in this file.
        """
        register: Callable[[HandlerT], HandlerT] = getattr(router, self.method.lower())(self.path, **kwargs)
        return register


def server_endpoint[**P, RetT](
    method: HttpMethod,
    path: str,
    *,
    errors_for_status: Mapping[int, type[error.BaseNetworkError]] | None = None,
) -> Callable[[AsyncCallable[P, RetT]], ServerEndpoint[P, RetT]]:
    """
    Transforms a function into a `ServerEndpoint`, for fully type-checked REST calls from the client.

    The handler is registered with `endpoint.route()` on the server, and the client calls it with
    `endpoint.call_server()`.

    :param errors_for_status: Status codes which mean something more specific than "the request was
        invalid", and the error to raise for each of them.

    Example usage::

        @server_endpoint("GET", "/session/{session_id}")
        async def GetSession(session_id: int) -> TypedJsonObject[MultiplayerSessionEntry]:
            raise NotImplementedError

        @GetSession.route(router)
        async def get_session(user: UserDep, session_id: int) -> MultiplayerSessionEntry:
            return MultiplayerSession.get_by_id(session_id).create_session_entry()

        result = await GetSession.call_server(NetworkClient())(session_id=2)
    """

    def decorator(fn: AsyncCallable[P, RetT]) -> ServerEndpoint[P, RetT]:
        return ServerEndpoint(fn, method, path, errors_for_status)

    return decorator


class CreateSessionRequest(pydantic.BaseModel):
    name: typing.Annotated[str, pydantic.StringConstraints(min_length=1, max_length=MAX_SESSION_NAME_LENGTH)]


class GuestLoginForm(typing.TypedDict):
    """The server takes these as individual `Form()` parameters, so there's no model to share."""

    name: str
    sid: str


@server_endpoint("POST", "/session")
async def CreateSession(body: CreateSessionRequest) -> TypedJsonObject[MultiplayerSessionEntry]:
    """
    Creates a new multiplayer session, with the requesting user as its first (admin) member.
    When the `X-Randovania-Sid` header is present, that connection also joins the session's room.
    """
    raise NotImplementedError


@server_endpoint(
    "GET",
    "/world/{world_uuid}/abandoned-data",
    # The server intentionally does not tell the user whether the world exists at all.
    errors_for_status={403: error.WorldNotAssociatedError},
)
async def GetAbandonedWorldData(world_uuid: str) -> dict:
    """
    The data the GUI needs to drive an abandoned world: the world's own game modifications
    (stripped of anything about other worlds) and the locations already collected.
    """
    raise NotImplementedError


@server_endpoint(
    "GET",
    "/authentication_methods",
)
async def AuthenticationMethods() -> list[str]:
    """The values of `randovania.network_common.authentication.AuthenticationMethod` this server supports."""
    raise NotImplementedError


@server_endpoint(
    "POST",
    "/guest_login",
)
async def GuestLogin(form: GuestLoginForm) -> dict:
    """
    Logs the given sid in as a guest user, returning the new client-side session.
    Only available in debug servers.
    """
    raise NotImplementedError


ALL_ENDPOINTS: tuple[ServerEndpoint, ...] = (
    CreateSession,
    GetAbandonedWorldData,
    AuthenticationMethods,
    GuestLogin,
)
"""Every endpoint the client calls. Used to check that the server still provides all of them."""
