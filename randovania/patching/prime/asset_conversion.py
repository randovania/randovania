import copy
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import NamedTuple, List

import nod
from retro_data_structures.asset_provider import AssetProvider, InvalidAssetId, UnknownAssetId
from retro_data_structures.conversion import conversions
from retro_data_structures.conversion.asset_converter import AssetConverter, ConvertedAsset
from retro_data_structures.dependencies import all_converted_dependencies, Dependency
from retro_data_structures.formats import PAK, format_for
from retro_data_structures.game_check import Game

from randovania import get_data_path
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import Options
from randovania.lib import status_update_lib
from randovania.lib.status_update_lib import ProgressUpdateCallable

PRIME_MODELS_VERSION = 1
ECHOES_MODELS_VERSION = 2


def delete_converted_assets(assets_dir: Path):
    shutil.rmtree(assets_dir, ignore_errors=True)


def get_asset_cache_version(assets_dir: Path) -> int:
    try:
        with open(assets_dir.joinpath("meta.json")) as metafile:
            metadata = json.load(metafile)
            return int(metadata["version"])
    except FileNotFoundError:
        return 0


def prime_asset_provider() -> AssetProvider:
    opt = Options.with_default_data_dir()
    opt.load_from_disk()
    prime_1_options = opt.options_for_game(RandovaniaGame.METROID_PRIME)
    if prime_1_options.input_path is None:
        raise RuntimeError("No prime1 iso!")

    result = nod.open_disc_from_image(os.fspath(prime_1_options.input_path))
    if result is None:
        raise RuntimeError(f"Invalid prime1 iso: {prime_1_options.input_path}")

    part = result[0].get_data_partition()
    pak_file_names: List[str] = [
        name
        for name in part.files()
        if name.lower().endswith(".pak")
    ]
    pak_files = [
        part.read_file(name)
        for name in pak_file_names
    ]

    return AssetProvider(Game.PRIME, pak_file_names, pak_files)


def echoes_asset_provider() -> AssetProvider:
    internal_copies_path = Options.with_default_data_dir().internal_copies_path
    paks_path = internal_copies_path.joinpath("prime2", "contents", "files")

    all_files = list(paks_path.glob("*.pak"))
    return AssetProvider(Game.ECHOES, all_files)


def create_scan_visor_assets():
    dark_visor_ancs_id = 2233160302
    scan_visor_cmdl = 2949054468

    with echoes_asset_provider() as asset_provider:
        dark_visor_ancs = asset_provider.get_asset(dark_visor_ancs_id)

        scan_visor_ancs = copy.deepcopy(dark_visor_ancs)
        scan_visor_ancs.character_set.characters[0].model_id = scan_visor_cmdl


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


