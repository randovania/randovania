from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import NamedRequirementTemplate
from randovania.games.factorio.layout import FactorioConfiguration
from randovania.resolver.bootstrap import Bootstrap

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.games.factorio.generator.base_patches_factory import FactorioGameSpecific
    from randovania.layout.base.base_configuration import BaseConfiguration


class FactorioBootstrap(Bootstrap):
    def apply_game_specific_patches(
        self, configuration: BaseConfiguration, game: GameDescription, patches: GamePatches
    ) -> None:
        assert isinstance(configuration, FactorioConfiguration)

        game_specific: FactorioGameSpecific = patches.game_specific

        for recipe in game_specific["recipes"]:
            # Assume all the custom recipes craft only one item, and it's the same name as the recipe
            result_item: str = recipe["recipe_name"]

            template = game.resource_database.requirement_template[f"craft-{result_item}"]
            assert isinstance(template.requirement, RequirementOr)
            assert len(template.requirement.items) == 1
            old_requirement = template.requirement.items[0]
            assert isinstance(old_requirement, RequirementAnd)

            new_items = [old_requirement.items[0]]
            assert isinstance(new_items[0], ResourceRequirement)  # the recipe is unlocked

            new_items.append(RequirementTemplate(f"perform-{recipe['category']}"))
            new_items.extend([RequirementTemplate(f"craft-{it['name']}") for it in recipe["ingredients"]])

            game.resource_database.requirement_template[f"craft-{result_item}"] = NamedRequirementTemplate(
                template.display_name, RequirementOr([RequirementAnd(new_items)])
            )
