import itertools
import json
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

import randovania.interface_common.options
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter.options import EchoesPerGameOptions
from randovania.interface_common import update_checker, persisted_options
from randovania.interface_common.options import Options, DecodeFailedException, InfoAlert
from randovania.lib import migration_lib


@pytest.fixture(name="option")
def _option() -> Options:
    return Options(MagicMock())


def test_migrate_from_v11(option):
    old_data = {"version": 11,
                "options": {
                    "cosmetic_patches": {
                        "disable_hud_popup": True,
                        "speed_up_credits": True,
                        "open_map": True,
                        "pickup_markers": True,
                    }}}

    # Run
    new_data = persisted_options.get_persisted_options_from_data(old_data)
    option.load_from_persisted(new_data, False)

    # Assert
    expected_data = {
        "game_prime2": {
            "cosmetic_patches": {
                "disable_hud_popup": True,
                "speed_up_credits": True,
                "open_map": True,
                "pickup_markers": True,
                "unvisited_room_names": True
            },
            'input_path': None,
            'output_directory': None,
            'output_format': None,
            'use_external_models': []
        },
        "connector_builders": [],
        'schema_version': persisted_options._CURRENT_OPTIONS_FILE_VERSION,
    }
    assert new_data == expected_data


@patch("randovania.interface_common.options.Options._save_to_disk", autospec=True)
def test_context_manager_with_no_changes_doesnt_save(mock_save_to_disk: MagicMock,
                                                     option: Options):
    # Setup
    settings_changed = MagicMock()
    option.on_options_changed = settings_changed

    # Run
    with option:
        pass

    # Assert
    mock_save_to_disk.assert_not_called()
    settings_changed.assert_not_called()


@patch("randovania.interface_common.options.Options._save_to_disk", autospec=True)
def test_save_with_context_manager(mock_save_to_disk: MagicMock,
                                   option: Options):
    # Setup
    settings_changed = MagicMock()
    option._dark_mode = False
    option.on_options_changed = settings_changed

    # Run
    with option:
        option.dark_mode = True

    # Assert
    mock_save_to_disk.assert_called_once_with(option)
    settings_changed.assert_called_once_with()


@patch("randovania.interface_common.options.Options._save_to_disk", autospec=True)
def test_single_save_with_nested_context_manager(mock_save_to_disk: MagicMock,
                                                 option: Options):
    # Setup
    option._dark_mode = False

    # Run
    with option:
        option.dark_mode = True
        with option:
            pass

    # Assert
    mock_save_to_disk.assert_called_once_with(option)


def test_changing_field_without_context_manager_should_error(option: Options):
    # Run
    with pytest.raises(AssertionError) as exception:
        option.dark_mode = True

    # Assert
    assert str(exception.value) == "Attempting to edit an Options, but it wasn't made editable"


def test_getting_unknown_field_should_error(option: Options):
    # Run
    with pytest.raises(AttributeError) as exception:
        assert option.something_that_does_not_exist is None

    # Assert
    assert str(exception.value) == "something_that_does_not_exist"


def test_getting_unknown_game_should_error(option: Options):
    # Run
    with pytest.raises(AttributeError) as exception:
        assert option.game_unknown_game is None

    # Assert
    assert str(exception.value) == "game_unknown_game"


def test_set_options_for_game_with_wrong_type(option: Options):
    # Run
    with pytest.raises(ValueError) as exception:
        option.set_options_for_game(RandovaniaGame.METROID_PRIME, EchoesPerGameOptions(
            cosmetic_patches=RandovaniaGame.METROID_PRIME_ECHOES.data.layout.cosmetic_patches.default(),
        ))

    # Assert
    assert str(exception.value) == (
        "Expected <class 'randovania.games.prime1.exporter.options.PrimePerGameOptions'>, "
        "got <class 'randovania.games.prime2.exporter.options.EchoesPerGameOptions'>"
    )


