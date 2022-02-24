import dataclasses

from randovania.exporter import pickup_exporter
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration
from randovania.games.super_metroid.layout.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches, MusicMode
from randovania.generator.item_pool import pickup_creator

_multiplier_for_item = {
    "Energy Tank": 100, "Reserve Tank": 100,
}

_mapping = {
    "Missile": "Missile Expansion",
    "Super Missile": "Super Missile Expansion",
    "Power Bombs": "Power Bomb Expansion",

    "Nothing": "No Item",
}

_effect = {
    "Energy Tank": "Get Energy Tank",
    "Missile Expansion": "Get Missile Expansion",
    "Super Missile Expansion": "Get Super Missile Expansion",
    "Power Bomb Expansion": "Get Power Bomb Expansion",
    "Grapple Beam": "Get Grapple Beam",
    "X-Ray Scope": "Get X-Ray Scope",
    "Varia Suit": "Get Varia Suit",
    "Spring Ball": "Get Spring Ball",
    "Morph Ball": "Get Morph Ball",
    "Screw Attack": "Get Screw Attack",
    "Hi-Jump Boots": "Get Hi-Jump Boots",
    "Space Jump": "Get Space Jump",
    "Speed Booster": "Get Speed Booster",
    "Charge Beam": "Get Charge Beam",
    "Ice Beam": "Get Ice Beam",
    "Wave Beam": "Get Wave Beam",
    "Spazer Beam": "Get Spazer Beam",
    "Plasma Beam": "Get Plasma Beam",
    "Morph Ball Bombs": "Get Morph Ball Bombs",
    "Reserve Tank": "Get Reserve Tank",
    "Gravity Suit": "Get Gravity Suit",
    "No Item": "No Effect",
}


def sm_pickup_details_to_patcher(detail: pickup_exporter.ExportedPickupDetails
                                 ) -> dict:
    if detail.model.game == RandovaniaGame.SUPER_METROID:
        model_name = detail.model.name
    else:
        model_name = "Nothing"

    scan_text = detail.scan_text
    hud_text = detail.hud_text[0]
    pickup_type = "Nothing"
    count = 0

    for resource, quantity in detail.conditional_resources[0].resources:
        if resource.resource_type == ResourceType.ITEM and resource.extra["item_id"] >= 1000:
            continue
        pickup_type = resource.long_name
        count = quantity
        break

    count *= _multiplier_for_item.get(pickup_type, 1)

    item_name = _mapping.get(pickup_type, pickup_type)

    result = {
        "item_name": item_name,
        "quantity_given": count,
        "pickup_effect": _effect[item_name],
        "pickup_index": detail.index.index,
        "native_sprite_name": item_name,
        "owner_name": None,
    }

    return result


def sm_starting_items_to_patcher(item: ItemResourceInfo, quantity: int) -> dict:
    item_name = _mapping.get(item.long_name, item.long_name)
    quantity *= _multiplier_for_item.get(item_name, 1)
    result = {
        "item_name": item_name,
        "quantity_given": quantity,
        "pickup_effect": _effect[item_name],
    }
    return result


class SuperMetroidPatchDataFactory(BasePatchDataFactory):
    cosmetic_patches: SuperMetroidCosmeticPatches
    configuration: SuperMetroidConfiguration

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.SUPER_METROID

    def create_data(self) -> dict:
        db = self.game
        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(db.resource_database),
                                      self.players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            db.world_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(db, pickup_exporter.GenericAcquiredMemo(),
                                                            self.players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        gameplay_patch_list = [field.name for field in dataclasses.fields(self.configuration.patches)]
        cosmetic_patch_list = [field.name for field in dataclasses.fields(self.cosmetic_patches)]

        cosmetic_patch_list.remove("music")
        specific_patches = {}

        for patch in gameplay_patch_list:
            specific_patches[patch] = getattr(self.configuration.patches, patch)
        for patch in cosmetic_patch_list:
            specific_patches[patch] = getattr(self.cosmetic_patches, patch)
        if self.cosmetic_patches.music != MusicMode.VANILLA:
            specific_patches[self.cosmetic_patches.music.value] = True

        starting_point = self.patches.starting_location

        starting_area = db.world_list.area_by_area_location(starting_point)

        starting_save_index = starting_area.extra["save_index"]

        starting_location_info = {
            "starting_region": starting_point.world_name,
            "starting_save_station_index": starting_save_index,
        }

        return {
            "pickups": [
                sm_pickup_details_to_patcher(detail)
                for detail in pickup_list
            ],
            "starting_items": [
                sm_starting_items_to_patcher(item, qty)
                for item, qty in self.patches.starting_items.items()
            ],
            "specific_patches": specific_patches,
            "starting_conditions": starting_location_info
        }