def convert_prime1_pickups(echoes_files_path: Path, assets_path: Path, randomizer_data: dict,
                           status_update: ProgressUpdateCallable):
    next_id = 0xFFFF0000

    def id_generator(_):
        nonlocal next_id
        new_id = next_id
        while asset_provider.asset_id_exists(new_id):
            new_id += 1

        next_id = new_id + 1
        return new_id

    updaters = status_update_lib.split_progress_update(status_update, 2)

    # Restoring from cache causes game crashes when loading a room with a Prime model. Skipping until resolved
    if get_asset_cache_version(assets_path) >= ECHOES_MODELS_VERSION and False:
        with open(assets_path.joinpath("meta.json"), "r") as data_additions_file:
            randomizer_data_additions = json.load(data_additions_file)["data"]

        converted_assets = {}
        # Read assets from cache if available
        for i, item in enumerate(randomizer_data_additions):
            item_name = item["Name"].replace('prime1_', '')
            updaters[0](f"Restoring Prime 1 {item_name}", i / len(randomizer_data_additions))
            for asset in item["Assets"]:
                asset_type = asset["Type"]
                asset_id = asset["AssetID"]
                asset_path = assets_path.joinpath("{}.{}".format(asset_id, asset_type))
                construct_class = format_for(asset_type)

                raw = asset_path.read_bytes()
                decoded_from_raw = construct_class.parse(raw, target_game=Game.ECHOES)
                converted_asset = ConvertedAsset(
                    id=asset_id,
                    type=asset_type,
                    resource=decoded_from_raw,
                )
                converted_assets[asset_id] = converted_asset

    else:
        try:
            asset_provider = prime_asset_provider()
        except RuntimeError:
            raise

        start = time.time()
        with asset_provider:
            conversion_updaters = status_update_lib.split_progress_update(updaters[0], 2)
            conversion_updaters[0]("Loading Prime 1 PAKs", 0)
            converter = AssetConverter(
                target_game=Game.ECHOES,
                asset_providers={Game.PRIME: asset_provider},
                id_generator=id_generator,
                converters=conversions.converter_for,
            )
            conversion_updaters[0]("Finished loading Prime 1 PAKs", 1)
            # logging.debug(f"Finished loading PAKs: {time.time() - start}")

            result = {}
            num_assets = len(prime1_assets)
            for i, (name, asset) in enumerate(prime1_assets.items()):
                updaters[1](f"Converting {name} from Prime 1", i / num_assets)
                if asset.ancs != 0 and asset.cmdl != 0:
                    result[name] = Asset(
                        ancs=converter.convert_id(asset.ancs, Game.PRIME),
                        cmdl=converter.convert_id(asset.cmdl, Game.PRIME),
                        character=asset.character,
                        scale=asset.scale,
                    )
            conversion_updaters[1]("Finished converting Prime 1 assets", 1)
            assets_path.mkdir(exist_ok=True, parents=True)
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
                for dep in converted_dependencies[asset.ancs] | converted_dependencies[asset.cmdl]
            ]
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
        with open(assets_path.joinpath("meta.json"), "w") as data_additions_file:
            json.dump(meta_dict, data_additions_file, indent=4)
        end = time.time()
        # logging.debug(f"Time took: {end - start}")

    # Write to paks now

    pak_updaters = status_update_lib.split_progress_update(updaters[1], 5)
    for pak_i in range(1, 6):
        pak_status = pak_updaters[pak_i - 1]
        pak_path = echoes_files_path.joinpath("files", f"Metroid{pak_i}.pak")
        pak_status(f"Preparing to write custom assets to Echoes {pak_path.name}", 0)
        num_assets = len(converted_assets) + 1

        new_pak = PAK.parse(
            pak_path.read_bytes(),
            target_game=Game.ECHOES,
        )
        for i, new_asset in enumerate(converted_assets.values()):
            if new_asset.type.upper() == "EVNT":
                continue

            pak_status(f"Writing new asset {new_asset.type} 0x{new_asset.id:08X} to {pak_path.name}", i / num_assets)
            new_pak.resources.append({
                "compressed": 0,
                "asset": {
                    "type": new_asset.type,
                    "id": new_asset.id,
                },
                "contents": {
                    "value": format_for(new_asset.type).build(new_asset.resource, target_game=Game.ECHOES),
                },
            })

        pak_status(f"Writing new {pak_path.name}", (num_assets - 1) / num_assets)
        PAK.build_file(new_pak, pak_path, target_game=Game.ECHOES)

        for asset in randomizer_data_additions:
            asset["Index"] = len(randomizer_data["ModelData"])
            randomizer_data["ModelData"].append(asset)


def convert_prime2_pickups(output_path: Path, status_update: ProgressUpdateCallable):
    metafile = output_path.joinpath("meta.json")
    if get_asset_cache_version(output_path) >= ECHOES_MODELS_VERSION:
        with open(metafile, "r") as md:
            return json.load(md)

    next_id = 0xFFFF0000

    delete_converted_assets(output_path)

    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")
    with randomizer_data_path.open() as randomizer_data_file:
        randomizer_data = json.load(randomizer_data_file)

    def id_generator(asset_type):
        nonlocal next_id
        result = next_id
        while asset_provider.asset_id_exists(result):
            result += 1

        next_id = result + 1
        return result

    start = time.time()
    with echoes_asset_provider() as asset_provider:
        logging.info("Loading PAKs")
        converter = AssetConverter(
            target_game=Game.PRIME,
            asset_providers={Game.ECHOES: asset_provider},
            id_generator=id_generator,
            converters=conversions.converter_for,
        )
        logging.info(f"Finished loading PAKs: {time.time() - start}")

        # These aren't guaranteed to be available in the paks yet, so skip them for now
        models_to_skip = [
            "VioletTranslator",
            "AmberTranslator",
            "EmeraldTranslator",
            "CobaltTranslator",
            "DarkBeamAmmoExpansion",
            "LightBeamAmmoExpansion"
        ]

        # Fix the Varia Suit's character in the suits ANCS referencing a missing skin.
        # 0x3A5E2FE1 is Light Suit's skin
        # this is fixed by Claris' patcher when exporting for Echoes
        asset_provider.get_asset(0xa3e787b7).character_set.characters[0].skin_id = 0x3A5E2FE1

        # Use echoes missile expansion for unlimited missiles instead of missile launcher
        unlimited_missile_data = next(i for i in randomizer_data["ModelData"] if i["Index"] == 42)
        unlimited_missile_data["Model"] = 1581025172
        unlimited_missile_data["AnimSet"] = 435828657

        result = {}
        assets_to_change = [
            data
            for data in randomizer_data["ModelData"]
            if (data["Model"] != Game.ECHOES.invalid_asset_id
                and data["AnimSet"] != Game.ECHOES.invalid_asset_id
                and data["Name"] not in models_to_skip)
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
    logging.info(f"Time took: {end - start}")

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

    logging.info(f"Time took: {time.time() - start}")
    return metadata


if __name__ == '__main__':
    convert_prime2_pickups(Path("converted"), print)
