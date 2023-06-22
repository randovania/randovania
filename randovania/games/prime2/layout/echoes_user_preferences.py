import dataclasses

from opr.echoes_user_preferences import OprEchoesUserPreferences
from randovania.bitpacking.json_dataclass import JsonDataclass


@dataclasses.dataclass(frozen=True)
class EchoesUserPreferences(OprEchoesUserPreferences, JsonDataclass):
    pass
