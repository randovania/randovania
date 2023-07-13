from random import Random

from randovania.exporter import pickup_exporter
from randovania.exporter.hints import guaranteed_item_hint
from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.game_description.assignment import PickupTarget
from randovania.games.am2r.exporter.hint_namer import AM2RHintNamer
from randovania.games.am2r.layout.hint_configuration import ArtifactHintMode, IceBeamHintMode
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.lib import json_lib


class AM2RPatchDataFactory(BasePatchDataFactory):
    _EASTER_EGG_SHINY = 1024

    def _create_pickups_dict(self, pickup_list, item_info, rng: Random):
        pickup_map_dict = {}
        for pickup in pickup_list:
            quantity = pickup.conditional_resources[0].resources[0][1]
            object_name = self.game.region_list.node_from_pickup_index(pickup.index).extra["object_name"]
            pickup_map_dict[object_name] = {
                "sprite_details": {
                    "name": item_info[pickup.model.name]["sprite_name"],
                    "speed": item_info[pickup.model.name]["sprite_speed"]
                },
                "item_effect": pickup.original_pickup.name,
                "quantity": quantity,
                "text": {
                    "header": item_info[pickup.model.name]["text_header"],
                    "description": item_info[pickup.name]["text_desc"]
                }
            }
            if (pickup_map_dict[object_name]["item_effect"] == "Missile Expansion" and
                    pickup_map_dict[object_name]["sprite_details"]["name"] == "sItemMissile" and
                    pickup_map_dict[object_name]["text"]["header"] == "Got Missile Tank" and not pickup.other_player and
                    rng.randint(0, self._EASTER_EGG_SHINY) == 0):
                pickup_map_dict[object_name]["sprite_details"]["name"] = "sItemShinyMissile"
                pickup_map_dict[object_name]["text"]["header"] = "Got Shiny Missile Tank"

            # TODO: add screw shiny and hijump shiny

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
            "grave_grotto_blocks": self.patches.configuration.grave_grotto_blocks,
            "fusion_mode": self.patches.configuration.fusion_mode,
            "nest_pipes": self.patches.configuration.nest_pipes,
            "softlock_prevention_blocks": self.patches.configuration.softlock_prevention_blocks,
            "a3_entrance_blocks": self.patches.configuration.a3_entrance_blocks,
            # TODO: uncomment after rebasing/merging main "screw_blocks": self.patches.configuration.screw_blocks,
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

    def _create_hints(self):
        artifacts = [self.game.resource_database.get_item(f"Metroid DNA {i + 1}") for i in range(46)]
        ice = [(self.game.resource_database.get_item("Ice Beam"))]
        artifact_hints = {}
        hint_config = self.patches.configuration.hints
        if hint_config.artifacts != ArtifactHintMode.DISABLED:
            artifact_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                AM2RHintNamer(self.description.all_patches, self.players_config),
                hint_config.artifacts == ArtifactHintMode.HIDE_AREA,
                artifacts,
                False  # TODO: set this to true, when patcher supports setting colors!
            )
        else:
            artifact_hints = {k: f"{k.long_name} is hidden somewhere on SR-388." for k in artifacts}

        ice_hint = {}
        if hint_config.ice_beam != IceBeamHintMode.DISABLED:
            ice_hint = guaranteed_item_hint.create_guaranteed_hints_for_resources(
                self.description.all_patches,
                self.players_config,
                AM2RHintNamer(self.description.all_patches, self.players_config),
                hint_config.ice_beam == IceBeamHintMode.HIDE_AREA,
                ice,
                False  # TODO: set this to true, when patcher supports setting colors!
            )
        else:
            ice_hint = {k: "Ice Beam is located somewhere on SR-388." for k in ice}

        hints = artifact_hints | ice_hint

        return {
            key.long_name: value
            for key, value in hints.items()
        }

    def _get_item_data(self):
        item_data = json_lib.read_path(
            RandovaniaGame.AM2R.data_path.joinpath("pickup_database", "item_data.json")
        )

        for i in range(1, 47):
            item_data[f"Metroid DNA {i}"] = item_data["Metroid DNA"]

        # TODO: use correct speed for launchers, they are not 0.2

        item_data["Missiles"] = item_data["Missile Expansion"]
        item_data["Super Missiles"] = item_data["Super Missile Expansion"]
        item_data["Power Bombs"] = item_data["Power Bomb Expansion"]
        item_data["EnergyTransferModule"] = item_data["Nothing"]
        return item_data

    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def create_data(self) -> dict:
        db = self.game

        useless_target = PickupTarget(pickup_creator.create_nothing_pickup(db.resource_database),
                                      self.players_config.player_index)

        item_data = self._get_item_data()
        memo_data = {}
        for (key, value) in item_data.items():
            memo_data[key] = value["text_desc"]
        memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=self.patches.configuration.energy_per_tank)

        pickup_list = pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            exporter=pickup_exporter.create_pickup_exporter(memo_data, self.players_config),
            visual_etm=pickup_creator.create_visual_etm(),
        )

        return {
            "configuration_identifier": self._create_hash_dict(),
            "starting_items": self._create_starting_items_dict(),
            "starting_location": self._create_starting_location(),
            "pickups": self._create_pickups_dict(pickup_list, item_data, self.rng),
            "rooms": self._create_room_dict(),
            "game_patches": self._create_game_patches(),
            "door_locks": self._create_door_locks(),
            "hints": self._create_hints()
            # TODO: add cosmetic field and decide what to even put in there.
        }
