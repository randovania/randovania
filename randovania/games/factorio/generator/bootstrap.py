from __future__ import annotations

import collections
from typing import TYPE_CHECKING

import typing_extensions

from randovania.game_description.game_database_view import (
    GameDatabaseView,
    GameDatabaseViewProxy,
    ResourceDatabaseView,
    ResourceDatabaseViewProxy,
)
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import NamedRequirementTemplate
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.factorio.data_importer import data_parser
from randovania.games.factorio.generator import recipes
from randovania.games.factorio.layout import FactorioConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.no_op_damage_state import NoOpDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import (
        GameDatabaseView,
    )
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.games.factorio.generator.base_patches_factory import FactorioGameSpecific
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState


def _recipe_unlocked_requirements(items: list[ItemResourceInfo]) -> list[Requirement]:
    items = [ResourceRequirement.simple(it) for it in items]
    if len(items) > 1:
        return [RequirementAnd(items)]
    return items


class FactorioResourceDatabaseViewProxy(ResourceDatabaseViewProxy):
    def __init__(self, original: ResourceDatabaseView, replacement_templates: dict[str, NamedRequirementTemplate]):
        super().__init__(original)
        self._replacement_templates = replacement_templates

    @typing_extensions.override
    def get_template_requirement(self, name: str) -> NamedRequirementTemplate:
        if name in self._replacement_templates:
            return self._replacement_templates[name]
        return super().get_template_requirement(name)


class FactorioGameDatabaseViewProxy(GameDatabaseViewProxy):
    def __init__(self, original: GameDatabaseView, replacement_templates: dict[str, NamedRequirementTemplate]):
        super().__init__(original)
        self._replacement_templates = replacement_templates

    @typing_extensions.override
    def get_resource_database_view(self) -> ResourceDatabaseView:
        return FactorioResourceDatabaseViewProxy(super().get_resource_database_view(), self._replacement_templates)


class FactorioBootstrap(Bootstrap):
    def create_damage_state(self, game: GameDatabaseView, configuration: BaseConfiguration) -> DamageState:
        return NoOpDamageState()

    def apply_game_specific_patches(
        self, game: GameDatabaseView, configuration: BaseConfiguration, patches: GamePatches
    ) -> GameDatabaseView:
        assert isinstance(configuration, FactorioConfiguration)

        resource_database = game.get_resource_database_view()
        recipes_raw = data_parser.load_recipes_raw()
        tech_for_recipe: dict[str, list[ItemResourceInfo]] = collections.defaultdict(list)

        for tech in resource_database.get_all_resources_of_type(ResourceType.ITEM):
            for recipe in tech.extra["recipes_unlocked"]:
                tech_for_recipe[recipe].append(tech)

        game_specific: FactorioGameSpecific = patches.game_specific

        template_replacements = {}

        for recipe_name, recipe_data in game_specific["recipes"].items():
            # Assume all the custom recipes craft only one item, and it's the same name as the recipe
            result_item: str = recipe_name
            recipe = recipes_raw[recipe_name]

            category = recipes.determine_recipe_category(
                recipe_name, recipe.get("category", "crafting"), recipe_data["ingredients"]
            )

            template = resource_database.get_template_requirement(f"craft-{result_item}")
            new_items = _recipe_unlocked_requirements(tech_for_recipe[result_item])
            new_items.append(RequirementTemplate(f"perform-{category}"))
            new_items.extend([RequirementTemplate(f"craft-{it}") for it in recipe_data["ingredients"]])

            template_replacements[f"craft-{result_item}"] = NamedRequirementTemplate(
                template.display_name, RequirementAnd(new_items)
            )

        return FactorioGameDatabaseViewProxy(game, template_replacements)
