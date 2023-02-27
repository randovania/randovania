import logging
from pathlib import Path

from PySide6 import QtWidgets

from randovania.gui.lib import async_dialog, file_prompts
from randovania.layout.layout_description import LayoutDescription, InvalidLayoutDescription
from randovania.lib.migration_lib import UnsupportedVersion


async def load_layout_description(parent: QtWidgets.QWidget | None, path: Path) -> LayoutDescription | None:
    try:
        return LayoutDescription.from_file(path)

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
