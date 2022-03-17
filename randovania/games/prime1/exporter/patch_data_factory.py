import typing
from random import Random
from typing import List, Union

import randovania
from randovania.exporter import pickup_exporter, item_names
from randovania.exporter.hints import guaranteed_item_hint, credits_spoiler
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.hint_namer import PrimeHintNamer
from randovania.games.prime1.layout.hint_configuration import ArtifactHintMode
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime1.patcher import prime1_elevators, prime_items
from randovania.generator.item_pool import pickup_creator

_EASTER_EGG_SHINY_MISSILE = 1024

_STARTING_ITEM_NAME_TO_INDEX = {
    "powerBeam": "Power",
    "ice": "Ice",
    "wave": "Wave",
    "plasma": "Plasma",
    "missiles": "Missile",
    "scanVisor": "Scan",
    "bombs": "Bombs",
    "powerBombs": "PowerBomb",
    "flamethrower": "Flamethrower",
    "thermalVisor": "Thermal",
    "charge": "Charge",
    "superMissile": "Supers",
    "grapple": "Grapple",
    "xray": "X-Ray",
    "iceSpreader": "IceSpreader",
    "spaceJump": "SpaceJump",
    "morphBall": "MorphBall",
    "combatVisor": "Combat",
    "boostBall": "Boost",
    "spiderBall": "Spider",
    "gravitySuit": "GravitySuit",
    "variaSuit": "VariaSuit",
    "phazonSuit": "PhazonSuit",
    "energyTanks": "EnergyTank",
    "wavebuster": "Wavebuster"
}

# "Power Suit": "PowerSuit",
# "Combat Visor": "Combat",
# "Unknown Item 1": "Unknown1",
# "Health Refill": "HealthRefill",
# "Unknown Item 2": "Unknown2",

_MODEL_MAPPING = {
    (RandovaniaGame.METROID_PRIME_ECHOES, "CombatVisor INCOMPLETE"): "Combat Visor",
    (RandovaniaGame.METROID_PRIME_ECHOES, "ChargeBeam INCOMPLETE"): "Charge Beam",
    (RandovaniaGame.METROID_PRIME_ECHOES, "SuperMissile"): "Super Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "ScanVisor INCOMPLETE"): "Scan Visor",
    (RandovaniaGame.METROID_PRIME_ECHOES, "VariaSuit INCOMPLETE"): "Varia Suit",
    (RandovaniaGame.METROID_PRIME_ECHOES, "DarkSuit"): "Varia Suit",
    (RandovaniaGame.METROID_PRIME_ECHOES, "LightSuit"): "Varia Suit",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MorphBall INCOMPLETE"): "Morph Ball",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MorphBallBomb"): "Morph Ball Bomb",
    (RandovaniaGame.METROID_PRIME_ECHOES, "BoostBall"): "Boost Ball",
    (RandovaniaGame.METROID_PRIME_ECHOES, "SpiderBall"): "Spider Ball",
    (RandovaniaGame.METROID_PRIME_ECHOES, "PowerBomb"): "Power Bomb",
    (RandovaniaGame.METROID_PRIME_ECHOES, "PowerBombExpansion"): "Power Bomb Expansion",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MissileExpansion"): "Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MissileExpansionPrime1"): "Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "MissileLauncher"): "Missile",
    (RandovaniaGame.METROID_PRIME_ECHOES, "GrappleBeam"): "Grapple Beam",
    (RandovaniaGame.METROID_PRIME_ECHOES, "SpaceJumpBoots"): "Space Jump Boots",
    (RandovaniaGame.METROID_PRIME_ECHOES, "EnergyTank"): "Energy Tank",
}

# The following locations have cutscenes that weren't removed
_LOCATIONS_WITH_MODAL_ALERT = {
    63,  # Artifact Temple
    23,  # Watery Hall (Charge Beam)
    50,  # Research Core
}

