import contextlib
import json
import platform
import re
import typing
from pathlib import Path

import sentry_sdk

import randovania
from randovania.version_hash import full_git_hash

_CLIENT_DEFAULT_URL = "https://44282e1a237c48cfaf8120c40debc2fa@o4504594031509504.ingest.sentry.io/4504594037211137"
_SERVER_DEFAULT_URL = "https://c2147c86fecc490f8e7dcfc201d35895@o4504594031509504.ingest.sentry.io/4504594037276672"
_BOT_DEFAULT_URL = "https://7e7607e10378497689b443d8922870f7@o4504594031509504.ingest.sentry.io/4504606761287680"
_sampling_per_path = {
    'restore_user_session': 1.0,
}


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


_HOME_RE = re.compile(r"(:[/\\]Users[/\\])([^/\\]+)([/\\])")


def _filter_windows_home(data):
    def filter_home(s: str) -> str:
        return _HOME_RE.sub(r"\1<redacted>\3", s)

    return _filter_data(data, filter_home)


def _before_send(event, hint):
    _filter_windows_home(event["extra"])
    if "logentry" in event:
        _filter_windows_home(event["logentry"])
    return event


def _before_breadcrumb(event, hint):
    _filter_windows_home(event)
    return event


def _init(include_flask: bool, default_url: str, sampling_rate: float = 0.25, exclude_server_name: bool = False):
    if randovania.is_dirty():
        return

    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration

    configuration = randovania.get_configuration()

    integrations = [
        AioHttpIntegration(),
    ]

    if include_flask:
        from sentry_sdk.integrations.flask import FlaskIntegration
        integrations.append(FlaskIntegration())

    server_name = None
    if exclude_server_name:
        # hostname for clients contains pii, so exclude them if we're not doing server.
        server_name = "client"

    sentry_url = configuration.get("sentry_url", default_url)
    if sentry_url is None:
        return

    def traces_sampler(sampling_context):
        if randovania.is_dev_version():
            return 1.0
        else:
            if sampling_context['transaction_context']['op'] == 'message':
                return _sampling_per_path.get(sampling_context['transaction_context']['name'], 0.5)
            return sampling_rate

    sentry_sdk.init(
        dsn=sentry_url,
        integrations=integrations,
        release=full_git_hash,
        environment="staging" if randovania.is_dev_version() else "production",
        traces_sampler=traces_sampler,
        server_name=server_name,
        before_send=_before_send,
        before_breadcrumb=_before_breadcrumb,
        auto_session_tracking=include_flask,
    )
    sentry_sdk.set_context("os", {
        "name": platform.system(),
        "version": platform.release(),
    })


def client_init():
    _init(False, _CLIENT_DEFAULT_URL,
          exclude_server_name=True)
    sentry_sdk.set_tag("frozen", randovania.is_frozen())


def server_init():
    return _init(True, _SERVER_DEFAULT_URL)


def bot_init():
    return _init(False, _BOT_DEFAULT_URL, sampling_rate=1.0)


@contextlib.contextmanager
def attach_patcher_data(patcher_data: dict):
    with sentry_sdk.configure_scope() as scope:
        scope.add_attachment(
            json.dumps(patcher_data).encode("utf-8"),
            filename="patcher.json",
            content_type="application/json",
        )
        yield
