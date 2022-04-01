import dataclasses

from randovania.games.game import RandovaniaGame


def test_dangerous_settings(preset_manager):
    configuration = preset_manager.default_preset_for_game(RandovaniaGame.BLANK).get_preset().configuration
    dangerous_config = dataclasses.replace(configuration, first_progression_must_be_local=True)

    # Run
    no_dangerous = configuration.dangerous_settings()
    has_dangerous = dangerous_config.dangerous_settings()

    # Assert
    assert no_dangerous == []
    assert has_dangerous == ["Requiring first progression to be local causes increased generation failure."]
