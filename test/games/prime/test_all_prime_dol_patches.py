from unittest.mock import MagicMock, ANY

from randovania.games.game import RandovaniaGame
from randovania.games.prime import all_prime_dol_patches


def test_apply_string_display_patch():
    offsets = all_prime_dol_patches.StringDisplayPatchAddresses(0x15, 0, 0, 0, 0, 0)
    dol_file = MagicMock()

    # Run
    all_prime_dol_patches.apply_string_display_patch(offsets, dol_file)

    # Assert
    dol_file.write.assert_called_once_with(0x15, ANY)


def test_apply_reverse_energy_tank_heal_patch_active(dol_file):
    game = RandovaniaGame.PRIME2
    addresses = all_prime_dol_patches.DangerousEnergyTankAddresses(
        small_number_float=0x1600,
        incr_pickup=0x2000,
    )

    # Run
    dol_file.set_editable(True)
    with dol_file:
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(0x1500, addresses, False, game, dol_file)
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(0x1500, addresses, True, game, dol_file)

    # Assert
    results = dol_file.dol_path.read_bytes()[0x100:]
    assert results == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\xc0\x02\x01\x00\xd0\x1e\x00\x14\x60\x00\x00\x00\x60\x00\x00\x00')


def test_apply_reverse_energy_tank_heal_patch_inactive(dol_file):
    game = RandovaniaGame.PRIME2
    addresses = all_prime_dol_patches.DangerousEnergyTankAddresses(
        small_number_float=0x1600,
        incr_pickup=0x2000,
    )

    # Run
    dol_file.set_editable(True)
    with dol_file:
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(0x1500, addresses, True, game, dol_file)
        all_prime_dol_patches.apply_reverse_energy_tank_heal_patch(0x1500, addresses, False, game, dol_file)

    # Assert
    results = dol_file.dol_path.read_bytes()[0x100:]
    assert results == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x7f\xc3\xf3\x78\x38\x80\x00\x29\x38\xa0\x27\x0f\x4b\xff\xff\x65')
