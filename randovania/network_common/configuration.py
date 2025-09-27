from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import Required

    from randovania.discord_bot.bot import BotConfiguration
    from randovania.monitoring import SentryUrlKeys
    from randovania.server.configuration import ServerConfiguration


class NetworkConfiguration(TypedDict, total=False):
    server_address: Required[str]
    socketio_path: Required[str]

    guest_secret: str
    discord_client_id: int
    verify_ssl: bool

    sentry_urls: dict[SentryUrlKeys, str]
    sentry_sampling_rate: float

    discord_bot: BotConfiguration

    server_config: ServerConfiguration
