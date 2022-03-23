from pydoc import doc
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
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.hint_namer import PrimeHintNamer
from randovania.games.prime1.layout.hint_configuration import ArtifactHintMode
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration, RoomRandoMode
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime1.patcher import prime1_elevators, prime_items
from randovania.generator.item_pool import pickup_creator
from randovania.games.prime1.exporter.vanilla_maze_seeds import VANILLA_MAZE_SEEDS

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

_DOCKS_TO_SKIP = [
    ("Frigate Orpheon", "Air Lock", 1),
    ("Frigate Orpheon", "Air Lock", 2),
    ("Frigate Orpheon", "Deck Alpha Mech Shaft", 0),
    ("Frigate Orpheon", "Deck Alpha Mech Shaft", 1),
    ("Frigate Orpheon", "Connection Elevator to Deck Alpha", 0),
    ("Frigate Orpheon", "Connection Elevator to Deck Alpha", 1),
    ("Frigate Orpheon", "Biotech Research Area 2", 0),
    ("Frigate Orpheon", "Deck Gamma Monitor Hall", 0),
    ("Frigate Orpheon", "Connection Elevator to Deck Beta", 1),
    ("Frigate Orpheon", "Biotech Research Area 1", 2),
    ("Frigate Orpheon", "Biotech Research Area 1", 3),
    ("Frigate Orpheon", "Cargo Freight Lift to Deck Gamma", 1),
    ("Frigate Orpheon", "Cargo Freight Lift to Deck Gamma", 2),
    ("Frigate Orpheon", "Cargo Freight Lift to Deck Gamma", 3),
    ("Frigate Orpheon", "Subventilation Shaft Section A", 0),
    ("Frigate Orpheon", "Subventilation Shaft Section B", 0),
    ("Frigate Orpheon", "Subventilation Shaft Section B", 1),
    ("Frigate Orpheon", "Main Ventilation Shaft Section A", 0),
    ("Frigate Orpheon", "Main Ventilation Shaft Section B", 0),
    ("Frigate Orpheon", "Main Ventilation Shaft Section C", 1),
    ("Frigate Orpheon", "Main Ventilation Shaft Section D", 0),
    ("Frigate Orpheon", "Main Ventilation Shaft Section E", 1),
    ("Frigate Orpheon", "Main Ventilation Shaft Section F", 1),
    ("Frigate Orpheon", "Reactor Core", 0),
    ("Frigate Orpheon", "Reactor Core Entrance", 0),
    ("Frigate Orpheon", "Reactor Core Entrance", 1),
    ("Chozo Ruins", "Main Plaza", 4),
    ("Chozo Ruins", "Main Plaza", 5),
    ("Chozo Ruins", "Piston Tunnel", 0),
    ("Chozo Ruins", "Piston Tunnel", 1),
    ("Chozo Ruins", "Training Chamber", 1),
    ("Chozo Ruins", "Energy Core", 0),
    ("Chozo Ruins", "Burn Dome Access", 1),
    ("Chozo Ruins", "Furnace", 2),
    ("Chozo Ruins", "Crossway Access West", 1),
    ("Phendrana Drifts", "Quarantine Cave", 2),
    ("Phendrana Drifts", "Quarantine Monitor", 0),
    ("Phendrana Drifts", "West Tower", 0),
    ("Phendrana Drifts", "West Tower", 1),
    ("Phendrana Drifts", "Phendrana's Edge", 3),
    ("Phendrana Drifts", "Security Cave", 0),
    ("Tallon Overworld", "Reactor Core", 0),
    ("Tallon Overworld", "Reactor Access", 0),
    ("Tallon Overworld", "Reactor Access", 1),
    ("Tallon Overworld", "Cargo Freight Lift to Deck Gamma", 0),
    ("Tallon Overworld", "Life Grove Tunnel", 1),
    ("Tallon Overworld", "Life Grove", 0),
    ("Magmoor Caverns", "Warrior Shrine", 1),
    ("Magmoor Caverns", "Fiery Shores", 2),
    ("Impact Crater", "Phazon Infusion Chamber", 0),
    ("Impact Crater", "Subchamber One", 0),
    ("Impact Crater", "Subchamber One", 1),
    ("Impact Crater", "Subchamber Two", 0),
    ("Impact Crater", "Subchamber Two", 1),
    ("Impact Crater", "Subchamber Three", 0),
    ("Impact Crater", "Subchamber Three", 1),
    ("Impact Crater", "Subchamber Four", 0),
    ("Impact Crater", "Subchamber Four", 1),
    ("Impact Crater", "Subchamber Five", 0),
    ("Impact Crater", "Subchamber Five", 1),
    ("Impact Crater", "Metroid Prime Lair", 0),
]

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
                world_data[world.name]["rooms"][area.name] = {"pickups":[]}
                
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

                if self.configuration.superheated_probability != 0:
                    world_data[world.name]["rooms"][area.name]["superheated"] = self.rng.random() <= self.configuration.superheated_probability/1000.0

                if self.configuration.submerged_probability != 0:
                    world_data[world.name]["rooms"][area.name]["submerge"] = self.rng.random() <= self.configuration.submerged_probability/1000.0

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

        if self.configuration.room_rando == RoomRandoMode.ONE_WAY:
            for world in db.world_list.worlds:
                if world.name == "End of Game":
                    continue
                
                area_dock_nums = dict()
                attached_areas = dict()
                size_indices = dict()
                unused_docks = list()

                for area in world.areas:
                    area_dock_nums[area.name] = list()
                    attached_areas[area.name] = list()
                    for node in area.nodes:
                        if not isinstance(node, DockNode):
                            continue
                        index = node.extra["dock_index"]
                        if (world.name, area.name, index) in _DOCKS_TO_SKIP:
                            continue
                        area_dock_nums[area.name].append(index)
                        attached_areas[area.name].append(node.default_connection.area_name)
                        unused_docks.append((area.name, index))
                    size_indices[area.name] = area.extra["size_index"]

                self.rng.shuffle(unused_docks)

                for area in world.areas:
                    world_data[world.name]["rooms"][area.name]["doors"] = dict()
                    for dock_num in area_dock_nums[area.name]:

                        def are_rooms_compatible(src, dest):
                            if src is None or dest is None:
                                return False

                            # both rooms must have patchable docks
                            if len(area_dock_nums[src]) == 0 or len(area_dock_nums[dest]) == 0:
                                return False

                            # destinations cannot be in the same room
                            if src == dest:
                                return False
                            
                            # rooms cannot be neighbors
                            if src in attached_areas[dest]:
                                return False

                            # The two rooms must not crash if drawn at the same time (size_index > 1.0)
                            if size_indices[src] + size_indices[dest] >= 1.0:
                                return False

                            return True

                        # First try each of the unused docks
                        dest_name = None
                        dest_dock = None
                        for (name, dock) in unused_docks:
                            if are_rooms_compatible(area.name, name):
                                dest_name = name
                                dest_dock = dock
                                break

                        # If that wasn't successful, pick random destinations until it works out
                        while dest_name is None or dest_dock is None or not are_rooms_compatible(area.name, dest_name):
                            dest_name = self.rng.choice(world.areas).name

                            if len(area_dock_nums[dest_name]) == 0:
                                dest_dock = None
                                continue
                            
                            dest_dock = self.rng.choice(area_dock_nums[dest_name])

                        # Don't use this dock as a destination again unless there are no other options
                        try:
                            unused_docks.remove((dest_name, dest_dock))
                        except ValueError:
                            # print("re-used %s:%d" % (dest_name, dest_dock))
                            pass

                        world_data[world.name]["rooms"][area.name]["doors"][str(dock_num)] = {
                            "destination": {
                                "roomName": dest_name,
                                "dockNum": dest_dock,
                            }
                        }

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
        
        if self.configuration.large_samus:
            ctwk_config["playerSize"] = 1.75

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
            maze_seeds = [self.rng.choice(VANILLA_MAZE_SEEDS)]
        else:
            maze_seeds = None

        seed = self.description.get_seed_for_player(self.players_config.player_index)

        boss_sizes = None
        if self.configuration.random_boss_sizes:
            def get_random_size(min, max):
                if self.rng.choice([True, False]):
                    return self.rng.uniform(min, 0.8)
                else:
                    return self.rng.uniform(1.2, max)

            boss_sizes = {
                "parasiteQueen": get_random_size(0.1, 3.0),
                "incineratorDrone": get_random_size(0.2, 3.5),
                "adultSheegoth": get_random_size(0.2, 1.5),
                "thardus": get_random_size(0.05, 2.5),
                "elitePirate1": get_random_size(0.05, 2.3),
                "elitePirate2": get_random_size(0.05, 1.3),
                "elitePirate3": get_random_size(0.05, 2.0),
                "phazonElite": get_random_size(0.05, 2.0),
                "omegaPirate": get_random_size(0.05, 2.0),
                "Ridley": get_random_size(0.2, 1.8),
                "exo": get_random_size(0.05, 2.0),
                "essence": get_random_size(0.5, 2.25),
            }

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
                "bossSizes": boss_sizes,
                "noDoors": self.configuration.no_doors,
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
