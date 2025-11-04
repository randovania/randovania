import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class GameTestData:
    """Contains data and configuration parameters to allow the test suit to assert things properly for this game."""

    expected_seed_hash: bytes
    """The seed hash expected for the layout generated in test_create_description."""

    generator_test_seed_number: int = 0
    """The seed number used in test_create_description."""
