from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

import randovania

if TYPE_CHECKING:
    from randovania.lib.status_update_lib import ProgressUpdateCallable


def find_bad_installation(
    hash_list: dict[str, str],
    progress_update: ProgressUpdateCallable,
) -> tuple[list[str], set[str]]:
    root = randovania.get_file_path()

    extra_files = set()
    bad_files = []

    progress_update("Checking for unexpected files", -1)
    for f in root.rglob("*"):
        relative = os.fspath(f.relative_to(root))
        if f.is_file() and relative not in hash_list:
            extra_files.add(relative)

    total = len(hash_list)
    for i, (name, expected_hash) in enumerate(hash_list.items()):
        try:
            actual_hash = hashlib.sha256(root.joinpath(name).read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                bad_files.append(name)

        except OSError:
            bad_files.append(name)

        progress_update(f"{i + 1} out of {total} files checked.", (i + 1) / total)

    extra_files.remove(os.fspath(Path("data").joinpath("frozen_file_list.json")))
    extra_files.remove("randovania.exe")

    return bad_files, extra_files
