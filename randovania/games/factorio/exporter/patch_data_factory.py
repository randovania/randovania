from __future__ import annotations

import typing

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.games.factorio.data_importer import data_parser
from randovania.games.factorio.generator import recipes
from randovania.games.factorio.generator.item_cost import item_is_fluid
from randovania.games.factorio.layout import FactorioConfiguration, FactorioCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator

if typing.TYPE_CHECKING:
    import factorio_randovania_mod.configuration as cfg

    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.games.factorio.generator.base_patches_factory import FactorioGameSpecific


class FactorioPatchDataFactory(PatchDataFactory[FactorioConfiguration, FactorioCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.FACTORIO

    def create_useless_pickup(self) -> PickupEntry:
        """Used for any location with no PickupEntry assigned to it."""
        return pickup_creator.create_nothing_pickup(
            self.game.resource_database,
            model_name="__randovania-assets__/graphics/icons/nothing.png",
        )

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return self.create_useless_pickup()

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        rl = self.game.region_list

        technologies = []

        for exported in self.export_pickup_list():
            node = rl.node_from_pickup_index(exported.index)
            area = rl.nodes_to_area(node)

            prerequisites = []

            con_req = area.connections[area.node_with_name("Connection to Tech Tree")][node]
            assert isinstance(con_req, RequirementAnd)

            for req in con_req.items:
                if isinstance(req, NodeRequirement):
                    other_node = rl.node_by_identifier(req.node_identifier)
                    prerequisites.append(other_node.extra["tech_name"])

            new_tech = {
                "tech_name": node.extra["tech_name"],
                "locale_name": exported.name,
                "description": exported.description,
                "icon": exported.model.name,
                "icon_size": 64 if exported.model.name.startswith("__base__/graphics/icons") else 256,
                "cost_reference": node.extra["original_tech"],
                "prerequisites": prerequisites,
                "unlocks": [
                    conditional.resources[0][0].short_name
                    for conditional in exported.conditional_resources
                    if conditional.resources
                ],
            }

            technologies.append(new_tech)

        result: cfg.Configuration = {
            "configuration_identifier": self.description.shareable_hash,
            "layout_uuid": str(self.players_config.get_own_uuid()),
            "optional_modifications": {
                "can_send_fish_to_space": self.configuration.can_send_fish_to_space,
                "stronger_solar": self.configuration.stronger_solar,
                "productivity_everywhere": self.configuration.productivity_everywhere,
                "single_item_freebie": self.configuration.single_item_freebie,
                "strict_multiplayer_freebie": self.configuration.strict_multiplayer_freebie,
            },
            "technologies": technologies,
            "recipes": self._create_recipe_patches(),
            "starting_tech": [
                # TODO: care about amount decently
                resource.short_name
                for resource, amount in self.patches.starting_resources().as_resource_gain()
                if amount > 0
            ],
        }

        return result

    def _create_recipe_patches(self) -> list[cfg.ConfigurationRecipesItem]:
        result = []

        game_specific: FactorioGameSpecific = self.patches.game_specific
        recipes_raw = data_parser.load_recipes_raw()

        for recipe_name, modification in game_specific["recipes"].items():
            recipe = recipes_raw[recipe_name]
            category = recipes.determine_recipe_category(
                recipe_name, recipe.get("category", "crafting"), modification["ingredients"]
            )

            result.append(
                {
                    "recipe_name": recipe_name,
                    "category": category,
                    "ingredients": [
                        {"name": item_name, "amount": amount, "type": "fluid" if item_is_fluid(item_name) else "item"}
                        for item_name, amount in modification["ingredients"].items()
                    ],
                }
            )

        return result