def test_load_from_disk_no_data(tmp_path, mocker):
    # Setup
    mock_get_persisted_options_from_data: MagicMock = mocker.patch(
        "randovania.interface_common.persisted_options.get_persisted_options_from_data", autospec=True
    )
    option = Options(tmp_path)

    # Run
    option.load_from_disk()

    # Assert
    mock_get_persisted_options_from_data.assert_not_called()


def test_load_from_disk_first_successful(tmp_path, mocker):
    mocker.patch(
        "randovania.interface_common.persisted_options.find_config_files", autospec=True,
        return_value=[
            "[1]",
            "[2]",
        ]
    )
    mock_get_persisted_options_from_data = mocker.patch(
        "randovania.interface_common.persisted_options.get_persisted_options_from_data", autospec=True,
    )
    option = Options(tmp_path)
    option.load_from_persisted = MagicMock()

    # Run
    result = option.load_from_disk(False)

    # Assert
    assert result
    option.load_from_persisted.assert_called_once_with(mock_get_persisted_options_from_data.return_value, False)
    mock_get_persisted_options_from_data.assert_called_once_with([1])


def test_load_from_disk_first_failure(tmp_path, mocker):
    persisted_result = MagicMock()
    mocker.patch(
        "randovania.interface_common.persisted_options.find_config_files", autospec=True,
        return_value=[
            "[1]",
            "[2]",
        ]
    )
    mock_get_persisted_options_from_data = mocker.patch(
        "randovania.interface_common.persisted_options.get_persisted_options_from_data", autospec=True,
        side_effect=[
            migration_lib.UnsupportedVersion(),
            persisted_result,
        ]
    )
    option = Options(tmp_path)
    option.load_from_persisted = MagicMock()

    # Run
    result = option.load_from_disk(True)

    # Assert
    assert result
    option.load_from_persisted.assert_called_once_with(persisted_result, True)
    mock_get_persisted_options_from_data.assert_has_calls([
        call([1]),
        call([2]),
    ])


@pytest.mark.parametrize(
    "fields_to_test",
    [
        pytest.param(combination, id=",".join(combination))
        for combination in itertools.combinations(randovania.interface_common.options._SERIALIZER_FOR_FIELD.keys(), 2)
    ]
)
def test_load_from_disk_with_data(fields_to_test: list[str],
                                  tmp_path, mocker):
    # Setup
    mock_get_persisted_options_from_data: MagicMock = mocker.patch(
        "randovania.interface_common.persisted_options.get_persisted_options_from_data", autospec=True
    )
    mock_set_field: MagicMock = mocker.patch(
        "randovania.interface_common.options.Options._set_field", autospec=True
    )
    tmp_path.joinpath("config.json").write_text("[1, 2, 54, 69]")

    option = Options(tmp_path)

    persisted_options = {
        field_name: MagicMock()
        for field_name in fields_to_test
    }
    new_serializers = {
        field_name: MagicMock()
        for field_name in fields_to_test
    }
    mock_get_persisted_options_from_data.return_value = persisted_options

    # Run
    with patch.dict(randovania.interface_common.options._SERIALIZER_FOR_FIELD, new_serializers):
        option.load_from_disk()

    # Assert
    mock_get_persisted_options_from_data.assert_called_once_with([1, 2, 54, 69])
    for field_name, serializer in new_serializers.items():
        serializer.decode.assert_called_once_with(persisted_options[field_name])

    mock_set_field.assert_has_calls([
        call(option, field_name, new_serializers[field_name].decode.return_value)
        for field_name in fields_to_test
    ])


# TODO: test with an actual field as well
def test_serialize_fields(option: Options):
    # Setup

    # Run
    result = option._serialize_fields()

    # Assert
    assert result == {
        "version": randovania.interface_common.persisted_options._CURRENT_OPTIONS_FILE_VERSION,
        "options": {
            "last_changelog_displayed": str(update_checker.strict_current_version()),
        }
    }


