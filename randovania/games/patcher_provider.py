from randovania.games.game import RandovaniaGame
from randovania.games.patcher import Patcher
from randovania.games.patchers import claris_patcher
from randovania.interface_common.options import Options


def patcher_for_game(game: RandovaniaGame) -> Patcher:
    if game == RandovaniaGame.PRIME1:
        raise ValueError("Prime 1 can't patch!")

    elif game == RandovaniaGame.PRIME2:
        return claris_patcher.instance

    elif game == RandovaniaGame.PRIME3:
        raise ValueError("Prime 3 can't patch!")

    else:
        raise ValueError(f"Unknown game: {game}")


class PatcherProvider:
    def __init__(self, options: Options):
        self._patchers = {
            RandovaniaGame.PRIME2: claris_patcher.ClarisPatcher(options),
        }

    def patcher_for_game(self, game: RandovaniaGame) -> Patcher:
        return self._patchers[game]
