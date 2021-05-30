import dataclasses

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.layout.prime2.echoes_user_preferences import EchoesUserPreferences


@dataclasses.dataclass(frozen=True)
class CorruptionCosmeticPatches(BaseCosmeticPatches):
    # qol_cosmetic: bool = True

    @classmethod
    def default(cls) -> "CorruptionCosmeticPatches":
        return cls()
