from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from randovania.gui.lib import async_dialog, file_prompts
from randovania.layout.layout_description import InvalidLayoutDescription, LayoutDescription
from randovania.lib.migration_lib import UnsupportedVersion

if TYPE_CHECKING:
    from pathlib import Path

    from PySide6 import QtWidgets


async def load_layout_description(parent: QtWidgets.QWidget | None, path: Path) -> LayoutDescription | None:
    try:
        return LayoutDescription.from_file(path)

    except (UnicodeDecodeError, json.JSONDecodeError):
        await async_dialog.warning(
            parent,
            "Unable to load game file",
            "File is not a Randovania game file.",
        )

    except (InvalidLayoutDescription, UnsupportedVersion) as e:
        logging.info("Unable to load layout file: %s (%s)", str(e), type(e).__name__)
        await async_dialog.warning(
            parent,
            "Unable to load game file",
            str(e),
        )

    return None


async def prompt_and_load_layout_description(parent: QtWidgets.QWidget) -> LayoutDescription | None:
    json_path = await file_prompts.prompt_input_layout(parent)
    if json_path is None:
        return None
    return await load_layout_description(parent, json_path)
