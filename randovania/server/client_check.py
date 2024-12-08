from enum import Enum

import randovania
from randovania.lib import version_lib


class ClientVersionCheck(Enum):
    STRICT = "strict"
    MATCH_MAJOR_MINOR = "match-major-minor"
    IGNORE = "ignore"


def check_client_version(version_checking: ClientVersionCheck, client_version: str, server_version: str):
    if version_checking == ClientVersionCheck.STRICT:
        if server_version != client_version:
            return f"Incompatible client version '{client_version}', expected '{server_version}'"

    elif version_checking == ClientVersionCheck.MATCH_MAJOR_MINOR:
        server = version_lib.parse_string(server_version)
        client = version_lib.parse_string(client_version)
        if server.release[:2] != client.release[:2]:
            shorter_client = "{}.{}".format(*client.release[:2])
            shorter_server = "{}.{}".format(*server.release[:2])
            return f"Incompatible client version '{shorter_client}', expected '{shorter_server}'"


def check_client_headers(expected_headers: dict[str, str], environ: dict[str, str]):
    wrong_headers = {}
    for name, expected in expected_headers.items():
        value = environ.get("HTTP_{}".format(name.upper().replace("-", "_")))
        if value != expected:
            wrong_headers[name] = value

    if wrong_headers:
        message = "\n".join(
            f"Expected '{expected_headers[name]}' for '{name}', got '{value}'." for name, value in wrong_headers.items()
        )
        return (
            f"Incompatible client:\n{message}\n\nServer is version {randovania.VERSION}, please confirm you're updated."
        )
