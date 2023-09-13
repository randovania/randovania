from __future__ import annotations

from enum import Enum

import pytest

from randovania.lib import enum_lib


def test_add_missing_fields():
    class A(Enum):
        first = 1
        second = 2

    with pytest.raises(ValueError, match="long_name for <enum 'A'> are not synchronized"):
        enum_lib.add_long_name(A, {A.first: "FIRST"})