# Show a popup on collection if two or more is for another player.
# The location to the right is considered for the count, but it can't show a popup.
_LOCATIONS_GROUPED_TOGETHER = [
    ({0, 1, 2, 3}, None),  # Main Plaza
    ({5, 6, 7}, None),  # Ruined Shrine (all 3)
    ({94}, 97),  # Warrior shrine -> Fiery Shores Tunnel
    ({55}, 54),  # Gravity Chamber: Upper -> Lower
    ({19, 17}, None),  # Hive Totem + Transport Access North
    ({59}, 58),  # Alcove -> Landing Site
    ({62, 65}, None),  # Root Cave + Arbor Chamber
    ({15, 16}, None),  # Ruined Gallery
    ({52, 53}, None),  # Research Lab Aether
]

_VANILLA_MAZE_SEEDS = [
    0x38BF30F8,
    0x0FC40F11,
    0x5B2524E8,
    0x082F7F85,
    0x106C3FBD,
    0x66B00296,
    0x347C3A0A,
    0x3C086FA7,
    0x31BD576E,
    0x74AE54B3,
    0x6A6F2F00,
    0x238B2D8A,
    0x1630586B,
    0x43601735,
    0x4F16036B,
    0x680C3158,
    0x2F423547,
    0x4B9E6269,
    0x72CC6119,
    0x6CE42754,
    0x4B0A6564,
    0x00C171D8,
    0x2D6A3AE9,
    0x7E016A7B,
    0x29987167,
    0x4BFC2AC6,
    0x47B543C7,
    0x66183D28,
    0x3CB153A3,
    0x752D5B64,
    0x2786601D,
    0x0D3D1064,
    0x33787808,
    0x1F87495F,
    0x722048D2,
    0x0A67605C,
    0x090A4E09,
    0x5C7D5569,
    0x39C92B9D,
    0x1A474EFD,
    0x010C387A,
    0x066A6458,
    0x17220ABC,
    0x5842591E,
    0x75ED3574,
    0x39072AE3,
    0x7F9F1781,
    0x769E5C34,
    0x09787BDE,
    0x356F3315,
    0x37E947F1,
    0x0E7B45CB,
    0x023D4B64,
    0x60A14070,
    0x1FB10E09,
    0x07543FD0,
    0x02F81E3A,
    0x71893A83,
    0x07CF1F6A,
    0x3D627E4C,
    0x591F5317,
    0x0AD47683,
    0x038D1FBF,
    0x69DB0B97,
    0x7CEC0A6F,
    0x42B96A41,
    0x50211FE3,
    0x2A7F192F,
    0x1440516A,
    0x03A47996,
    0x6FA755C4,
    0x67B91A15,
    0x656F23D0,
    0x0708063D,
    0x54CF00FC,
    0x59B15B17,
    0x6D412671,
    0x073A4331,
    0x0FA0705D,
    0x1B281BC2,
    0x2E1D7C70,
    0x1CFF58B0,
    0x19A67C93,
    0x287A60E4,
    0x55611C92,
    0x2C7231E2,
    0x5B0875D0,
    0x55EB3C4A,
    0x2DBE5953,
    0x79B16760,
    0x30596C5F,
    0x5D387296,
    0x0E1A0975,
    0x1A787A78,
    0x20C458DD,
    0x731969DD,
    0x35894C3E,
    0x78E35925,
    0x67AA1994,
    0x05027F2F,
    0x47583F7E,
    0x166E28DA,
    0x4717421D,
    0x67EC1B2C,
    0x566764C4,
    0x0D3A6AAE,
    0x56E137D1,
    0x61EF4153,
    0x60001202,
    0x669F48F3,
    0x48D946CE,
    0x59F171A5,
    0x70946C60,
    0x12D01540,
    0x3FB628DF,
    0x0C0173FC,
    0x72361CDC,
    0x6C2634BF,
    0x08874C85,
    0x1298390C,
    0x328C250F,
    0x2EED3A89,
    0x736447D2,
    0x55F47926,
    0x2DBB4361,
    0x09877544,
    0x77EC336D,
    0x52995CF2,
    0x38C06A2D,
    0x5F3165AA,
    0x31F45D9A,
    0x61913722,
    0x0D26132D,
    0x1F7406FC,
    0x4C175BA3,
    0x160B1794,
    0x61344251,
    0x523144CC,
    0x0276333F,
    0x70F13EC7,
    0x7C8A595F,
    0x7AFD143C,
    0x2E087991,
    0x1F7B7D72,
    0x562F2423,
    0x771800EE,
    0x1AC63593,
    0x44756DD7,
    0x585641A3,
    0x71F6779C,
    0x54736B1E,
    0x388E5D58,
    0x5CF23936,
    0x281962C6,
    0x69E448AC,
    0x67DF678C,
    0x7FDB5CF6,
    0x6B6257BA,
    0x702D5690,
    0x22C75853,
    0x18EE6F4A,
    0x74CB5236,
    0x6AE20180,
    0x5E5E1BEC,
    0x6C1F0C0D,
    0x4E8743A5,
    0x30833062,
    0x0A2B1E68,
    0x5D3D6E7C,
    0x4EBA52A2,
    0x388C1C6E,
    0x777678DA,
    0x6BB169D8,
    0x25CF20E0,
    0x4E9265EC,
    0x58D427F5,
    0x589550AC,
    0x7D9718DC,
    0x14EF6BB8,
    0x4F1337C5,
    0x36141ACA,
    0x6F4E58C5,
    0x55D9660A,
    0x011F018B,
    0x2A1F0984,
    0x55B82D4B,
    0x364D753E,
    0x0B484526,
    0x33707DAA,
    0x66720A01,
    0x13634FE1,
    0x7ED97457,
    0x51722B26,
    0x2C3A0748,
    0x60D45C93,
    0x09BF0D5E,
    0x46EE378A,
    0x77D43C93,
    0x58884536,
    0x7E802AA6,
    0x511E391D,
    0x67277255,
    0x2FDC66B3,
    0x44B857B2,
    0x7F541C10,
    0x19317C01,
    0x5302582F,
    0x0F343EDF,
    0x0EE61243,
    0x5F2D4814,
    0x0CAF3DFD,
    0x673F0C00,
    0x72647713,
    0x397B17B0,
    0x3BA6769E,
    0x4E842ED1,
    0x0E785543,
    0x33A8004E,
    0x72EC3566,
    0x2A196221,
    0x366E7E4F,
    0x0BC138FB,
    0x6EA80B43,
    0x7B4F68C9,
    0x6314373D,
    0x2BAA0E3F,
    0x3FEF54B7,
    0x651C5C0E,
    0x0264479F,
    0x5A075DE3,
    0x730C3562,
    0x52DC5688,
    0x23B86795,
    0x4CF07417,
    0x415A45C0,
    0x54884C1C,
    0x665D4B51,
    0x013178EF,
    0x5F697FBC,
    0x3D164F19,
    0x1A061828,
    0x50E0794E,
    0x2DC2628D,
    0x1A8E01F0,
    0x3BE07F32,
    0x71942C45,
    0x02BA124A,
    0x05CF2065,
    0x2D7463FD,
    0x437366FB,
    0x6D061234,
    0x45F43160,
    0x4A8D57E2,
    0x02497261,
    0x08F65FED,
    0x31550CB1,
    0x34CA19C4,
    0x23DB0EAA,
    0x0DDB507A,
    0x7EB52915,
    0x3C6B0449,
    0x7F891F26,
    0x6DD32122,
    0x7AD0394B,
    0x3B7A7498,
    0x5D0D61F0,
    0x1C0203E0,
    0x4F6E24F5,
    0x170B3855,
    0x4A7A7C20,
    0x417A1F46,
    0x7283315D,
    0x7821267D,
    0x0B1842E2,
    0x5AD87022,
    0x41E51EFB,
    0x62BA23D3,
    0x424B3FF2,
    0x6B14153F,
    0x3D6F4A50,
    0x766A32CC,
    0x35351B42,
    0x38184E67,
    0x09E46D7C,
    0x2A934B8F,
    0x0519782B,
    0x161A2713,
    0x2014465D,
    0x2CEE5510,
    0x613C5D58,
    0x7E3116D4,
    0x52D87611,
    0x1BF92217,
    0x34296443,
    0x4DC3757A,
    0x70747F81,
    0x43F12A3C,
    0x156A2251,
    0x1DD054D7,
    0x42E72CE0,
]

