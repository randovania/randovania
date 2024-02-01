from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

import randovania

if TYPE_CHECKING:
    from randovania.lib.status_update_lib import ProgressUpdateCallable


def hash_everything_in(root: Path) -> dict[str, str]:
    hash_list: dict[str, str] = {}

    for f in root.rglob("*"):
        relative = os.fspath(f.relative_to(root))
        if f.is_file():
            hash_list[relative] = hashlib.sha256(f.read_bytes()).hexdigest()

    return hash_list


def find_bad_installation(
    expected_hashes: dict[str, str],
    progress_update: ProgressUpdateCallable,
) -> tuple[list[str], list[str], set[str]]:
    """Hashes all files in the file path and compares to a known good list when the executable was created.
    Returns three lists:
    - Files with different hash
    - Files that are missing
    - Files that were not expected
    """
    root = randovania.get_file_path()

    extra_files = set()
    bad_files = []
    missing_files = []

    actual_hashes = hash_everything_in(root)

    progress_update("Checking for unexpected files", -1)
    for relative in actual_hashes.keys():
        if relative not in expected_hashes:
            extra_files.add(relative)

    total = len(expected_hashes)
    for i, (name, expected_hash) in enumerate(expected_hashes.items()):
        if name in actual_hashes:
            if actual_hashes[name] != expected_hash:
                bad_files.append(name)
        else:
            missing_files.append(name)

        progress_update(f"{i + 1} out of {total} files checked.", (i + 1) / total)

    extra_files.remove(os.fspath(Path("data").joinpath("frozen_file_list.json")))

    return bad_files, missing_files, extra_files