def test_edit_during_options_changed(tmpdir):
    # Setup
    option = Options(Path(tmpdir))
    option._displayed_alerts = set()

    def on_changed():
        with option:
            option.displayed_alerts = {InfoAlert.MULTIWORLD_FAQ}

    option.on_options_changed = on_changed

    # Run
    with option:
        option.displayed_alerts = {InfoAlert.FAQ}

    second_option = Options(Path(tmpdir))
    second_option.load_from_disk()

    # Assert
    assert option.displayed_alerts == {InfoAlert.MULTIWORLD_FAQ}
    assert option.displayed_alerts == second_option.displayed_alerts


@pytest.mark.parametrize("ignore_decode_errors", [False, True])
def test_load_from_disk_missing_json(ignore_decode_errors: bool,
                                     tmpdir):
    # Setup
    option = Options(Path(tmpdir))
    tmpdir.join("config.json").write_text("wtf", "utf-8")

    if ignore_decode_errors:
        result = option.load_from_disk(ignore_decode_errors)
        assert result != ignore_decode_errors
    else:
        with pytest.raises(DecodeFailedException):
            option.load_from_disk(ignore_decode_errors)


@pytest.mark.parametrize("ignore_decode_errors", [False])
def test_load_from_disk_invalid_json(ignore_decode_errors: bool,
                                     tmpdir):
    # Setup
    option = Options(Path(tmpdir))
    tmpdir.join("config.json").write_text(
        json.dumps(randovania.interface_common.persisted_options.serialized_data_for_options({
            "game_prime2": {
                "cosmetic_patches": {
                    "pickup_model_style": "invalid-value"
                }
            }
        })),
        "utf-8")

    if ignore_decode_errors:
        result = option.load_from_disk(ignore_decode_errors)
        assert result != ignore_decode_errors
    else:
        with pytest.raises(DecodeFailedException):
            option.load_from_disk(ignore_decode_errors)


def test_reset_to_defaults():
    # Create and test they're equal
    blank = Options(MagicMock())
    modified = Options(MagicMock())
    assert blank._serialize_fields() == modified._serialize_fields()

    # Modify and test they're different
    with modified:
        for field in randovania.interface_common.options._SERIALIZER_FOR_FIELD.keys():
            # This cause weirdness in serializing it
            if field != "last_changelog_displayed":
                modified._set_field(field, getattr(modified, field))
    assert blank._serialize_fields() != modified._serialize_fields()

    # Reset and test they're the same
    with modified:
        modified.reset_to_defaults()
    assert blank._serialize_fields() == modified._serialize_fields()


def test_setting_fields_to_self_do_nothing():
    options = Options(MagicMock())
    initial_serialize = options._serialize_fields()

    # Modify and test they're different
    with options:
        for field in randovania.interface_common.options._SERIALIZER_FOR_FIELD.keys():
            setattr(options, field, getattr(options, field))

    # Reset and test they're the same
    assert options._serialize_fields() == initial_serialize


def test_mark_alert_as_displayed(tmp_path):
    opt = Options(tmp_path)

    all_alerts = (InfoAlert.FAQ, InfoAlert.MULTIWORLD_FAQ)
    for alert in all_alerts:
        assert not opt.is_alert_displayed(alert)
        opt.mark_alert_as_displayed(alert)
        assert opt.is_alert_displayed(alert)

    assert opt.displayed_alerts == set(all_alerts)

    new_opt = Options(tmp_path)
    new_opt.load_from_disk()
    assert new_opt.displayed_alerts == set(all_alerts)


def test_set_parent_for_preset(tmp_path):
    opt = Options(tmp_path)
    u1 = uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6')
    u2 = uuid.UUID('b51fdeaa-1fff-4b79-8cd6-3e5a78077fa6')

    assert opt.get_parent_for_preset(u1) is None
    opt.set_parent_for_preset(u1, u2)
    assert opt.get_parent_for_preset(u1) == u2
