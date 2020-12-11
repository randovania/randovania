from unittest.mock import MagicMock, ANY

from randovania.games.prime import all_prime_dol_patches


def test_apply_string_display_patch():
    offsets = all_prime_dol_patches.StringDisplayPatchAddresses(0x15, 0, 0, 0, 0, 0)
    dol_file = MagicMock()

    # Run
    all_prime_dol_patches.apply_string_display_patch(offsets, dol_file)

    # Assert
    dol_file.write.assert_called_once_with(0x15, ANY)

