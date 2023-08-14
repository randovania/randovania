from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.exporter.game_exporter import GameExportParams

if TYPE_CHECKING:
    from pathlib import Path


@dataclasses.dataclass(frozen=True)
class EchoesGameExportParams(GameExportParams):
    input_path: Path | None
    output_path: Path
    contents_files_path: Path
    asset_cache_path: Path
    backup_files_path: Path
    prime_path: Path | None
    use_prime_models: bool
