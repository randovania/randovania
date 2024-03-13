from __future__ import annotations

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("randovania_lupa", include_py_files=True)

hiddenimports = [
    "randovania_lupa.lua51",
]
