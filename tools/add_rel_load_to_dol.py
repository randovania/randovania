import argparse
import shutil
from pathlib import Path

from randovania.dol_patching.assembler import ppc
from randovania.dol_patching.dol_file import DolFile


def align_to_32(value: int) -> int:
    return (value + 31) & ~31


def patch_dol(input_path: Path, bin_path: Path, out_path: Path):
    bin_map = bin_path.with_suffix(bin_path.suffix + ".map").read_text("utf-8")

    bin_symbols = {}
    for line in bin_map.splitlines():
        symbol_line = line.strip().split(" ", 1)
        if len(symbol_line) == 2:
            bin_symbols[symbol_line[1]] = int(symbol_line[0], 16)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, out_path)

    bin_patch = bin_path.read_bytes()
    aligned_size = align_to_32(len(bin_patch))
    bin_patch += b"\x00" * (aligned_size - len(bin_patch))

    dol = DolFile(out_path)
    dol.symbols["PPCSetFpIEEEMode"] = 0x8035712c
    dol.set_editable(True)

    with dol:
        dol.add_text_section(0x80002000, bin_patch)
        dol.write_instructions(dol.resolve_symbol("PPCSetFpIEEEMode") + 4, [
            ppc.b(bin_symbols["rel_loader_hook"])
        ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dol_file", type=Path)
    parser.add_argument("bin_path", type=Path)
    parser.add_argument("out_path", type=Path)
    args = parser.parse_args()
    patch_dol(args.dol_file, args.bin_path, args.out_path)


if __name__ == '__main__':
    main()
