import py
import pytest


@pytest.fixture
def test_files_dir():
    return py.path.local(__file__).new(basename="test_files")
