# -*- mode: python -*-

block_cipher = None


a = Analysis(['randovania/__main__.py', 'randovania/cli/__init__.py'],
             pathex=[],
             binaries=[],
             datas=[
                 ("randovania/data", "data")
             ],
             hiddenimports=[
                 "py._builtin",
                 "py._path",
                 "py._path.common",
                 "py._path.local",
                 "py._error",
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='randovania',
          debug=False,
          strip=False,
          upx=True,
          console=True )
