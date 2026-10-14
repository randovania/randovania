from __future__ import annotations

import pytest

from randovania.layout.versioned_preset import VersionedPreset


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("My Preset", "my-preset"),
        ("Préset Ünicode", "preset-unicode"),
    ],
)
def test_slug_name(name: str, expected: str) -> None:
    preset = VersionedPreset({"name": name}, from_layout_description=False)

    assert preset.slug_name == expected
