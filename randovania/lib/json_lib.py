import json
from pathlib import Path
from typing import Any


def read_path(path: Path) -> Any:
    with path.open("r") as file:
        return json.load(file)


def write_path(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=4, separators=(',', ': '))
    )
