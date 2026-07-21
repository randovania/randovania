from __future__ import annotations

import pytest

from randovania.gui.dialog.connections_editor.path import Path

EMPTY = Path()
SINGLE = Path((2,))
DOUBLE = Path((0, 2))
TRIPLE = Path((0, 2, 1))


@pytest.mark.parametrize(("path", "expected"), [(SINGLE, 2), (DOUBLE, 2), (TRIPLE, 1)])
def test_row_returns_last(path: Path, expected: int):
    assert path.row() == expected


@pytest.mark.parametrize(("path", "expected"), [(SINGLE, Path()), (DOUBLE, Path((0,))), (TRIPLE, Path((0, 2)))])
def test_parent_removes_last(path: Path, expected: Path):
    assert path.parent() == expected


@pytest.mark.parametrize(("path", "expected"), [(SINGLE, 2), (DOUBLE, 0), (TRIPLE, 0)])
def test_head_returns_first(path: Path, expected: int):
    assert path.head() == expected


@pytest.mark.parametrize(("path", "expected"), [(SINGLE, Path()), (DOUBLE, Path((2,))), (TRIPLE, Path((2, 1)))])
def test_tail_removes_first(path: Path, expected: Path):
    assert path.tail() == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [(EMPTY, Path((1,))), (SINGLE, Path((2, 1))), (DOUBLE, Path((0, 2, 1))), (TRIPLE, Path((0, 2, 1, 1)))],
)
def test_extend_with_appends(path: Path, expected: Path):
    assert path.extend_with(1) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [(EMPTY, Path((0,))), (SINGLE, Path((0, 2))), (DOUBLE, Path((0, 0, 2))), (TRIPLE, Path((0, 0, 2, 1)))],
)
def test_prefixed_with_prepends(path: Path, expected: Path):
    assert path.prefixed_with(0) == expected


@pytest.mark.parametrize(
    ("path", "expected"), [(EMPTY, Path()), (SINGLE, Path((2,))), (DOUBLE, Path((2, 0))), (TRIPLE, Path((1, 2, 0)))]
)
def test_reversed(path: Path, expected: Path):
    assert path.reversed() == expected


@pytest.mark.parametrize(("path", "expected"), [(DOUBLE, Path((0, 3))), (TRIPLE, Path((0, 2, 2)))])
def test_next_sibling_increments_last(path: Path, expected: Path):
    assert path.next_sibling() == expected


@pytest.mark.parametrize(("path", "expected"), [(DOUBLE, Path((0, 1))), (TRIPLE, Path((0, 2, 0)))])
def test_previous_sibling_decrements_last(path: Path, expected: Path):
    assert path.previous_sibling() == expected
