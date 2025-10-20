from __future__ import annotations

import contextlib
import os
import platform
import re
import typing
from pathlib import Path

import sentry_sdk
import sentry_sdk.integrations.logging
import sentry_sdk.scrubber
import sentry_sdk.types

import randovania

if typing.TYPE_CHECKING:
    from randovania.lib.json_lib import JsonObject_RO


class HomeEventScrubber(sentry_sdk.scrubber.EventScrubber):
    def scrub_dict(self, d: object) -> None:
        super().scrub_dict(d)
        _filter_user_home(d)


def _filter_data(data: object, str_filter: typing.Callable[[str], str]) -> typing.Any | None:
    result = None
    if isinstance(data, dict):
        for k, v in tuple(data.items()):
            new = _filter_data(v, str_filter)
            if new is not None:
                data[k] = new

    elif isinstance(data, list):
        for i, v in enumerate(data):
            new = _filter_data(v, str_filter)
            if new is not None:
                data[i] = new

    elif isinstance(data, tuple):
        for i, v in enumerate(data):
            new = _filter_data(v, str_filter)
            if new is not None:
                if result is None:
                    result = list(data)
                result[i] = new

    elif isinstance(data, Path):
        new = _filter_data(str(data), str_filter)
        if new is not None:
            result = type(data)(new)

    elif isinstance(data, str):
        new = str_filter(data)
        if new != data:
            result = new

    return result


_HOME_RE = re.compile(r"(:?[/\\](?:home|Users)[/\\]+)([^/\\]+)([/\\])")


def _filter_user_home(data: typing.Any) -> typing.Any | None:
    def filter_home(s: str) -> str:
        return _HOME_RE.sub(r"\1<redacted>\3", s)

    return _filter_data(data, filter_home)


def before_breadcrumb(crumb: dict[str, typing.Any], hint: sentry_sdk.types.Hint) -> dict[str, typing.Any] | None:
    # Crumb is a dictionary, so this function will always return None and modify crumb in-place instead.
    _filter_user_home(crumb)
    return crumb


def before_send(event: sentry_sdk.types.Event, hint: sentry_sdk.types.Hint) -> sentry_sdk.types.Event | None:
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, ConnectionError):
            return None

    _filter_user_home(event)
    return event


type SentryUrlKeys = typing.Literal["client", "server", "bot"]


def _init(
    include_server: bool, url_key: SentryUrlKeys, sampling_rate: float = 1.0, exclude_server_name: bool = False
) -> None:
    if randovania.is_dirty():
        return

    configuration = randovania.get_configuration()
    if "sentry_urls" not in configuration:
        return

    sentry_url = configuration["sentry_urls"][url_key]
    if sentry_url is None:
        return

    from sentry_sdk.integrations.aiohttp import AioHttpIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    integrations = [
        AioHttpIntegration(),
        AsyncioIntegration(),
        LoggingIntegration(),
    ]

    profiles_sample_rate = sampling_rate
    if include_server:
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        integrations.append(FastApiIntegration())
    else:
        profiles_sample_rate = 0.5 if randovania.is_dev_version() else 0.0

    server_name = None
    if exclude_server_name:
        # hostname for clients contains pii, so exclude them if we're not doing server.
        server_name = "client"

    def traces_sampler(sampling_context):
        # Ignore the websocket request
        if sampling_context["transaction_context"]["name"] == "generic WSGI request":
            return 0

        return sampling_rate

    sentry_sdk.init(
        dsn=sentry_url,
        integrations=integrations,
        release=f"v{randovania.VERSION}",
        environment="staging" if randovania.is_dev_version() else "production",
        traces_sampler=traces_sampler,
        profiles_sample_rate=profiles_sample_rate,
        server_name=server_name,
        auto_session_tracking=include_server,
        event_scrubber=HomeEventScrubber(),
        before_breadcrumb=before_breadcrumb,
        before_send=before_send,
        enable_logs=True,
        # before_send_log=before_send_log,  # If we need to explicitly filter user data
    )
    sentry_sdk.Scope.get_global_scope().set_context(
        "os",
        {
            "name": platform.system(),
            "version": platform.release(),
        },
    )


def client_init() -> None:
    _init(False, "client", exclude_server_name=True)

    global_scope = sentry_sdk.Scope.get_global_scope()
    global_scope.set_tag("frozen", randovania.is_frozen())
    global_scope.set_tag("cpu.architecture", platform.machine())
    global_scope.set_tag("cpu.processor", platform.processor() or "unknown")  # Empty string is an invalid value
    global_scope.set_tag("cpu.count", os.cpu_count())

    # Ignore the "packet queue is empty, aborting" message
    # It causes a disconnect, but we smoothly reconnect in that case.
    sentry_sdk.integrations.logging.ignore_logger("engineio.client")


def server_init(sampling_rate: float) -> None:
    return _init(True, "server", sampling_rate=sampling_rate)


def bot_init() -> None:
    return _init(False, "bot")


trace_function = sentry_sdk.trace
set_tag = sentry_sdk.set_tag
start_transaction = sentry_sdk.start_transaction


def trace_block(description: str):
    current_span = sentry_sdk.get_current_span()
    if current_span is not None:
        return current_span.start_child(
            op=sentry_sdk.consts.OP.FUNCTION,
            description=description,
        )
    else:
        return contextlib.nullcontext()


class Metrics:
    """Placeholder for monitoring events in the client."""

    def incr(self, key: str, value: int = 1, tags: JsonObject_RO | None = None) -> None:
        pass

    def gauge(self, key: str, value: int = 1, tags: JsonObject_RO | None = None) -> None:
        pass


metrics = Metrics()
