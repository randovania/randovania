from __future__ import annotations

from typing import TYPE_CHECKING, NotRequired, TypedDict

if TYPE_CHECKING:
    from randovania.server.client_check import ClientVersionCheck
    from randovania.server.discord_auth import EnforceRoleConfiguration


class ServerConfiguration(TypedDict, total=True):
    secret_key: str
    discord_client_secret: str
    fernet_key: str
    enforce_role: NotRequired[EnforceRoleConfiguration]
    client_version_checking: ClientVersionCheck
    database_path: str
    socketio_path: NotRequired[str]
