from __future__ import annotations

import functools
import ssl
import typing

import aiohttp
import certifi

if typing.TYPE_CHECKING:
    from aiohttp.typedefs import LooseHeaders


@functools.cache
def ssl_context(extra_certificates: str | None = None) -> ssl.SSLContext:
    """
    Creates an SSLContext that uses certificates from `certifi` instead of the host's.
    This puts certificate availability under our control and makes it consistent across platforms.

    The result is cached, so it must not be mutated by callers.

    :param extra_certificates: PEM-encoded certificates to trust, in addition to the ones from `certifi`.
    """
    context = ssl.create_default_context(cafile=certifi.where())
    if extra_certificates is not None:
        context.load_verify_locations(cadata=extra_certificates)
    return context


def http_session(
    headers: LooseHeaders | None = None,
    *,
    context: ssl.SSLContext | None = None,
) -> aiohttp.ClientSession:
    """
    Create an aiohttp.ClientSession, configured to use certificates from `certifi` instead of the host.

    :param headers: Headers to include in every request made with this session.
    :param context: The SSLContext to use. Defaults to `ssl_context()`.
    """
    return aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(ssl=context or ssl_context()))
