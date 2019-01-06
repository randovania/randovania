from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Dict, BinaryIO

from randovania.game_description.world import World

GameVersion = str


# TODO: these maybe also include the target register
_instructions = {
    "lis": 0x3c80,
    "addi": 0x3884,
}


@dataclass
class FullLoadInstruction:
    high_bits_load: int
    low_bits_load: int

    def check_has_instructions(self, dol: BinaryIO, game_version: GameVersion):
        _check_instruction_at(dol, self.high_bits_load, "lis", game_version)
        _check_instruction_at(dol, self.low_bits_load, "addi", game_version)

    def write_value(self, dol: BinaryIO, value: int):
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("Invalid value: {}. Must be a unsigned 32-bit value".format(value))

        high_value = value >> 16
        low_value = value & 0xFFFF

        if low_value >> 15:
            # When low_value is considered negative, adding it will subtract the overflow bit
            # Add one to high_value to fix it
            high_value += 1

        dol.seek(self.high_bits_load + 2)
        dol.write(high_value.to_bytes(2, "big"))
        dol.seek(self.low_bits_load + 2)
        dol.write(low_value.to_bytes(2, "big"))


_initial_load_offsets: Dict[GameVersion, Tuple[FullLoadInstruction, ...]] = {
    "v1.028": (FullLoadInstruction(0x00140378, 0x00140380), FullLoadInstruction(0x00140388, 0x00140380))
}


def _check_instruction_at(dol: BinaryIO, offset: int, instruction: str, game_version: GameVersion):
    dol.seek(offset)
    value = dol.read(2)
    if value != _instructions[instruction].to_bytes(2, "big"):
        raise RuntimeError(
            "Expected an `{instruction}` ({instruction_value}:x) instruction at {offset:x}"
            ", but found {value:x} instead. Is this really a {version} version ISO?".format(
                instruction=instruction,
                instruction_value=_instructions[instruction],
                offset=offset,
                value=value,
                version=game_version,
            ))


def change_starting_world(game_root: Path, new_starting_world: World):
    dol_path = game_root.joinpath("sys", "main.dol")

    version = "v1.028"
    offsets = _initial_load_offsets[version]

    with dol_path.open("r+b") as dol:
        for offset in offsets:
            offset.check_has_instructions(dol, version)

        for offset in offsets:
            offset.write_value(dol, new_starting_world.world_asset_id)
