import json
from pathlib import Path
from typing import Any


def read_path(path: Path) -> Any:
    with path.open("r") as file:
        return json.load(file)
