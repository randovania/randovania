from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import NamedRequirementTemplate
from randovania.games.factorio.data_importer import data_parser
from randovania.games.factorio.generator import recipes
from randovania.games.factorio.layout import FactorioConfiguration
from randovania.resolver.bootstrap import Bootstrap

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.games.factorio.generator.base_patches_factory import FactorioGameSpecific
    from randovania.layout.base.base_configuration import BaseConfiguration


def _recipe_unlocked_requirements(items: list[ItemResourceInfo]) -> list[Requirement]:
    items = [ResourceRequirement.simple(it) for it in items]
    if len(items) > 1:
        return [RequirementAnd(items)]
    return items


class FactorioBootstrap(Bootstrap):
    def apply_game_specific_patches(
        self, configuration: BaseConfiguration, game: GameDescription, patches: GamePatches
    ) -> None:
        assert isinstance(configuration, FactorioConfiguration)

        recipes_raw = data_parser.load_recipes_raw()
        tech_for_recipe: dict[str, list[ItemResourceInfo]] = collections.defaultdict(list)
        for tech in game.resource_database.item:
            for recipe in tech.extra["recipes_unlocked"]:
                tech_for_recipe[recipe].append(tech)

        game_specific: FactorioGameSpecific = patches.game_specific

        for recipe_name, recipe_data in game_specific["recipes"].items():
            # Assume all the custom recipes craft only one item, and it's the same name as the recipe
            result_item: str = recipe_name
            recipe = recipes_raw[recipe_name]

            category = recipes.determine_recipe_category(
                recipe_name, recipe.get("category", "crafting"), recipe_data["ingredients"]
            )

            template = game.resource_database.requirement_template[f"craft-{result_item}"]
            new_items = _recipe_unlocked_requirements(tech_for_recipe[result_item])
            new_items.append(RequirementTemplate(f"perform-{category}"))
            new_items.extend([RequirementTemplate(f"craft-{it}") for it in recipe_data["ingredients"]])

            game.resource_database.requirement_template[f"craft-{result_item}"] = NamedRequirementTemplate(
                template.display_name, RequirementAnd(new_items)
            )
