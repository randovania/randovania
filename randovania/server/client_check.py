from distutils.version import StrictVersion
from enum import Enum
from typing import Dict

import randovania


class ClientVersionCheck(Enum):
    STRICT = "strict"
    MATCH_MAJOR_MINOR = "match-major-minor"
    IGNORE = "ignore"


def check_client_version(version_checking: ClientVersionCheck, client_version: str, server_version: str):
    if version_checking == ClientVersionCheck.STRICT:
        if server_version != client_version:
            return f"Incompatible client version '{client_version}', expected '{server_version}'"

    elif version_checking == ClientVersionCheck.MATCH_MAJOR_MINOR:
        server = StrictVersion(server_version.split(".dev")[0])
        client = StrictVersion(client_version.split(".dev")[0])
        if server.version[:2] != client.version[:2]:
            shorter_client = "{}.{}".format(*client.version[:2])
            shorter_server = "{}.{}".format(*server.version[:2])
            return f"Incompatible client version '{shorter_client}', expected '{shorter_server}'"


def check_client_headers(expected_headers: Dict[str, str], environ: Dict[str, str]):
    wrong_headers = {}
    for name, expected in expected_headers.items():
        value = environ.get("HTTP_{}".format(name.upper().replace("-", "_")))
        if value != expected:
            wrong_headers[name] = value

    if wrong_headers:
        message = "\n".join(
            f"Expected '{expected_headers[name]}' for '{name}', got '{value}'."
            for name, value in wrong_headers.items()
        )
        return (
            "Incompatible client:\n{}\n\nServer is version {}, please confirm you're updated.".format(
                message, randovania.VERSION,
            )
        )
