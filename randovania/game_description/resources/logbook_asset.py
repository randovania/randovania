from randovania.game_description.resources.resource_type import ResourceType


class LogbookAsset:
    _string_asset_id: int

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.LOGBOOK_INDEX

    @property
    def long_name(self) -> str:
        return "LogbookAsset 0x{:08X}".format(self._string_asset_id)

    def __init__(self, asset_id: int):
        self._string_asset_id = asset_id

    def __lt__(self, other: "LogbookAsset") -> bool:
        return self._string_asset_id < other._string_asset_id

    def __repr__(self):
        return self.long_name

    def __hash__(self):
        return self._string_asset_id

    def __eq__(self, other):
        return isinstance(other, LogbookAsset) and other._string_asset_id == self._string_asset_id

    @property
    def asset_id(self) -> int:
        return self._string_asset_id
