from __future__ import annotations

import ssl
import typing

import aiohttp
import certifi

if typing.TYPE_CHECKING:
    from aiohttp.typedefs import LooseHeaders


def http_session(headers: LooseHeaders | None = None) -> aiohttp.ClientSession:
    """
    Create an aiohttp.ClientSession, configured to use certificates from `certifi` instead of the host.
    This puts certificate availability under our control and makes it consistent across platforms.
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    return aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(ssl=ssl_context))
