from __future__ import annotations

import dataclasses
from pathlib import Path

from randovania.exporter.game_exporter import GameExportParams


@dataclasses.dataclass(frozen=True)
class EchoesGameExportParams(GameExportParams):
    input_path: Path | None
    output_path: Path
    contents_files_path: Path
    asset_cache_path: Path
    backup_files_path: Path
    prime_path: Path | None
    use_prime_models: bool
