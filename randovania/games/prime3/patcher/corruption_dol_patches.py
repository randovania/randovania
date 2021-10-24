import dataclasses

from randovania.patching.prime.all_prime_dol_patches import BasePrimeDolVersion


@dataclasses.dataclass(frozen=True)
class CorruptionDolVersion(BasePrimeDolVersion):
    pass
