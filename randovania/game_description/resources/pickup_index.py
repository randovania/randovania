class PickupIndex:
    __slots__ = ("_index",)
    _index: int

    @property
    def long_name(self) -> str:
        return f"PickupIndex {self._index}"

    @property
    def short_name(self):
        return self.long_name

    def __init__(self, index: int):
        self._index = index

    def __lt__(self, other: "PickupIndex") -> bool:
        return self._index < other._index

    def __repr__(self):
        return self.long_name

    def __hash__(self):
        return self._index

    def __eq__(self, other):
        return isinstance(other, PickupIndex) and other._index == self._index

    @property
    def index(self) -> int:
        return self._index

    @property
    def as_json(self):
        return self._index

    @classmethod
    def from_json(cls, value):
        return cls(value)
