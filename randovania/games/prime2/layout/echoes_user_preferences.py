from __future__ import annotations

import dataclasses

from open_prime_rando.dol_patching.echoes.user_preferences import OprEchoesUserPreferences

from randovania.bitpacking.json_dataclass import JsonDataclass


@dataclasses.dataclass(frozen=True)
class EchoesUserPreferences(OprEchoesUserPreferences, JsonDataclass):
    pass