def prime1_pickup_details_to_patcher(detail: pickup_exporter.ExportedPickupDetails,
                                     modal_hud_override: bool,
                                     rng: Random) -> dict:
    model = detail.model.as_json

    scan_text = detail.scan_text
    hud_text = detail.hud_text[0]
    pickup_type = "Nothing"
    count = 0

    for resource, quantity in detail.conditional_resources[0].resources:
        if resource.extra["item_id"] >= 1000:
            continue
        pickup_type = resource.long_name
        count = quantity
        break

    if (model["name"] == "Missile" and not detail.other_player
            and "Missile Expansion" in hud_text
            and rng.randint(0, _EASTER_EGG_SHINY_MISSILE) == 0):
        model["name"] = "Shiny Missile"
        hud_text = hud_text.replace("Missile Expansion", "Shiny Missile Expansion")
        scan_text = scan_text.replace("Missile Expansion", "Shiny Missile Expansion")

    result = {
        "type": pickup_type,
        "model": model,
        "scanText": scan_text,
        "hudmemoText": hud_text,
        "currIncrease": count,
        "maxIncrease": count,
        "respawn": False
    }
    if modal_hud_override:
        result["modalHudmemo"] = True

    return result


def _create_locations_with_modal_hud_memo(pickups: List[pickup_exporter.ExportedPickupDetails]) -> typing.Set[int]:
    result = set()

    for index in _LOCATIONS_WITH_MODAL_ALERT:
        if pickups[index].other_player:
            result.add(index)

    for indices, extra in _LOCATIONS_GROUPED_TOGETHER:
        num_other = sum(pickups[i].other_player for i in indices)
        if extra is not None:
            num_other += pickups[extra].other_player

        if num_other > 1:
            for index in indices:
                if pickups[index].other_player:
                    result.add(index)

    return result


