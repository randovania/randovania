from dataclasses import dataclass


@dataclass(frozen=True)
class PlayersConfiguration:
    player_index: int
    player_names: dict[int, str]

    @property
    def is_multiworld(self) -> int:
        return len(self.player_names) > 1
