from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Mapping

    from randovania.lib.json_lib import JsonObject_RO


class Unauthorized(Exception):
    """An Exception raised when user is not authorized."""


class InvalidRequest(Exception):
    """An Exception raised when a Request is not Valid"""


class RateLimited(Exception):
    """An Exception raised when a Request is not Valid"""

    def __init__(self, json: JsonObject_RO, headers: Mapping) -> None:
        self.json = json
        self.headers = headers
        self.message = json["message"]
        self.retry_after = json["retry_after"]
        super().__init__(self.message)


class InvalidToken(Exception):
    """An exception raised when a Response has invalid tokens"""


class ScopeMissing(Exception):
    scope: str

    def __init__(self, scope: str):
        self.scope = scope
        super().__init__(self.scope)


class ClientSessionNotInitialized(Exception):
    """An exception raised when no Client Session is initialized but one would be needed"""
