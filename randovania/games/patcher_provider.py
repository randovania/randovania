from randovania.games.game import RandovaniaGame
from randovania.games.patcher import Patcher
from randovania.interface_common.options import Options


class PatcherProvider:
    def __init__(self, options: Options):
        from randovania.games.patchers import claris_patcher
        from randovania.games.patchers import randomprime_patcher
        self._patchers = {
            RandovaniaGame.PRIME1: randomprime_patcher.RandomprimePatcher(),
            RandovaniaGame.PRIME2: claris_patcher.ClarisPatcher(),
        }

    def patcher_for_game(self, game: RandovaniaGame) -> Patcher:
        return self._patchers[game]
