import collections
import json
import logging
import pprint
import shutil
import time
from pathlib import Path
from typing import NamedTuple, Iterator

import open_prime_rando.echoes.custom_assets
from retro_data_structures.asset_manager import AssetManager, IsoFileProvider
from retro_data_structures.conversion import conversions
from retro_data_structures.conversion.asset_converter import AssetConverter, ConvertedAsset
from retro_data_structures.dependencies import all_converted_dependencies, Dependency
from retro_data_structures.exceptions import InvalidAssetId, UnknownAssetId
from retro_data_structures.formats import PAK, format_for
from retro_data_structures.game_check import Game

from randovania import get_data_path
from randovania.game_description import default_database
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.lib import status_update_lib, json_lib
from randovania.lib.status_update_lib import ProgressUpdateCallable

PRIME_MODELS_VERSION = 1
ECHOES_MODELS_VERSION = 3


def delete_converted_assets(assets_dir: Path):
    shutil.rmtree(assets_dir, ignore_errors=True)


def get_asset_cache_version(assets_dir: Path) -> int:
    try:
        metadata = json_lib.read_path(assets_dir.joinpath("meta.json"))
        return int(metadata["version"])
    except FileNotFoundError:
        return 0


def prime_asset_manager(input_iso: Path) -> AssetManager:
    return AssetManager(IsoFileProvider(input_iso), Game.PRIME)


def echoes_asset_manager(input_path: Path) -> AssetManager:
    return AssetManager(IsoFileProvider(input_path), Game.ECHOES)


class Asset(NamedTuple):
    ancs: int
    cmdl: int
    character: int = 0
    scale: float = 1.0


prime1_assets = {
    "Charge Beam": Asset(0xE3CBC3F3, 0xC5472401),
    "Power Beam": Asset(0x00000000, 0x00000000),
    "Wave Beam": Asset(0x09881302, 0x009771B9, scale=0.75),
    "Ice Beam": Asset(0x52A3B1A4, 0xDA25B1BE, scale=0.75),
    "Plasma Beam": Asset(0x6397CC1B, 0xA792116A, scale=0.75),
    # "Missile": Asset(0xA9B8E446, 0x2D7E6590),
    "Grapple Beam": Asset(0xC5B5ED4D, 0xF86621C9, scale=0.75),
    "Combat Visor": Asset(0x00000000, 0x00000000),
    "Scan Visor": Asset(0x00000000, 0x00000000),
    "Thermal Visor": Asset(0x9F0C908A, 0x61DAB956, scale=1.5),
    "X-Ray Visor": Asset(0x9F0C908A, 0x61DAB956, scale=1.5),
    "Space Jump Boots": Asset(0x999E81FE, 0xA10715DA),
    "Energy Tank": Asset(0xF37BCBC7, 0x86908399, scale=1.5),
    "Morph Ball": Asset(0x2D0FD5C9, 0x903E8AC5, character=0, scale=1.6),
    "Morph Ball Bomb": Asset(0xDA110E43, 0xB5544D27),
    "Boost Ball": Asset(0x2D0FD5C9, 0x903E8AC5),
    "Spider Ball": Asset(0x2D0FD5C9, 0x79D95DEC, character=2),
    "Power Bomb": Asset(0xF19131AD, 0xD532BDB8, scale=4.668),
    "Power Bomb Expansion": Asset(0x0B5BBF9E, 0x227D7166),
    "Power Suit": Asset(0x00000000, 0x00000000),
    "Varia Suit": Asset(0xA3E787B7, 0xCD995C16, scale=1.5),
    "Gravity Suit": Asset(0x27A97006, 0x95946E41, scale=1.5),
    "Phazon Suit": Asset(0x00000000, 0x00000000),
    "Super Missile": Asset(0x7C04E388, 0x853A56F0, character=0, scale=2.0),
    "Wavebuster": Asset(0x7C04E388, 0x74A39FE6, character=2, scale=2.0),
    "Ice Spreader": Asset(0x7C04E388, 0x85BA7ACB, character=3, scale=2.0),
    "Flamethrower": Asset(0x7C04E388, 0xC54BBF68, character=1, scale=2.0),
    "Artifact of Truth": Asset(0xFAA9C708, 0x884E88DC, character=3, scale=0.8),
    "Artifact of Strength": Asset(0xFAA9C708, 0xFFD05A2C, character=1, scale=0.479),
    "Artifact of Elder": Asset(0xFAA9C708, 0x64751643, character=5, scale=0.86),
    "Artifact of Wild": Asset(0xFAA9C708, 0x10EDFFCC, character=6, scale=0.8),
    "Artifact of Lifegiver": Asset(0xFAA9C708, 0x8B48B3A3, character=7, scale=0.819),
    "Artifact of Warrior": Asset(0xFAA9C708, 0xFCD66153, character=8),
    "Artifact of Chozo": Asset(0xFAA9C708, 0x67732D3C, character=9, scale=0.819),
    "Artifact of Nature": Asset(0xFAA9C708, 0x15E7B24D, character=10, scale=0.809),
    "Artifact of Sun": Asset(0xFAA9C708, 0x8E42FE22, character=11, scale=0.769),
    "Artifact of World": Asset(0xFAA9C708, 0x12174A4C, character=0, scale=0.699),
    "Artifact of Spirit": Asset(0xFAA9C708, 0x89B20623, character=2, scale=0.85),
    "Artifact of Newborn": Asset(0xFAA9C708, 0xFE2CD4D3, character=4, scale=0.6),
}


