from __future__ import annotations

import uuid

import pytest

from randovania.interface_common.worlds_configuration import INVALID_UUID, is_uuid_multiworld


@pytest.mark.parametrize(
    ("world_uuid", "expected"),
    [
        (INVALID_UUID, False),
        (uuid.UUID("11111111-1111-8111-8111-111111111111"), False),
        (uuid.uuid4(), True),
        (uuid.UUID("22222222-2222-4222-a222-222222222222"), True),
    ],
)
def test_is_uuid_multiworld(world_uuid: uuid.UUID, expected: bool) -> None:
    assert is_uuid_multiworld(world_uuid) == expected
