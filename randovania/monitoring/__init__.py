from __future__ import annotations

import contextlib
import json
import platform
import re
import typing
from pathlib import Path

import sentry_sdk
import sentry_sdk.integrations.logging
import sentry_sdk.metrics
import sentry_sdk.scrubber
import sentry_sdk.types

import randovania


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


_HOME_RE = re.compile(r"(:?[/\\](?:home|Users)[/\\])([^/\\]+)([/\\])")


def _filter_user_home(data: typing.Any) -> typing.Any | None:
    def filter_home(s: str) -> str:
        return _HOME_RE.sub(r"\1<redacted>\3", s)

    return _filter_data(data, filter_home)


def before_breadcrumb(crumb: dict[str, typing.Any], hint: sentry_sdk.types.Hint) -> dict[str, typing.Any] | None:
    # Crumb is a dictionary, so this function will always return None and modify crumb in-place instead.
    _filter_user_home(crumb)
    return crumb


def before_send(event: sentry_sdk.types.Event, hint: sentry_sdk.types.Hint) -> sentry_sdk.types.Event | None:
    _filter_user_home(event)
    return event


def _init(include_flask: bool, url_key: str, sampling_rate: float = 1.0, exclude_server_name: bool = False) -> None:
    if randovania.is_dirty():
        return

    configuration = randovania.get_configuration()
    if "sentry_urls" not in configuration:
        return

    sentry_url = configuration["sentry_urls"][url_key]
    if sentry_url is None:
        return

    from sentry_sdk.integrations.aiohttp import AioHttpIntegration

    integrations = [
        AioHttpIntegration(),
    ]

    profiles_sample_rate = sampling_rate
    if include_flask:
        from sentry_sdk.integrations.flask import FlaskIntegration

        integrations.append(FlaskIntegration())
    else:
        profiles_sample_rate = 0.0

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
        auto_session_tracking=include_flask,
        event_scrubber=HomeEventScrubber(),
        before_breadcrumb=before_breadcrumb,
        before_send=before_send,
    )
    sentry_sdk.set_context(
        "os",
        {
            "name": platform.system(),
            "version": platform.release(),
        },
    )


def client_init() -> None:
    _init(False, "client", exclude_server_name=True)

    sentry_sdk.set_tag("frozen", randovania.is_frozen())
    sentry_sdk.set_tag("cpu.architecture", platform.machine())

    # Ignore the "packet queue is empty, aborting" message
    # It causes a disconnect, but we smoothly reconnect in that case.
    sentry_sdk.integrations.logging.ignore_logger("engineio.client")


def server_init(sampling_rate: float) -> None:
    return _init(True, "server", sampling_rate=sampling_rate)


def bot_init() -> None:
    return _init(False, "bot")


@contextlib.contextmanager
def attach_patcher_data(patcher_data: dict):
    with sentry_sdk.push_scope() as scope:
        scope.add_attachment(
            json.dumps(patcher_data).encode("utf-8"),
            filename="patcher.json",
            content_type="application/json",
        )
        yield scope


trace_function = sentry_sdk.trace
set_tag = sentry_sdk.set_tag
start_transaction = sentry_sdk.start_transaction
metrics = sentry_sdk.metrics


def trace_block(description: str):
    current_span = sentry_sdk.get_current_span()
    if current_span is not None:
        return current_span.start_child(
            op=sentry_sdk.consts.OP.FUNCTION,
            description=description,
        )
    else:
        return contextlib.nullcontext()
