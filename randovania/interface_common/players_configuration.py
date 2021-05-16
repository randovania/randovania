from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class PlayersConfiguration:
    player_index: int
    player_names: Dict[int, str]

    @property
    def is_multiworld(self) -> int:
        return len(self.player_names) > 1
