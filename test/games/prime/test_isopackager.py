import sys
from unittest.mock import patch

from randovania.games.prime import iso_packager


def test_can_process_iso_success():
    assert iso_packager.can_process_iso()


def test_can_process_iso_failure():
    with patch.dict(sys.modules, nod=None):
        del sys.modules["randovania.games.prime.iso_packager"]
        from randovania.games.prime.iso_packager import can_process_iso
        assert not can_process_iso()
