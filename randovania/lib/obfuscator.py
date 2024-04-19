from __future__ import annotations

import json

import cryptography
from cryptography.fernet import Fernet

try:
    from randovania.lib.obfuscator_secret import secret as _secret  # type: ignore
except ImportError:
    _secret = None

_encrypt: Fernet | None = None


class MissingSecret(Exception):
    pass


class InvalidSecret(Exception):
    pass


def _get_fernet() -> Fernet:
    if _secret is None:
        raise MissingSecret

    global _encrypt
    if _encrypt is None:
        _encrypt = Fernet(_secret)

    return _encrypt


def obfuscate(data: bytes) -> str:
    return _get_fernet().encrypt(data).decode("ascii")


def obfuscate_json(data: dict) -> str:
    return obfuscate(json.dumps(data).encode("utf-8"))


def deobfuscate(data: str) -> bytes:
    try:
        return _get_fernet().decrypt(data)
    except cryptography.fernet.InvalidToken:
        raise InvalidSecret from None


def deobfuscate_json(data: str) -> dict:
    return json.loads(deobfuscate(data).decode("utf-8"))
