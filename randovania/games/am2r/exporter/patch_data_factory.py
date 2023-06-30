from random import Random

from randovania.exporter import pickup_exporter
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator


class AM2RItemInfo:
    def __init__(self, sprite_name: str, sprite_speed: int, text_header: str, text_desc: str):
        self.sprite_name = sprite_name
        self.sprite_speed = sprite_speed
        self.text_header = text_header
        self.text_desc = text_desc


def _create_item_info_dict():
    info = {}
    def_speed = 0.2
    info["Missile Expansion"] = AM2RItemInfo("sItemMissile", def_speed, "Got Missile Tank",
                                             "Missile capacity increased by [capacity]")
    info["Missiles"] = info["Missile Expansion"]
    info["Super Missile Expansion"] = AM2RItemInfo("sItemSuperMissile", def_speed, "Got Super Missile Tank",
                                                   "Super Missile capacity increased by [capacity].")
    info["Super Missiles"] = info["Super Missile Expansion"]
    info["Power Bomb Expansion"] = AM2RItemInfo("sItemPowerBomb", def_speed, "Got Power Bomb Tank",
                                                "Power Bomb capacity increased by [capacity].")
    info["Power Bombs"] = info["Power Bomb Expansion"]
    info["Energy Tank"] = AM2RItemInfo("sItemEnergyTank", def_speed, "Got Energy Tank",
                                       "Suit Energy increased by [energy] units")
    # TODO: use correct speed here, they are not 0.2
    info["Missile Launcher"] = AM2RItemInfo("sItemMissileLauncher", def_speed, "Got Missile Launcher",
                                            "Missiles can now be fired. Missile capacity increased by [capacity]")

    info["Super Missile Launcher"] = AM2RItemInfo("sItemSMissileLauncher", def_speed, "Got SuperMissile Launcher",
                                                  "Super Missiles can now be fired. "
                                                  "Super Missile capacity increased by [capacity]")
    info["Power Bomb Launcher"] = AM2RItemInfo("sItemPBombLauncher", def_speed, "Got Power Bomb Launcher",
                                               "Power Bomb can now be fired. "
                                               "Power Bomb capacity increased by [capacity]")
    info["Metroid DNA"] = AM2RItemInfo("sItemDNA", 0.28, "Metroid DNA acquired",
                                       "Collect all DNA in order to reach the Queen")
    for i in range(1, 47):
        info[f'Metroid DNA {i}'] = info["Metroid DNA"]

    info["Bombs"] = AM2RItemInfo("sItemBomb", def_speed, "Bombs acquired", "Press | in Morph Ball to deploy")
    info["Power Grip"] = AM2RItemInfo("sItemPowergrip", def_speed, "Power Grip acquired", "You can now grab ledges")
    info["Spider Ball"] = AM2RItemInfo("sItemSpiderBall", def_speed, "Spider Ball acquired",
                                       "Press or hold | in Morph Ball mode to climb walls")
    info["Spring Ball"] = AM2RItemInfo("sItemJumpBall", def_speed, "Spring Ball acquired", "Press | in Morph Ball mode")
    info["Screw Attack"] = AM2RItemInfo("sItemScrewAttack", def_speed, "Screw Attack acquired",
                                        "Jump into enemies to inflict massive damage")
    info["Varia Suit"] = AM2RItemInfo("sItemVariaSuit", def_speed, "Varia Suit acquired", "Reduces Damage taken by 50%")
    info["Space Jump"] = AM2RItemInfo("sItemSpaceJump", def_speed, "Space Jump acquired",
                                      "Jump continuously in the air")
    info["Speed Booster"] = AM2RItemInfo("sItemSpeedBooster", 0.5, "Speed Booster acquired",
                                         "Run continuously to begin Speed Boosting")
    info["Hi-Jump"] = AM2RItemInfo("sItemHijump", def_speed, "Hi-Jump acquired", "Maximum Jump height increased")
    info["Gravity Suit"] = AM2RItemInfo("sItemGravitySuit", def_speed, "Gravity Suit acquired",
                                        "Liquid friction eliminated - Improved Defense")
    info["Charge Beam"] = AM2RItemInfo("sItemChargeBeam", def_speed, "Charge Beam acquired",
                                       "Hold | to charge your beam")
    info["Ice Beam"] = AM2RItemInfo("sItemIceBeam", def_speed, "Ice Beam acquired",
                                    "Instantly freeze enemies. Extra damage")
    info["Wave Beam"] = AM2RItemInfo("sItemWaveBeam", def_speed, "Wave Beam acquired",
                                     "Beams can now go through solid objects")
    info["Spazer Beam"] = AM2RItemInfo("sItemSpazerBeam", def_speed, "Spazer Beam acquired",
                                       "Beams now have a wider range")
    info["Plasma Beam"] = AM2RItemInfo("sItemPlasmaBeam", def_speed, "Plasma Beam acquired", "Beams can pierce enemies")
    info["Morph Ball"] = AM2RItemInfo("sItemMorphBall", 0.1666, "Morph Ball acquired", "Roll around in a ball")
    info["Nothing"] = AM2RItemInfo("sItemUnknown", 0.3333, "Nothing acquired", "A useless item")
    info["EnergyTransferModule"] = info["Nothing"]
    info["Unknown Item"] = AM2RItemInfo("sItemUnknown", 0.3333, "Got Unknown Item", "A mysterious item")

    return info


