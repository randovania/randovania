from randovania.game_description.resources.resource_type import ResourceType


class ScanAsset:
    _asset_id: int

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.LORE_INDEX

    @property
    def long_name(self) -> str:
        return "ScanAsset {}".format(self._asset_id)

    def __init__(self, asset_id: int):
        self._asset_id = asset_id

    def __lt__(self, other: "ScanAsset") -> bool:
        return self._asset_id < other._asset_id

    def __repr__(self):
        return self.long_name

    def __hash__(self):
        return self._asset_id

    def __eq__(self, other):
        return isinstance(other, ScanAsset) and other._asset_id == self._asset_id

    @property
    def asset_id(self) -> int:
        return self._asset_id
