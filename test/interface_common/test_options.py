import itertools
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock, call

import pytest

import randovania.interface_common.options
import randovania.interface_common.persisted_options
from randovania.interface_common.options import Options
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutSkyTempleKeyMode


@pytest.fixture(name="option")
def _option() -> Options:
    return Options(MagicMock())


def test_migrate_from_v1():
    old_data = {"version": 1,
                "options": {"hud_memo_popup_removal": True,
                            "game_files_path": None,
                            "show_advanced_options": False,
                            "display_generate_help": True, "include_menu_mod": False, "layout_logic": "normal",
                            "layout_mode": "standard", "layout_sky_temple_keys": "randomized",
                            "layout_elevators": "vanilla", "layout_item_loss": "enabled", "quantity_for_pickup": {}}}

    # Run
    new_data = randovania.interface_common.persisted_options.get_persisted_options_from_data(old_data)

    # Assert
    assert new_data == {
        "patcher_configuration": {
            "disable_hud_popup": True,
            "menu_mod": False
        },
        "layout_configuration": {
            "trick_level": "normal",
            "sky_temple_keys": "fully-random",
            "item_loss": "enabled",
            "elevators": "vanilla",
            "pickup_quantities": {},
        }
    }


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
    option._output_directory = Path("start")
    option.on_options_changed = settings_changed

    # Run
    with option:
        option.output_directory = Path("end")

    # Assert
    mock_save_to_disk.assert_called_once_with(option)
    settings_changed.assert_called_once_with()


@patch("randovania.interface_common.options.Options._save_to_disk", autospec=True)
def test_single_save_with_nested_context_manager(mock_save_to_disk: MagicMock,
                                                 option: Options):
    # Setup
    option._output_directory = Path("start")

    # Run
    with option:
        option.output_directory = Path("end")
        with option:
            pass

    # Assert
    mock_save_to_disk.assert_called_once_with(option)


def test_changing_field_without_context_manager_should_error(option: Options):
    # Run
    with pytest.raises(AssertionError) as exception:
        option.output_directory = Path("start")

    # Assert
    assert str(exception.value) == "Attempting to edit an Options, but it wasn't made editable"


@patch("randovania.interface_common.options.get_persisted_options_from_data", autospec=True)
@patch("randovania.interface_common.options.Options._read_persisted_options", return_value=None, autospec=True)
def test_load_from_disk_no_data(mock_read_persisted_options: MagicMock,
                                mock_get_persisted_options_from_data: MagicMock,
                                option: Options):
    # Run
    option.load_from_disk()

    # Assert
    mock_read_persisted_options.assert_called_once_with(option)
    mock_get_persisted_options_from_data.assert_not_called()


@pytest.mark.parametrize("fields_to_test",
                         itertools.combinations(randovania.interface_common.options._SERIALIZER_FOR_FIELD.keys(), 2))
@patch("randovania.interface_common.options.Options._set_field", autospec=True)
@patch("randovania.interface_common.options.get_persisted_options_from_data", autospec=True)
@patch("randovania.interface_common.options.Options._read_persisted_options", autospec=True)
def test_load_from_disk_with_data(mock_read_persisted_options: MagicMock,
                                  mock_get_persisted_options_from_data: MagicMock,
                                  mock_set_field: MagicMock,
                                  fields_to_test: List[str],
                                  option: Options):
    # Setup
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
    mock_read_persisted_options.assert_called_once_with(option)
    mock_get_persisted_options_from_data.assert_called_once_with(mock_read_persisted_options.return_value)
    for field_name, serializer in new_serializers.items():
        serializer.decode.assert_called_once_with(persisted_options[field_name])

    mock_set_field.assert_has_calls(
        call(option, field_name, new_serializers[field_name].decode.return_value)
        for field_name in fields_to_test
    )


# TODO: test with an actual field as well
def test_serialize_fields(option: Options):
    # Setup

    # Run
    result = option._serialize_fields()

    # Assert
    assert result == {
        "version": 3,
        "options": {}
    }


_sample_layout_configurations = [
    {
        "trick_level": trick_level,
        "sky_temple_keys": LayoutSkyTempleKeyMode.FULLY_RANDOM,
        "item_loss": item_loss,
        "elevators": LayoutRandomizedFlag.RANDOMIZED,
        "pickup_quantities": {},
    }
    for trick_level in [LayoutTrickLevel.NO_TRICKS, LayoutTrickLevel.HARD, LayoutTrickLevel.MINIMAL_RESTRICTIONS]
    for item_loss in LayoutEnabledFlag
]


@pytest.fixture(params=_sample_layout_configurations, name="initial_layout_configuration_params")
def _initial_layout_configuration_params(request) -> dict:
    return request.param


@pytest.mark.parametrize("new_trick_level",
                         [LayoutTrickLevel.NO_TRICKS, LayoutTrickLevel.TRIVIAL, LayoutTrickLevel.HYPERMODE])
def test_edit_layout_trick_level(option: Options,
                                 initial_layout_configuration_params: dict,
                                 new_trick_level: LayoutTrickLevel):
    # Setup
    option._layout_configuration = LayoutConfiguration.from_params(**initial_layout_configuration_params)
    option._nested_autosave_level = 1

    # Run
    initial_layout_configuration_params["trick_level"] = new_trick_level
    setattr(option, "layout_configuration_trick_level", new_trick_level)

    # Assert
    assert option.layout_configuration == LayoutConfiguration.from_params(**initial_layout_configuration_params)


def test_edit_layout_quantity(option: Options,
                              initial_layout_configuration_params: dict):
    # Setup
    option._layout_configuration = LayoutConfiguration.from_params(**initial_layout_configuration_params)
    option._nested_autosave_level = 1
    pickup = next(option._layout_configuration.pickup_quantities.pickups())

    # Run
    initial_layout_configuration_params["pickup_quantities"] = {pickup.name: 12}
    option.set_quantity_for_pickup(pickup, 12)

    # Assert
    assert option.layout_configuration == LayoutConfiguration.from_params(**initial_layout_configuration_params)


def test_edit_during_options_changed(tmpdir):
    # Setup
    option = Options(Path(tmpdir))
    option._output_directory = Path("start")

    def on_changed():
        with option:
            option.output_directory = Path("final")

    option.on_options_changed = on_changed

    # Run
    with option:
        option.output_directory = Path("middle")

    second_option = Options(Path(tmpdir))
    second_option.load_from_disk()

    # Assert
    assert option.output_directory == Path("final")
    assert option.output_directory == second_option.output_directory