class AM2RPatchDataFactory(BasePatchDataFactory):
    _EASTER_EGG_SHINY_MISSILE = 1024

    def _create_pickups_dict(self, pickup_list, item_info, rng: Random):
        pickup_map_dict = {}
        for pickup in pickup_list:
            quantity = pickup.conditional_resources[0].resources[0][1]
            object_name = self.game.region_list.node_from_pickup_index(pickup.index).extra["object_name"]
            pickup_map_dict[object_name] = {
                "sprite_details": {
                    "name": item_info[pickup.model.name].sprite_name,
                    "speed": item_info[pickup.model.name].sprite_speed
                },
                "item_effect": pickup.original_pickup.name,
                "quantity": quantity,
                "text": {
                    "header": item_info[pickup.model.name].text_header,
                    "description": item_info[pickup.name].text_desc.replace("[capacity]", str(quantity)).replace(
                        "[energy]", str(self.configuration.energy_per_tank)
                    )
                }
            }
            if (pickup_map_dict[object_name]["item_effect"] == "Missile Expansion" and
                    pickup_map_dict[object_name]["sprite_details"]["name"] == "sItemMissile" and
                    pickup_map_dict[object_name]["text"]["header"] == "Got Missile Tank" and not pickup.other_player and
                    rng.randint(0, self._EASTER_EGG_SHINY_MISSILE) == 0):
                pickup_map_dict[object_name]["sprite_details"]["name"] = "sItemShinyMissile"
                pickup_map_dict[object_name]["text"]["header"] = "Got Shiny Missile Tank"

        return pickup_map_dict

    def _create_room_dict(self):
        room_name_dict = {}
        for region in self.game.region_list.regions:
            for area in region.areas:
                room_name_dict[area.extra["map_name"]] = {
                    "display_name": area.name
                }
        return room_name_dict

    def _create_starting_items_dict(self):
        start = {}
        starting_resources = self.patches.starting_resources()
        for resource, quantity in starting_resources.as_resource_gain():
            start[resource.short_name] = quantity
        return start

    def _create_starting_location(self):
        return {
            "save_room": self.game.region_list.node_by_identifier(self.patches.starting_location).extra["save_room"]
        }

    def _create_hash_dict(self):
        return {
            "word_hash": self.description.shareable_word_hash,
            "hash": self.description.shareable_hash
        }

    def _create_game_patches(self):
        game_patches = {
            "septogg_helpers": self.patches.configuration.septogg_helpers,
            "change_level_design": self.patches.configuration.change_level_design,
            "respawn_bomb_blocks": self.patches.configuration.respawn_bomb_blocks,
            "skip_cutscenes": self.patches.configuration.skip_cutscenes,
            "energy_per_tank": self.patches.configuration.energy_per_tank,
            "remove_grave_grotto_blocks": self.patches.configuration.remove_grave_grotto_blocks,
            "fusion_mode": self.patches.configuration.fusion_mode,
        }
        for item, state in self.patches.configuration.ammo_pickup_configuration.pickups_state.items():
            launcher_text = ""
            if item.name == "Missile Expansion":
                launcher_text = "require_missile_launcher"
            elif item.name == "Super Missile Expansion":
                launcher_text = "require_super_launcher"
            elif item.name == "Power Bomb Expansion":
                launcher_text = "require_pb_launcher"

            if not launcher_text:
                continue

            game_patches[launcher_text] = state.requires_main_item
        return game_patches

    def _create_door_locks(self):
        locks = {}
        for node, weakness in self.patches.all_dock_weaknesses():
            locks[node.extra["instance_id"]] = {
                "lock": weakness.long_name
            }
        return locks

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def create_data(self) -> dict:
        db = self.game

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(db.resource_database),
                                      self.players_config.player_index)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(pickup_exporter.GenericAcquiredMemo(), self.players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        item_info = _create_item_info_dict()

        return {
            "configuration_identifier": self._create_hash_dict(),
            "starting_items": self._create_starting_items_dict(),
            "starting_location": self._create_starting_location(),
            "pickups": self._create_pickups_dict(pickup_list, item_info, self.rng),
            "rooms": self._create_room_dict(),
            "game_patches": self._create_game_patches(),
            "door_locks": self._create_door_locks()
            # TODO: add cosmetic field and decide what to even put in there.
            # TODO: add hints field
        }
