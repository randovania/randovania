from unittest.mock import MagicMock, call

from randovania.lib.status_update_lib import DynamicSplitProgressUpdate


def test_dynamic_split_progress_single():
    # Setup
    raw_updater = MagicMock()

    # Run
    split = DynamicSplitProgressUpdate(raw_updater)
    u1 = split.create_split()
    u1("Hello", 0.0)
    u1("Hello2", 1.0)

    # Assert
    raw_updater.assert_has_calls([
        call("Hello", 0.0),
        call("Hello2", 1.0),
    ])


def test_dynamic_split_progress_two():
    # Setup
    raw_updater = MagicMock()

    # Run
    split = DynamicSplitProgressUpdate(raw_updater)
    u1 = split.create_split()
    u2 = split.create_split()
    u1("Hello", 0.0)
    u1("Hello2", 1.0)
    u2("Tests", 0.0)
    u2("Finish", 1.0)

    # Assert
    raw_updater.assert_has_calls([
        call("Hello", 0.0),
        call("Hello2", 0.5),
        call("Tests", 0.5),
        call("Finish", 1.0),
    ])


def test_dynamic_split_progress_weighted():
    # Setup
    raw_updater = MagicMock()

    # Run
    split = DynamicSplitProgressUpdate(raw_updater)
    u1 = split.create_split()
    u2 = split.create_split(weight=2.0)
    u3 = split.create_split()
    u1("Hello", 0.0)
    u1("Hello2", 1.0)
    u2("Tests", 0.0)
    u2("Middle", 1.0)
    u3("Final", 0.0)
    u3("Finish", 1.0)

    # Assert
    raw_updater.assert_has_calls([
        call("Hello", 0.0),
        call("Hello2", 0.25),
        call("Tests", 0.25),
        call("Middle", 0.75),
        call("Final", 0.75),
        call("Finish", 1.0),
    ])
