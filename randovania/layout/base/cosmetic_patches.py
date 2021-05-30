import dataclasses

from randovania.bitpacking.json_dataclass import JsonDataclass


@dataclasses.dataclass(frozen=True)
class BaseCosmeticPatches(JsonDataclass):
    pass

    @classmethod
    def default(cls) -> "BaseCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        raise NotImplementedError()