def convert_prime1_pickups(prime1_iso: Path, echoes_files_path: Path, assets_path: Path,
                           patch_data: dict, randomizer_data: dict, status_update: ProgressUpdateCallable):
    """"""
    updaters = status_update_lib.split_progress_update(status_update, 3)

    # Restoring from cache causes game crashes when loading a room with a Prime model. Skipping until resolved
    if get_asset_cache_version(assets_path) >= ECHOES_MODELS_VERSION and False:
        converted_assets, randomizer_data_additions = _read_prime1_from_cache(assets_path, updaters)

    else:
        converted_assets, randomizer_data_additions = _convert_prime1_assets(
            prime1_iso, assets_path,
            randomizer_data, updaters[0],
        )

    for asset in randomizer_data_additions:
        asset["Index"] = len(randomizer_data["ModelData"])
        randomizer_data["ModelData"].append(asset)

    model_name_to_data = {
        asset["Name"]: asset
        for asset in randomizer_data_additions
    }

    wl = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES).world_list
    pickup_index_to_mrea_asset_id = {
        location["Index"]: wl.nodes_to_area(wl.node_from_pickup_index(PickupIndex(location["Index"]))).extra["asset_id"]
        for location in randomizer_data["LocationData"]
    }

    # Prepare new resources for writing
    pak_resources = {}
    num_assets = len(converted_assets) + 1

    for i, new_asset in enumerate(converted_assets.values()):
        if new_asset.type.upper() == "EVNT":
            continue

        updaters[1](f"Encoding new asset {new_asset.type} 0x{new_asset.id:08X}", i / num_assets)
        pak_resources[new_asset.id] = {
            "compressed": 0,
            "asset": {
                "type": new_asset.type,
                "id": new_asset.id,
            },
            "contents": {
                "value": format_for(new_asset.type).build(new_asset.resource, target_game=Game.ECHOES),
            },
        }

    # Figure out where models are used for duplication
    extra_assets_for_mrea = collections.defaultdict(list)

    for pickup in patch_data["pickups"]:
        model = pickup["model"]
        if model["game"] == RandovaniaGame.METROID_PRIME.value:
            model_name = "{}_{}".format(model["game"], model["name"])
            if model_name not in model_name_to_data:
                continue

            asset_id = pickup_index_to_mrea_asset_id[pickup["pickup_index"]]
            dependency_list = extra_assets_for_mrea[asset_id]
            for dependency in model_name_to_data[model_name]["Assets"]:
                dependency_resource = pak_resources[dependency["AssetID"]]
                if dependency_resource not in dependency_list:
                    dependency_list.append(dependency_resource)

    # Write to paks now
    updaters[2](f"Writing modified PAks", 0)
    for pak_i in range(1, 6):
        pak_path = echoes_files_path.joinpath("files", f"Metroid{pak_i}.pak")

        new_pak = PAK.parse(
            pak_path.read_bytes(),
            target_game=Game.ECHOES,
        )

        additions = []
        for i, resource in enumerate(new_pak.resources):
            new_deps = extra_assets_for_mrea.get(resource["asset"]["id"])
            if new_deps is not None:
                additions.append((i - 1, new_deps))

        for i, new_deps in reversed(additions):
            new_pak.resources[i:i] = new_deps

        # And add all resources at the end of every pak anyway
        for resource in pak_resources.values():
            new_pak.resources.append(resource)

        PAK.build_file(new_pak, pak_path, target_game=Game.ECHOES)
        updaters[2](f"Wrote new {pak_path.name}", pak_i / 6)


