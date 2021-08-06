from typing import Union, Dict, Type

from randovania.games.game import RandovaniaGame
from randovania.layout.prime1.prime_configuration import PrimeConfiguration
from randovania.layout.prime1.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.layout.prime3.corruption_configuration import CorruptionConfiguration
from randovania.layout.prime3.corruption_cosmetic_patches import CorruptionCosmeticPatches
from randovania.layout.super_metroid.super_metroid_configuration import SuperMetroidConfiguration
from randovania.layout.super_metroid.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches

AnyGameConfiguration = Union[PrimeConfiguration, EchoesConfiguration, CorruptionConfiguration,
                             SuperMetroidConfiguration]
AnyCosmeticPatches = Union[PrimeCosmeticPatches, EchoesCosmeticPatches, CorruptionCosmeticPatches,
                           SuperMetroidCosmeticPatches]

GAME_TO_CONFIGURATION: Dict[RandovaniaGame, Type[AnyGameConfiguration]] = {
    RandovaniaGame.METROID_PRIME: PrimeConfiguration,
    RandovaniaGame.METROID_PRIME_ECHOES: EchoesConfiguration,
    RandovaniaGame.METROID_PRIME_CORRUPTION: CorruptionConfiguration,
    RandovaniaGame.SUPER_METROID: SuperMetroidConfiguration,
}

GAME_TO_COSMETIC: Dict[RandovaniaGame, Type[AnyCosmeticPatches]] = {
    RandovaniaGame.METROID_PRIME: PrimeCosmeticPatches,
    RandovaniaGame.METROID_PRIME_ECHOES: EchoesCosmeticPatches,
    RandovaniaGame.METROID_PRIME_CORRUPTION: CorruptionCosmeticPatches,
    RandovaniaGame.SUPER_METROID: SuperMetroidCosmeticPatches,
}
