import randovania
from randovania.version_hash import full_git_hash

_CLIENT_DEFAULT_URL = "https://44282e1a237c48cfaf8120c40debc2fa@o4504594031509504.ingest.sentry.io/4504594037211137"
_SERVER_DEFAULT_URL = "https://c2147c86fecc490f8e7dcfc201d35895@o4504594031509504.ingest.sentry.io/4504594037276672"
_BOT_DEFAULT_URL = "https://7e7607e10378497689b443d8922870f7@o4504594031509504.ingest.sentry.io/4504606761287680"
_sampling_per_path = {
    'restore_user_session': 1.0,
}


def _init(include_flask: bool, default_url: str):
    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration

    configuration = randovania.get_configuration()

    integrations = [
        AioHttpIntegration(),
    ]

    if include_flask:
        from sentry_sdk.integrations.flask import FlaskIntegration
        integrations.append(FlaskIntegration())

    sentry_url = configuration.get("sentry_url", default_url)
    if sentry_url is None:
        return

    def traces_sampler(sampling_context):
        if randovania.is_dev_version():
            return 1.0
        else:
            if sampling_context['transaction_context']['op'] == 'message':
                return _sampling_per_path.get(sampling_context['transaction_context']['name'], 0.5)
            return 0.25

    sentry_sdk.init(
        dsn=sentry_url,
        integrations=integrations,
        release=full_git_hash,
        environment="staging" if randovania.is_dev_version() else "production",
        traces_sampler=traces_sampler,
    )


def client_init():
    return _init(False, _CLIENT_DEFAULT_URL)


def server_init():
    return _init(True, _SERVER_DEFAULT_URL)


def bot_init():
    return _init(False, _BOT_DEFAULT_URL)