def merge_dependencies(dependencies: dict[int, set[Dependency]], asset_ids: Iterator[int]) -> Iterator[Dependency]:
    seen = set()

    def _recurse(asset_id: int):
        for dep in dependencies[asset_id]:
            # TODO: don't generate broken deps plz
            if dep.id == 0:
                continue

            if dep not in seen:
                seen.add(dep)
                yield from _recurse(dep.id)
                yield dep

    for it in asset_ids:
        yield from _recurse(it)


def _convert_prime1_assets(input_iso: Path, output_path: Path, randomizer_data: dict,
                           status_update: ProgressUpdateCallable):
    asset_manager = prime_asset_manager(input_iso)

    next_id = 0xFFFF0000

    def id_generator(_):
        nonlocal next_id
        new_id = next_id
        next_id = new_id + 1
        return new_id

    start = time.time()
    conversion_updaters = status_update_lib.split_progress_update(status_update, 2)
    conversion_updaters[0]("Loading Prime 1 PAKs", 0)
    converter = AssetConverter(
        target_game=Game.ECHOES,
        asset_providers={Game.PRIME: asset_manager},
        id_generator=id_generator,
        converters=conversions.converter_for,
    )
    conversion_updaters[0]("Finished loading Prime 1 PAKs", 1)
    # logging.debug(f"Finished loading PAKs: {time.time() - start}")

    result = {}
    num_assets = len(prime1_assets)
    for i, (name, asset) in enumerate(prime1_assets.items()):
        conversion_updaters[1](f"Converting {name} from Prime 1", i / num_assets)
        if asset.ancs != 0 and asset.cmdl != 0:
            result[name] = Asset(
                ancs=converter.convert_id(asset.ancs, Game.PRIME),
                cmdl=converter.convert_id(asset.cmdl, Game.PRIME),
                character=asset.character,
                scale=asset.scale,
            )
    conversion_updaters[1]("Finished converting Prime 1 assets", 1)
    output_path.mkdir(exist_ok=True, parents=True)
    # Cache these assets here
    # This doesn't work properly so skip this for now
    '''
    for asset in converter.converted_assets.values():
        assetdata = format_for(asset.type).build(asset.resource, target_game=Game.ECHOES)
        if len(assetdata) % 32 != 0:
            assetdata += b"\xFF" * (32 - (len(assetdata) % 32))
        assets_path.joinpath(f"{asset.id}.{asset.type.upper()}").write_bytes(
            assetdata
        )
    '''
    end = time.time()

    # logging.debug(f"Time took: {end - start}")
    converted_assets = converter.converted_assets
    converted_dependencies = all_converted_dependencies(converter)
    # logging.debug("Updating RandomizerData.json")
    start = time.time()
    meta_dict = {"version": PRIME_MODELS_VERSION}

    randomizer_data_additions = []
    for name, asset in result.items():
        dependencies = [
            {"AssetID": dep.id, "Type": dep.type.upper()}
            for dep in merge_dependencies(converted_dependencies, [asset.ancs, asset.cmdl])
        ]
        pprint.pprint(dependencies)
        randomizer_data_additions.append({
            "Index": len(randomizer_data["ModelData"]),  # Adjust this one later
            "Name": f"prime1_{name}",
            "Model": asset.cmdl,
            "ScanModel": 0xFFFFFFFF,
            "AnimSet": asset.ancs,
            "Character": asset.character,
            "DefaultAnim": 0,
            "Rotation": [0.0, 0.0, 0.0],
            "Scale": [asset.scale, asset.scale, asset.scale],
            "OrbitOffset": [0.0, 0.0, 0.0],
            "Lighting": {
                "CastShadow": True,
                "UnknownBool1": True,
                "UseWorldLighting": 1,
                "UnknownBool2": False
            },
            "Assets": dependencies
        })
    meta_dict["data"] = randomizer_data_additions
    with open(output_path.joinpath("meta.json"), "w") as data_additions_file:
        json.dump(meta_dict, data_additions_file, indent=4)

    end = time.time()
    # logging.debug(f"Time took: {end - start}")
    return converted_assets, randomizer_data_additions