def _starting_items_value_for(resource_database: ResourceDatabase,
                              starting_items: CurrentResources, index: str) -> Union[bool, int]:
    item = resource_database.get_item(index)
    value = starting_items.get(item, 0)
    if item.max_capacity > 1:
        return value
    else:
        return value > 0


def _name_for_location(world_list: WorldList, location: AreaIdentifier) -> str:
    loc = location.as_tuple
    if loc in prime1_elevators.RANDOM_PRIME_CUSTOM_NAMES and loc != ("Frigate Orpheon", "Exterior Docking Hangar"):
        return prime1_elevators.RANDOM_PRIME_CUSTOM_NAMES[loc]
    else:
        return world_list.area_name(world_list.area_by_area_location(location), separator=":")


class PrimePatchDataFactory(BasePatchDataFactory):
    cosmetic_patches: PrimeCosmeticPatches
    configuration: PrimeConfiguration

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME

    def get_default_game_options(self):
        cosmetic_patches = self.cosmetic_patches
        return {
            "screenBrightness": cosmetic_patches.user_preferences.screen_brightness,
            "screenOffsetX": cosmetic_patches.user_preferences.screen_x_offset,
            "screenOffsety": cosmetic_patches.user_preferences.screen_y_offset,
            "screenStretch": cosmetic_patches.user_preferences.screen_stretch,
            "soundMode": cosmetic_patches.user_preferences.sound_mode,
            "sfxVolume": cosmetic_patches.user_preferences.sfx_volume,
            "musicVolume": cosmetic_patches.user_preferences.music_volume,
            "visorOpacity": cosmetic_patches.user_preferences.hud_alpha,
            "helmetOpacity": cosmetic_patches.user_preferences.helmet_alpha,
            "hudLag": cosmetic_patches.user_preferences.hud_lag,
            "reverseYAxis": cosmetic_patches.user_preferences.invert_y_axis,
            "rumble": cosmetic_patches.user_preferences.rumble,
            "swapBeamControls": cosmetic_patches.user_preferences.swap_beam_controls,
        }

    def create_data(self) -> dict:
        db = self.game
        namer = PrimeHintNamer(self.description.all_patches, self.players_config)

        scan_visor = self.game.resource_database.get_item_by_name("Scan Visor")
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
        modal_hud_override = _create_locations_with_modal_hud_memo(pickup_list)

        world_data = {}

        for world in db.world_list.worlds:
            if world.name == "End of Game":
                continue

            world_data[world.name] = {
                "transports": {},
                "rooms": {}
            }
            for area in world.areas:
                pickup_indices = sorted(node.pickup_index for node in area.nodes if isinstance(node, PickupNode))
                if pickup_indices:
                    world_data[world.name]["rooms"][area.name] = {
                        "pickups": [
                            prime1_pickup_details_to_patcher(pickup_list[index.index],
                                                             index.index in modal_hud_override,
                                                             self.rng)
                            for index in pickup_indices
                        ],
                    }

                for node in area.nodes:
                    if not isinstance(node, TeleporterNode) or not node.editable:
                        continue

                    identifier = db.world_list.identifier_for_node(node)
                    target = _name_for_location(db.world_list, self.patches.elevator_connection[identifier])

                    source_name = prime1_elevators.RANDOM_PRIME_CUSTOM_NAMES[(
                        identifier.area_location.world_name,
                        identifier.area_location.area_name,
                    )]
                    world_data[world.name]["transports"][source_name] = target

        starting_memo = None
        extra_starting = item_names.additional_starting_items(self.configuration, db.resource_database,
                                                              self.patches.starting_items)
        if extra_starting:
            starting_memo = ", ".join(extra_starting)

        if self.cosmetic_patches.open_map and self.configuration.elevators.is_vanilla:
            map_default_state = "visible"
        else:
            map_default_state = "default"

        credits_string = credits_spoiler.prime_trilogy_credits(
            self.configuration.major_items_configuration,
            self.description.all_patches,
            self.players_config,
            namer,
            "&push;&font=C29C51F1;&main-color=#89D6FF;Major Item Locations&pop;",
            "&push;&font=C29C51F1;&main-color=#33ffd6;{}&pop;",
        )

        artifacts = [
            db.resource_database.get_item(index)
            for index in prime_items.ARTIFACT_ITEMS
        ]
        hint_config = self.configuration.hints
        if hint_config.artifacts == ArtifactHintMode.DISABLED:
            resulting_hints = {art: "{} is lost somewhere on Tallon IV.".format(art.long_name) for art in artifacts}
        else:
            resulting_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config, namer,
                hint_config.artifacts == ArtifactHintMode.HIDE_AREA,
                [db.resource_database.get_item(index) for index in prime_items.ARTIFACT_ITEMS],
                True,
            )

        # Tweaks
        ctwk_config = {}
        if self.configuration.small_samus:
            ctwk_config["playerSize"] = 0.3
            ctwk_config["morphBallSize"] = 0.3
            ctwk_config["easyLavaEscape"] = True

        if self.cosmetic_patches.use_hud_color:
            ctwk_config["hudColor"] = [
                self.cosmetic_patches.hud_color[0] / 255,
                self.cosmetic_patches.hud_color[1] / 255,
                self.cosmetic_patches.hud_color[2] / 255
            ]

        SUIT_ATTRIBUTES = ["powerDeg", "variaDeg", "gravityDeg", "phazonDeg"]
        suit_colors = {}
        for attribute, hue_rotation in zip(SUIT_ATTRIBUTES, self.cosmetic_patches.suit_color_rotations):
            if hue_rotation != 0:
                suit_colors[attribute] = hue_rotation

        starting_room = _name_for_location(db.world_list, self.patches.starting_location)

        starting_items = {
            name: _starting_items_value_for(db.resource_database, self.patches.starting_items, index)
            for name, index in _STARTING_ITEM_NAME_TO_INDEX.items()
        }

        if self.configuration.deterministic_idrone:
            idrone_config = {
                "eyeWaitInitialRandomTime": 0.0,
                "eyeWaitRandomTime": 0.0,
                "eyeStayUpRandomTime": 0.0,
                "resetContraptionRandomTime": 0.0,
                # ~~~ Justification for Divide by 2 ~~~
                # These Timer RNG values are normally re-rolled inbetween each of the 4 phases,
                # turning the zoid fight duration probability into a bell curve. With /2 we manipulate
                # the (now linear) probability characteristic to more often generate "average zoid fights"
                # while erring on the side of faster.
                "eyeWaitInitialMinimumTime": 8.0 + self.rng.random() * 5.0 / 2.0,
                "eyeWaitMinimumTime": 15.0 + self.rng.random() * 10.0 / 2.0,
                "eyeStayUpMinimumTime": 8.0 + self.rng.random() * 3.0 / 2.0,
                "resetContraptionMinimumTime": 3.0 + self.rng.random() * 3.0 / 2.0,
            }
        else:
            idrone_config = None
        
        if self.configuration.deterministic_maze:
            maze_seeds = [self.rng.choice(_VANILLA_MAZE_SEEDS)]
        else:
            maze_seeds = None

        seed = self.description.get_seed_for_player(self.players_config.player_index)

        return {
            "seed": seed,
            "preferences": {
                "defaultGameOptions": self.get_default_game_options(),
                "qolGameBreaking": self.configuration.qol_game_breaking,
                "qolCosmetic": self.cosmetic_patches.qol_cosmetic,
                "qolPickupScans": self.configuration.qol_pickup_scans,
                "qolCutscenes": self.configuration.qol_cutscenes.value,

                "mapDefaultState": map_default_state,
                "artifactHintBehavior": None,
                "automaticCrashScreen": True,
                "trilogyDiscPath": None,
                "quickplay": False,
                "quiet": False,
                "suitColors": suit_colors,
            },
            "gameConfig": {
                "shufflePickupPosition": self.configuration.shuffle_item_pos,
                "shufflePickupPosAllRooms": self.configuration.items_every_room,
                "startingRoom": starting_room,
                "startingMemo": starting_memo,
                "warpToStart": self.configuration.warp_to_start,
                "springBall": self.configuration.spring_ball,
                "incineratorDroneConfig": idrone_config,
                "mazeSeeds": maze_seeds,
                "nonvariaHeatDamage": self.configuration.heat_protection_only_varia,
                "staggeredSuitDamage": self.configuration.progressive_damage_reduction,
                "heatDamagePerSec": self.configuration.heat_damage,
                "autoEnabledElevators": self.patches.starting_items.get(scan_visor, 0) == 0,
                "multiworldDolPatches": True,

                "disableItemLoss": True,  # Item Loss in Frigate
                "startingItems": starting_items,

                "etankCapacity": self.configuration.energy_per_tank,
                "itemMaxCapacity": {
                    "Energy Tank": db.resource_database.get_item("EnergyTank").max_capacity,
                    "Power Bomb": db.resource_database.get_item("PowerBomb").max_capacity,
                    "Missile": db.resource_database.get_item("Missile").max_capacity,
                    "Unknown Item 1": db.resource_database.multiworld_magic_item.max_capacity,
                },

                "mainPlazaDoor": self.configuration.main_plaza_door,
                "backwardsFrigate": self.configuration.backwards_frigate,
                "backwardsLabs": self.configuration.backwards_labs,
                "backwardsUpperMines": self.configuration.backwards_upper_mines,
                "backwardsLowerMines": self.configuration.backwards_lower_mines,
                "phazonEliteWithoutDynamo": self.configuration.phazon_elite_without_dynamo,

                "gameBanner": {
                    "gameName": "Metroid Prime: Randomizer",
                    "gameNameFull": "Metroid Prime: Randomizer - {}".format(self.description.shareable_hash),
                    "description": "Seed Hash: {}".format(self.description.shareable_word_hash),
                },
                "mainMenuMessage": "Randovania v{}\n{}".format(
                    randovania.VERSION,
                    self.description.shareable_word_hash
                ),

                "creditsString": credits_string,
                "artifactHints": {
                    artifact.long_name: text
                    for artifact, text in resulting_hints.items()
                },
                "artifactTempleLayerOverrides": {
                    artifact.long_name: self.patches.starting_items.get(artifact, 0) == 0
                    for artifact in artifacts
                },
            },
            "tweaks": ctwk_config,
            "levelData": world_data,
            "hasSpoiler": self.description.has_spoiler,

            # TODO
            # "externAssetsDir": path_to_converted_assets,
        }
