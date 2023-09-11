from __future__ import annotations

import contextlib
import json
import platform
import re
import typing
from pathlib import Path

import sentry_sdk
import sentry_sdk.integrations.logging
import sentry_sdk.scrubber

import randovania

_CLIENT_DEFAULT_URL = "https://44282e1a237c48cfaf8120c40debc2fa@o4504594031509504.ingest.sentry.io/4504594037211137"
_SERVER_DEFAULT_URL = "https://c2147c86fecc490f8e7dcfc201d35895@o4504594031509504.ingest.sentry.io/4504594037276672"
_BOT_DEFAULT_URL = "https://7e7607e10378497689b443d8922870f7@o4504594031509504.ingest.sentry.io/4504606761287680"


def _filter_data(data, str_filter: typing.Callable[[str], str]) -> typing.Any | None:
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


def _filter_user_home(data):
    def filter_home(s: str) -> str:
        return _HOME_RE.sub(r"\1<redacted>\3", s)

    return _filter_data(data, filter_home)


class HomeEventScrubber(sentry_sdk.scrubber.EventScrubber):
    def scrub_dict(self, d):
        super().scrub_dict(d)
        _filter_user_home(d)


def _init(include_flask: bool, default_url: str, sampling_rate: float = 1.0, exclude_server_name: bool = False):
    if randovania.is_dirty():
        return

    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration

    configuration = randovania.get_configuration()

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

    sentry_url = configuration.get("sentry_url", default_url)
    if sentry_url is None:
        return

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
    )
    sentry_sdk.set_context(
        "os",
        {
            "name": platform.system(),
            "version": platform.release(),
        },
    )


def client_init():
    if not randovania.is_frozen():
        # TODO: It'd be nice to catch these running from source, but only for unmodified main.
        return

    _init(False, _CLIENT_DEFAULT_URL, exclude_server_name=True)
    sentry_sdk.set_tag("frozen", randovania.is_frozen())

    # Ignore the "packet queue is empty, aborting" message
    # It causes a disconnect, but we smoothly reconnect in that case.
    sentry_sdk.integrations.logging.ignore_logger("engineio.client")


def server_init(sampling_rate: float):
    return _init(True, _SERVER_DEFAULT_URL, sampling_rate=sampling_rate)


def bot_init():
    return _init(False, _BOT_DEFAULT_URL)


@contextlib.contextmanager
def attach_patcher_data(patcher_data: dict):
    with sentry_sdk.push_scope() as scope:
        scope.add_attachment(
            json.dumps(patcher_data).encode("utf-8"),
            filename="patcher.json",
            content_type="application/json",
        )
        yield


trace_function = sentry_sdk.trace
set_tag = sentry_sdk.set_tag


def trace_block(description: str):
    current_span = sentry_sdk.get_current_span()
    if current_span is not None:
        return current_span.start_child(
            op=sentry_sdk.consts.OP.FUNCTION,
            description=description,
        )
    else:
        return contextlib.nullcontext()
