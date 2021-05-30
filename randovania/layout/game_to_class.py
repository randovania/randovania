from typing import Union, Dict, Type

from randovania.games.game import RandovaniaGame
from randovania.layout.prime1.prime_configuration import PrimeConfiguration
from randovania.layout.prime1.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.layout.prime3.corruption_configuration import CorruptionConfiguration
from randovania.layout.prime3.corruption_cosmetic_patches import CorruptionCosmeticPatches

AnyGameConfiguration = Union[PrimeConfiguration, EchoesConfiguration, CorruptionConfiguration]
AnyCosmeticPatches = Union[PrimeCosmeticPatches, EchoesCosmeticPatches, CorruptionCosmeticPatches]

GAME_TO_CONFIGURATION: Dict[RandovaniaGame, Type[AnyGameConfiguration]] = {
    RandovaniaGame.PRIME1: PrimeConfiguration,
    RandovaniaGame.PRIME2: EchoesConfiguration,
    RandovaniaGame.PRIME3: CorruptionConfiguration,
}

GAME_TO_COSMETIC: Dict[RandovaniaGame, Type[AnyCosmeticPatches]] = {
    RandovaniaGame.PRIME1: PrimeCosmeticPatches,
    RandovaniaGame.PRIME2: EchoesCosmeticPatches,
    RandovaniaGame.PRIME3: CorruptionCosmeticPatches,
}
