# -*- mode: python -*-

import randovania
from randovania.games.game import RandovaniaGame
block_cipher = None
icon_path = "randovania/data/icons/sky_temple_key_NqN_icon.ico"

item_databases = [(f'randovania/games/{game.value}/item_database', f'games/{game.value}/item_database') for game in RandovaniaGame]
presets = [(f'randovania/games/{game.value}/presets', f'games/{game.value}/presets') for game in RandovaniaGame]
game_assets = [(f'randovania/games/{game.value}/assets', f'games/{game.value}/assets') for game in RandovaniaGame if game.data_path.joinpath("assets").exists()]

a = Analysis(['randovania/__main__.py', 'randovania/cli/__init__.py'],
             pathex=[],
             binaries=[],
             datas=[
                 ("randovania/data/configuration.json", "data/"),
                 ("randovania/data/migration_data.json", "data/"),
                 ("randovania/data/binary_data", "data/binary_data"),
                 ("randovania/data/ClarisEchoesMenu", "data/ClarisEchoesMenu"),
                 ("randovania/data/ClarisPrimeRandomizer", "data/ClarisPrimeRandomizer"),
                 ("randovania/data/gui_assets", "data/gui_assets"),
                 ("randovania/data/hash_words", "data/hash_words"),
                 ("randovania/data/icons", "data/icons"),
                 ("randovania/data/nintendont", "data/nintendont"),
                 *item_databases,
                 *presets,
                 *game_assets,
                 ("README.md", "data/")
             ],
             hiddenimports=[
                "mock",
                "unittest.mock",
                "pkg_resources.py2_warn",
                "randovania.server.discord.preset_lookup",
                "randovania.server.discord.database_command",
                "randovania.server.discord.faq_command",
             ],
             hookspath=[
                 # https://github.com/pyinstaller/pyinstaller/issues/4040
                 "tools/additional-pyinstaller-hooks",
             ],
             runtime_hooks=[],
             excludes=["PyQt5"],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='randovania',
          debug=False,
          strip=False,
          upx=False,
          icon=icon_path,
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='randovania')
app = BUNDLE(coll,
         name='Randovania.app',
         icon="tools/sky_temple_key.icns",
         bundle_identifier="run.metroidprime.randovania",
         info_plist={
            "LSBackgroundOnly": False,
            "CFBundleShortVersionString": randovania.VERSION,
         }
         )
