from __future__ import annotations

import pytest

from randovania.gui.dialog.connections_editor.path import RequirementTreePath

EMPTY = RequirementTreePath()
SINGLE = RequirementTreePath((2,))
DOUBLE = RequirementTreePath((0, 2))
TRIPLE = RequirementTreePath((0, 2, 1))


@pytest.mark.parametrize(("path", "expected"), [(SINGLE, 2), (DOUBLE, 2), (TRIPLE, 1)])
def test_row_returns_last(path: RequirementTreePath, expected: int):
    assert path.row() == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [(SINGLE, RequirementTreePath()), (DOUBLE, RequirementTreePath((0,))), (TRIPLE, RequirementTreePath((0, 2)))],
)
def test_parent_removes_last(path: RequirementTreePath, expected: RequirementTreePath):
    assert path.parent() == expected


@pytest.mark.parametrize(("path", "expected"), [(SINGLE, 2), (DOUBLE, 0), (TRIPLE, 0)])
def test_head_returns_first(path: RequirementTreePath, expected: int):
    assert path.head() == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [(SINGLE, RequirementTreePath()), (DOUBLE, RequirementTreePath((2,))), (TRIPLE, RequirementTreePath((2, 1)))],
)
def test_tail_removes_first(path: RequirementTreePath, expected: RequirementTreePath):
    assert path.tail() == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (EMPTY, RequirementTreePath((1,))),
        (SINGLE, RequirementTreePath((2, 1))),
        (DOUBLE, RequirementTreePath((0, 2, 1))),
        (TRIPLE, RequirementTreePath((0, 2, 1, 1))),
    ],
)
def test_extend_with_appends(path: RequirementTreePath, expected: RequirementTreePath):
    assert path.extend_with(1) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (EMPTY, RequirementTreePath((0,))),
        (SINGLE, RequirementTreePath((0, 2))),
        (DOUBLE, RequirementTreePath((0, 0, 2))),
        (TRIPLE, RequirementTreePath((0, 0, 2, 1))),
    ],
)
def test_prefixed_with_prepends(path: RequirementTreePath, expected: RequirementTreePath):
    assert path.prefixed_with(0) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (EMPTY, RequirementTreePath()),
        (SINGLE, RequirementTreePath((2,))),
        (DOUBLE, RequirementTreePath((2, 0))),
        (TRIPLE, RequirementTreePath((1, 2, 0))),
    ],
)
def test_reversed(path: RequirementTreePath, expected: RequirementTreePath):
    assert path.reversed() == expected


@pytest.mark.parametrize(
    ("path", "expected"), [(DOUBLE, RequirementTreePath((0, 3))), (TRIPLE, RequirementTreePath((0, 2, 2)))]
)
def test_next_sibling_increments_last(path: RequirementTreePath, expected: RequirementTreePath):
    assert path.next_sibling() == expected


@pytest.mark.parametrize(
    ("path", "expected"), [(DOUBLE, RequirementTreePath((0, 1))), (TRIPLE, RequirementTreePath((0, 2, 0)))]
)
def test_previous_sibling_decrements_last(path: RequirementTreePath, expected: RequirementTreePath):
    assert path.previous_sibling() == expected
