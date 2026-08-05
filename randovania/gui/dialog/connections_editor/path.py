from __future__ import annotations


class Path(tuple[int, ...]):
    """
    A series of indices for locating a Requirement within a requirement tree.

    Each index says "which child" to descend into at that level, starting from the tree's root. An empty Path() points
    to the root itself. Path((1,)) points to the second item within the root's children. Path((1, 0)) points to the
    first child of that second item, and so on.

    Every index except the last must point to a RequirementArrayBase, since only array requirements have children to
    descend into. The last index may point to any Requirement type, since that's the node the Path is actually
    identifying.

    This class does NOT perform validation. Attempting to get the row() or head() of an empty Path will result in an
    error. This extends to next_sibling() and previous_sibling() - these methods compute what the sibling's path would
    be, but do not guarantee that it exists in the requirement tree.
    """

    __slots__ = ()

    def row(self) -> int:
        """The last index in the Path - this node's position amongst siblings."""
        return self[-1]

    def parent(self) -> Path:
        """The Path to this node's parent, with the last index removed."""
        return Path(self[:-1])

    def head(self) -> int:
        """The first index in the Path - which child of the root to descend into."""
        return self[0]

    def tail(self) -> Path:
        """The remainder of the Path with its first index removed"""
        return Path(self[1:])

    def extend_with(self, idx: int) -> Path:
        """A new Path one level deeper, descending into child `idx` of this node."""
        return Path((*self, idx))

    def prefixed_with(self, idx: int) -> Path:
        """A new Path with `idx` inserted at the front, nesting this Path one level deeper within an outer index."""
        return Path((idx, *self))

    def reversed(self) -> Path:
        """This Path's indices in reverse order."""
        return Path(self[::-1])

    def next_sibling(self) -> Path:
        """The Path to the node immediately after this one, within the same parent."""
        return Path((*self[:-1], self[-1] + 1))

    def previous_sibling(self) -> Path:
        """The Path to the node immediately before this one, within the same parent."""
        return Path((*self[:-1], self[-1] - 1))
