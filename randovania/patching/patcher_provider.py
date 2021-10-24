from randovania.games.game import RandovaniaGame
from randovania.patching.patcher import Patcher


class PatcherProvider:
    def patcher_for_game(self, game: RandovaniaGame) -> Patcher:
        return game.data.patcher
