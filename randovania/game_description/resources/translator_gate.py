from randovania.game_description.resources.resource_type import ResourceType


class TranslatorGate:
    _index: int

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.GATE_INDEX

    @property
    def long_name(self) -> str:
        return "TranslatorGate {}".format(self._index)

    def __init__(self, index: int):
        self._index = index

    def __lt__(self, other: "TranslatorGate") -> bool:
        return self._index < other._index

    def __repr__(self):
        return self.long_name

    def __hash__(self):
        return self._index

    def __eq__(self, other):
        return isinstance(other, TranslatorGate) and other._index == self._index

    @property
    def index(self) -> int:
        return self._index
