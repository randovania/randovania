import configparser
from pathlib import Path

locale = configparser.ConfigParser()


def get_localized_name(n: str) -> str:
    for k in ["item-name", "entity-name", "fluid-name", "equipment-name", "recipe-name", "technology-name"]:
        if n in locale[k]:
            return locale[k][n]
        if f"{n}-1" in locale[k]:
            return locale[k][f"{n}-1"]

    if n.startswith("fill-"):
        return f"Fill {locale['fluid-name'][n[5:-7]]} barrel"

    if n.endswith("-barrel"):
        return f"{locale['fluid-name'][n[:-7]]} barrel"

    hardcoded_names = {
        "solid-fuel-from-heavy-oil": "Solid Fuel (Heavy Oil)",
        "solid-fuel-from-light-oil": "Solid Fuel (Light Oil)",
        "solid-fuel-from-petroleum-gas": "Solid Fuel (Petroleum Gas)",
    }

    try:
        return hardcoded_names[n]
    except KeyError:
        i = n.rfind("-")
        if i != -1:
            front, number = n[:i], n[i + 1 :]
            if number.isdigit():
                return f"{get_localized_name(front)} {number}"
        raise


def read_locales(factorio_path: Path) -> None:
    locale.read(
        [
            factorio_path.joinpath("data/base/locale/en/base.cfg"),
            factorio_path.joinpath("mods/randovania-layout/locale/en/strings.cfg"),
        ]
    )
