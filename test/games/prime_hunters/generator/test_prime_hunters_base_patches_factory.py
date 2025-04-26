from __future__ import annotations

import dataclasses
from unittest.mock import MagicMock

from randovania.games.prime_hunters.generator.base_patches_factory import HuntersBasePatchesFactory
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement


def test_force_field_assignment_for_configuration_all_missile(
    prime_hunters_game_description, prime_hunters_configuration
):
    # Setup
    factory = HuntersBasePatchesFactory()

    force_field_configuration = prime_hunters_configuration.force_field_configuration
    configuration = dataclasses.replace(
        prime_hunters_configuration,
        force_field_configuration=dataclasses.replace(
            force_field_configuration,
            force_field_requirement=dict.fromkeys(
                force_field_configuration.force_field_requirement.keys(), LayoutForceFieldRequirement.MISSILE
            ),
        ),
    )

    rng = MagicMock()

    # Run
    results = factory.create_game_specific(configuration, prime_hunters_game_description, rng)

    # Assert
    assert list(results.keys()) == ["force_fields"]
    associated_requirements = list(results["force_fields"].values())
    assert associated_requirements == [LayoutForceFieldRequirement.MISSILE.value] * len(
        force_field_configuration.force_field_requirement
    )


def test_force_field_assignment_for_configuration_all_random(
    prime_hunters_game_description, prime_hunters_configuration
):
    # Setup
    factory = HuntersBasePatchesFactory()

    force_field_configuration = prime_hunters_configuration.force_field_configuration
    configuration = dataclasses.replace(
        prime_hunters_configuration,
        force_field_configuration=force_field_configuration.with_full_random(),
    )

    requirements = [
        LayoutForceFieldRequirement.JUDICATOR.value,
        LayoutForceFieldRequirement.IMPERIALIST.value,
        LayoutForceFieldRequirement.SHOCK_COIL.value,
    ]
    requirements = requirements * len(force_field_configuration.force_field_requirement)

    choices = [
        LayoutForceFieldRequirement.JUDICATOR,
        LayoutForceFieldRequirement.IMPERIALIST,
        LayoutForceFieldRequirement.SHOCK_COIL,
    ]
    rng = MagicMock()
    rng.choice.side_effect = choices * len(force_field_configuration.force_field_requirement)

    # Run
    results = factory.create_game_specific(configuration, prime_hunters_game_description, rng)

    # Assert
    assert list(results.keys()) == ["force_fields"]
    associated_requirements = list(results["force_fields"].values())
    assert associated_requirements == requirements[: len(force_field_configuration.force_field_requirement)]
