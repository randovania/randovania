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
    RandovaniaGame.METROID_PRIME: PrimeConfiguration,
    RandovaniaGame.METROID_PRIME_ECHOES: EchoesConfiguration,
    RandovaniaGame.METROID_PRIME_CORRUPTION: CorruptionConfiguration,
}

GAME_TO_COSMETIC: Dict[RandovaniaGame, Type[AnyCosmeticPatches]] = {
    RandovaniaGame.METROID_PRIME: PrimeCosmeticPatches,
    RandovaniaGame.METROID_PRIME_ECHOES: EchoesCosmeticPatches,
    RandovaniaGame.METROID_PRIME_CORRUPTION: CorruptionCosmeticPatches,
}
