from __future__ import annotations

import dataclasses
from pathlib import Path

from randovania.exporter.game_exporter import GameExportParams, input_hash_for_directory, input_hash_for_file


@dataclasses.dataclass(frozen=True)
class EchoesGameExportParams(GameExportParams):
    input_path: Path | None
    output_path: Path
    contents_files_path: Path
    asset_cache_path: Path
    backup_files_path: Path
    prime_path: Path | None
    use_prime_models: bool

    def calculate_input_hash(self) -> dict[str, str | None]:
        return {
            "prime2_iso": input_hash_for_file(self.input_path),
            "backup_files_path": input_hash_for_directory(self.backup_files_path),
            "prime1_iso": input_hash_for_file(self.prime_path),
        }
