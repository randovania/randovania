from __future__ import annotations

import string

valid_chars = set(string.ascii_lowercase + string.ascii_uppercase + string.digits + " -")


def sanitize_for_path(name: str) -> str:
    return "".join(filter(lambda x: x in valid_chars, name))