def _read_prime1_from_cache(assets_path: Path, updaters):
    randomizer_data_additions = json_lib.read_path(assets_path.joinpath("meta.json"))["data"]
    converted_assets = {}
    # Read assets from cache if available
    for i, item in enumerate(randomizer_data_additions):
        item_name = item["Name"].replace('prime1_', '')
        updaters[0](f"Restoring Prime 1 {item_name}", i / len(randomizer_data_additions))
        for asset in item["Assets"]:
            asset_type = asset["Type"]
            asset_id = asset["AssetID"]
            asset_path = assets_path.joinpath(f"{asset_id}.{asset_type}")
            construct_class = format_for(asset_type)

            raw = asset_path.read_bytes()
            decoded_from_raw = construct_class.parse(raw, target_game=Game.ECHOES)
            converted_asset = ConvertedAsset(
                id=asset_id,
                type=asset_type,
                resource=decoded_from_raw,
            )
            converted_assets[asset_id] = converted_asset
    return converted_assets, randomizer_data_additions


def convert_prime2_pickups(input_path: Path, output_path: Path, status_update: ProgressUpdateCallable):
    metafile = output_path.joinpath("meta.json")
    if get_asset_cache_version(output_path) >= ECHOES_MODELS_VERSION:
        with open(metafile) as md:
            return json.load(md)

    delete_converted_assets(output_path)

    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")
    with randomizer_data_path.open() as randomizer_data_file:
        randomizer_data = json.load(randomizer_data_file)

    next_id = 0xFFFF0000

    def id_generator(_):
        nonlocal next_id
        new_id = next_id
        next_id = new_id + 1
        return new_id

    start = time.time()

    asset_manager = echoes_asset_manager(input_path)
    open_prime_rando.echoes.custom_assets.create_custom_assets(asset_manager)

    logging.info("Loading PAKs")
    status_update("Loading assets from Prime 2 to convert", 0.0)
    converter = AssetConverter(
        target_game=Game.PRIME,
        asset_providers={Game.ECHOES: asset_manager},
        id_generator=id_generator,
        converters=conversions.converter_for,
    )
    logging.info(f"Finished loading PAKs: {time.time() - start}")

    # Fix the Varia Suit's character in the suits ANCS referencing a missing skin.
    # 0x3A5E2FE1 is Light Suit's skin
    # this is fixed by Claris' patcher when exporting for Echoes
    suits_ancs = asset_manager.get_parsed_asset(0xa3e787b7)
    suits_ancs.raw.character_set.characters[0].skin_id = 0x3A5E2FE1
    asset_manager.replace_asset(0xa3e787b7, suits_ancs)

    # Use echoes missile expansion for unlimited missiles instead of missile launcher
    unlimited_missile_data = next(i for i in randomizer_data["ModelData"] if i["Index"] == 42)
    unlimited_missile_data["Model"] = 1581025172
    unlimited_missile_data["AnimSet"] = 435828657

    result = {}
    assets_to_change = [
        data
        for data in randomizer_data["ModelData"]
        if (data["Model"] != Game.ECHOES.invalid_asset_id
            and data["AnimSet"] != Game.ECHOES.invalid_asset_id)
    ]

    for i, data in enumerate(assets_to_change):
        try:
            status_update(f"Converting {data['Name']} from Prime 2", i / len(assets_to_change))
            result["{}_{}".format(RandovaniaGame.METROID_PRIME_ECHOES.value, data["Name"])] = Asset(
                ancs=converter.convert_id(data["AnimSet"], Game.ECHOES, missing_assets_as_invalid=False),
                cmdl=converter.convert_id(data["Model"], Game.ECHOES, missing_assets_as_invalid=False),
                character=data["Character"],
                scale=data["Scale"][0],
            )
        except (InvalidAssetId, UnknownAssetId) as e:
            raise RuntimeError("Unable to convert {}: {}".format(data["Name"], e))

    end = time.time()
    logging.info(f"Time took to convert assets: {end - start}")
    status_update(f"Finished converting assets from Prime 2 in {end - start:.3f}.", 1.0)

    start = time.time()
    converted_dependencies = all_converted_dependencies(converter)

    new_id_to_old = {
        new_id: old_id
        for (_, old_id), new_id in converter.converted_ids.items()
    }

    unique_anim = {}
    unique_evnt = []
    dont_delete = []
    for anim in converter.converted_assets.values():
        if anim.type != "ANIM":
            continue

        for ancs in converter.converted_assets.values():
            if ancs.type != "ANCS":
                continue

            # If the anim is a dependency of the ancs
            if any(anim.id in x for x in converted_dependencies[ancs.id]):
                for dep in converted_dependencies[ancs.id]:
                    if anim.id in unique_anim:
                        for depb in converted_dependencies[ancs.id]:
                            if depb.type == "EVNT":
                                if depb.id not in unique_evnt:
                                    unique_evnt.append(depb.id)
                                    converted_dependencies[ancs.id].remove(depb)
                                    converted_dependencies[ancs.id].add(Dependency("EVNT", unique_anim[anim.id]))
                                else:
                                    dont_delete.append(depb.id)
                        continue
                    if dep.type == "EVNT":
                        unique_anim[anim.id] = dep.id
                        anim.resource["anim"]["event_id"] = dep.id
                        break

    deleted_evnts = []
    for id in unique_evnt:
        if id not in dont_delete:
            deleted_evnts.append(id)
    for id in deleted_evnts:
        converter.converted_assets.pop(id)

    output_path.mkdir(exist_ok=True, parents=True)
    with output_path.joinpath("meta.json").open("w") as meta_out:
        metadata = {
            "version": ECHOES_MODELS_VERSION,
            "items": {
                name: {
                    "ancs": asset.ancs,
                    "cmdl": asset.cmdl,
                    "character": asset.character,
                    "scale": asset.scale,
                }
                for name, asset in result.items()
            },
            "new_assets": [
                {
                    "old_id": new_id_to_old.get(asset.id),
                    "new_id": asset.id,
                    "type": asset.type,
                    "dependencies": [
                        {"type": dep.type, "id": dep.id}
                        for dep in converted_dependencies[asset.id]
                    ]
                }
                for asset in converter.converted_assets.values()
            ],
        }
        json.dump(metadata, meta_out, indent=4)

    for asset in converter.converted_assets.values():
        assetdata = format_for(asset.type).build(asset.resource, target_game=Game.PRIME)
        if len(assetdata) % 32 != 0:
            assetdata += b"\xFF" * (32 - (len(assetdata) % 32))
        output_path.joinpath(f"{asset.id}.{asset.type.upper()}").write_bytes(
            assetdata
        )

    logging.info(f"Time took to write files: {time.time() - start}")
    status_update(f"Finished writing the converted assets in {end - start:.3f}.", 1.0)
    return metadata


def _debug_main():
    import randovania
    randovania.setup_logging("DEBUG", None)

    from randovania.interface_common.options import Options
    options = Options.with_default_data_dir()
    convert_prime2_pickups(options.internal_copies_path.joinpath("prime2", "contents"),
                           Path("converted"), print)


if __name__ == '__main__':
    _debug_main()
