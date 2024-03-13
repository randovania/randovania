# -*- mode: python -*-
import hashlib
import json
import os
import platform
import pathlib
from PyInstaller.utils.hooks import copy_metadata

import randovania
from randovania.games.game import RandovaniaGame

block_cipher = None

icon_path = "randovania/data/icons/executable_icon.ico"

pickup_databases = [
    (f"randovania/games/{game.value}/pickup_database", f"games/{game.value}/pickup_database") for game in RandovaniaGame
]
presets = [(f"randovania/games/{game.value}/presets", f"games/{game.value}/presets") for game in RandovaniaGame]
game_assets = [
    (f"randovania/games/{game.value}/assets", f"games/{game.value}/assets")
    for game in RandovaniaGame
    if game.data_path.joinpath("assets").exists()
]

datas = [
    ("randovania/data/configuration.json", "data/"),
    ("randovania/data/binary_data", "data/binary_data"),
    ("randovania/data/ClarisPrimeRandomizer", "data/ClarisPrimeRandomizer"),
    ("randovania/data/gui_assets", "data/gui_assets"),
    ("randovania/data/icons", "data/icons"),
    ("randovania/data/nintendont", "data/nintendont"),
    ("randovania/data/dotnet_runtime", "data/dotnet_runtime"),
    *pickup_databases,
    *presets,
    *game_assets,
    ("README.md", "data/"),
]
datas += copy_metadata("randovania", recursive=True)
if platform.system() == "Linux":
    linux_datas = [("randovania/data/xdg_assets", "xdg_assets")]
    datas += linux_datas


a = Analysis(
    ["randovania/__main__.py", "randovania/cli/__init__.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "unittest.mock",
    ],
    hookspath=[
        # https://github.com/pyinstaller/pyinstaller/issues/4040
        "tools/additional-pyinstaller-hooks",
    ],
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "randovania.server",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="randovania",
    debug=False,
    strip=False,
    upx=False,
    icon=icon_path,
    console=True,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name="randovania")
app = BUNDLE(
    coll,
    name="Randovania.app",
    icon="tools/rdv_logo.icns",
    bundle_identifier="run.metroidprime.randovania",
    info_plist={
        "LSBackgroundOnly": False,
        "CFBundleShortVersionString": randovania.VERSION,
    },
)
